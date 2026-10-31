"""Hexwise project transactions. No original is edited until explicit acceptance."""
import hashlib
import json
import os
import re
import stat
import tempfile
import threading
import time
import uuid
from pathlib import Path

MAX_FILE = 16 * 1024 * 1024


def sha(data):
    return hashlib.sha256(data).hexdigest()


def atomic(path, data, mode=0o600):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.hexwise-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
        if os.name == 'posix':
            directory = os.open(str(path.parent), os.O_RDONLY)
            try: os.fsync(directory)
            finally: os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def unhex(text):
    if not isinstance(text, str) or len(text) > MAX_FILE * 2 or not re.fullmatch(r'(?:[a-fA-F0-9]{2})*', text):
        raise ValueError('Expected complete hexadecimal byte pairs, without separators.')
    return bytes.fromhex(text)


def apply_proposal(data, proposal):
    if not isinstance(proposal, dict):
        raise ValueError('The model response must be a JSON object.')
    expected = proposal.get('base_sha256')
    if expected != sha(data):
        raise ValueError('The proposal does not match the current candidate hash.')
    if proposal.get('artifact') is not None and proposal.get('edits') is not None:
        raise ValueError('A proposal cannot contain both edits and an artifact.')
    if proposal.get('artifact') is not None:
        if not isinstance(proposal['artifact'], dict):
            raise ValueError('Invalid artifact object.')
        return unhex(proposal['artifact']['hex'])
    edits = proposal.get('edits')
    if not isinstance(edits, list) or not edits:
        raise ValueError('No byte edits or replacement artifact in response.')
    output = bytearray(data)
    end = 0
    for edit in edits:
        if not isinstance(edit, dict):
            raise ValueError('Every patch edit must be an object.')
        offset = edit.get('offset')
        if type(offset) is not int or offset < end:
            raise ValueError('Patch ranges must be sorted and non-overlapping.')
        before, after = unhex(edit['before']), unhex(edit['after'])
        if not before or len(before) != len(after) or offset + len(before) > len(data):
            raise ValueError('Patches must replace nonempty, equal-length ranges within the file.')
        if data[offset:offset + len(before)] != before:
            raise ValueError('Original bytes do not match the proposal.')
        output[offset:offset + len(before)] = after
        end = offset + len(before)
    return bytes(output)


def detect(data, filename=''):
    name = filename.lower()
    if data[:4] == b'\x7fELF' and len(data) >= 20:
        if data[4] not in (1,2) or data[5] not in (1,2):return ''
        order = 'little' if data[5] == 1 else 'big'
        machine = int.from_bytes(data[18:20], order)
        if machine in (62,183,243,21,22) and data[4]!=2:return ''
        if machine in (3,40) and data[4]!=1:return ''
        if machine==21 and data[5]!=1:return ''
        return {3:'linux-i386',62:'linux-x86_64',183:'linux-aarch64',40:'linux-armv7hf',
                243:'linux-riscv64',21:'linux-ppc64le',22:'linux-s390x'}.get(machine, '')
    if data[:4] == b'\xcf\xfa\xed\xfe' and len(data) >= 8:
        return {0x100000c:'macos-arm64',0x1000007:'macos-x86_64'}.get(int.from_bytes(data[4:8],'little'),'')
    if data[:2] == b'MZ' and len(data) >= 64:
        offset = int.from_bytes(data[60:64], 'little')
        if data[offset:offset+4] == b'PE\0\0':
            return {0x8664:'windows-x64',0x14c:'windows-x86',0xaa64:'windows-arm64',
                    0xa641:'windows-arm64ec'}.get(int.from_bytes(data[offset+4:offset+6],'little'),'')
    if data[:4] == b'\0asm':
        return 'wasm32-browser'
    if name.endswith(('.html','.htm','.css','.js','.json','.txt','.md','.py','.svg')):
        return 'web-document'
    return ''


class Projects:
    def __init__(self, directory):
        self.root = Path(directory).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

    def folder(self, project):
        if not re.fullmatch(r'[a-f0-9]{32}', project):
            raise ValueError('Invalid project ID.')
        return self.root / project

    def load(self, project):
        return json.loads((self.folder(project) / 'project.json').read_text())

    def save(self, project):
        with self.lock:
            atomic(self.folder(project['id']) / 'project.json', json.dumps(project, indent=2).encode())

    def update(self, project_id, **fields):
        with self.lock:
            project = self.load(project_id)
            project.update(fields)
            self.save(project)
            return project

    def open(self, filename):
        # File reads may wait on OS permission or cloud hydration. Do not hold the
        # project registry lock while waiting on an unrelated external file.
        original = Path(filename).absolute()
        if original.is_symlink() or not original.is_file():
            raise ValueError('Choose a regular file, not a symbolic link.')
        info=original.stat()
        if info.st_size > MAX_FILE:
            raise ValueError('This release supports files up to 16 MiB.')
        with original.open('rb') as stream:data=stream.read(MAX_FILE+1)
        if len(data)>MAX_FILE:raise ValueError('The file grew beyond the 16 MiB limit while opening.')
        with self.lock:
            project = dict(id=uuid.uuid4().hex, original=str(original.resolve()), name=original.name,
                           base_sha256=sha(data), mode=stat.S_IMODE(info.st_mode),
                           created=time.time(), profile=detect(data, original.name), snapshots=[],
                           messages=[], current=None, accepted=None)
            self.save(project)
            return self.snapshot(project['id'], data, 'Original · protected copy', 'original')

    def snapshot(self, project_id, data, label, origin='manual', expected=None):
        with self.lock:
            if len(data) > MAX_FILE:
                raise ValueError('Candidate exceeds the 16 MiB limit.')
            project = self.load(project_id)
            if expected is not None and project['current'] != expected:
                raise ValueError('The candidate changed. Reload before applying this edit.')
            snapshot = dict(id=uuid.uuid4().hex, sha256=sha(data), bytes=len(data), label=label[:160],
                            origin=origin, created=time.time(), parent=project['current'])
            atomic(self.folder(project_id) / 'snapshots' / (snapshot['id'] + '.bin'), data)
            project['snapshots'].append(snapshot)
            project['current'] = snapshot['id']
            self.save(project)
            return project

    def data(self, project_id, snapshot=None):
        project = self.load(project_id)
        identity = snapshot or project['current']
        if not any(s['id'] == identity for s in project['snapshots']):
            raise ValueError('Snapshot does not belong to this project.')
        data = (self.folder(project_id) / 'snapshots' / (identity + '.bin')).read_bytes()
        record = next(s for s in project['snapshots'] if s['id'] == identity)
        if sha(data) != record['sha256'] or len(data) != record['bytes']:
            raise ValueError('Snapshot integrity check failed. The saved bytes changed outside Hexwise.')
        return data

    def accept(self, project_id, expected):
        with self.lock:
            project = self.load(project_id)
            if expected != project['current']:
                raise ValueError('The candidate changed before acceptance.')
            original = Path(project['original'])
            if original.is_symlink() or not original.is_file():
                raise ValueError('The original file was moved or replaced.')
            old = original.read_bytes()
            if sha(old) != project['base_sha256']:
                raise ValueError('The original changed outside Hexwise. Reopen it; no overwrite was performed.')
            backup = self.folder(project_id) / 'backups' / (time.strftime('%Y%m%d-%H%M%S') + '-' + uuid.uuid4().hex[:8] + '.bin')
            atomic(backup, old)
            candidate = self.data(project_id)
            # Recheck immediately before replacement. External writers must still be quiescent.
            if sha(original.read_bytes()) != sha(old):
                raise ValueError('The original changed during acceptance. The backup is retained.')
            atomic(original, candidate, project['mode'])
            project['base_sha256'] = sha(candidate)
            project['accepted'] = dict(snapshot=expected, backup=str(backup), time=time.time())
            self.save(project)
            return project

    def message(self, project_id, role, text, **metadata):
        with self.lock:
            project = self.load(project_id)
            identity=uuid.uuid4().hex
            project['messages'].append(dict(id=identity,role=role,text=text,time=time.time(),**metadata))
            self.save(project)
            return identity

    def update_message(self,project_id,identity,**metadata):
        with self.lock:
            project=self.load(project_id)
            message=next(m for m in project['messages'] if m.get('id')==identity)
            message.update(metadata)
            self.save(project)

    def recent(self):
        result = []
        for path in self.root.glob('*/project.json'):
            try:
                p = json.loads(path.read_text())
                result.append({k:p[k] for k in ['id','name','original','created','profile']})
            except (OSError, ValueError, KeyError):
                continue
        return sorted(result, key=lambda p:p['created'], reverse=True)[:50]
