"""Explicit, network-disabled Docker runner for Linux candidates. Never execute on the host."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading
import uuid
from validation import check_candidate


def run_candidate(data, profile, image, arguments, directory, expected_stdout=None):
    if profile not in ('linux-x86_64','linux-aarch64'):
        raise ValueError('The container runner supports Linux x86-64 and ARM64 only. Other targets need a matching VM/device runner.')
    if not data.startswith(b'\x7fELF'):
        raise ValueError('This runner requires a complete Linux ELF executable, not a raw function or source document.')
    check=check_candidate(data)
    required_machine=62 if profile=='linux-x86_64' else 183
    if check['errors'] or check['details'].get('bits')!=64 or check['details'].get('machine')!=required_machine or not check['details'].get('program_headers'):
        raise ValueError('Candidate must have a structurally bounded 64-bit ELF header and program headers matching the selected architecture.')
    if not shutil.which('docker'):
        raise ValueError('Docker CLI is not installed. Use an isolated target environment for native execution.')
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_./:@-]{0,200}',image):
        raise ValueError('Specify an existing Docker image, preferably pinned by digest.')
    if not isinstance(arguments,list) or len(arguments)>32 or any(not isinstance(a,str) or len(a)>1000 for a in arguments):
        raise ValueError('Arguments must be a JSON list of at most 32 strings.')
    directory=Path(directory)/uuid.uuid4().hex
    directory.mkdir(parents=True,mode=0o755)
    candidate=directory/'candidate'
    candidate.write_bytes(data);candidate.chmod(0o755)
    name='hexwise-'+uuid.uuid4().hex
    platform='linux/amd64' if profile=='linux-x86_64' else 'linux/arm64'
    command=['docker','run','--name',name,'--rm','--pull','never','--platform',platform,
             '--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges',
             '--memory','128m','--cpus','1','--pids-limit','32','--user','65534:65534',
             '--ulimit','nofile=64:64','--log-driver','none',
             '--mount',f'type=bind,source={directory.resolve()},target=/artifact,readonly',
             '--entrypoint','/artifact/candidate',image]+arguments
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output=bytearray();total=[0]
    def drain():
        while True:
            block=process.stdout.read(4096)
            if not block:break
            total[0]+=len(block)
            if len(output)<65536:output.extend(block[:65536-len(output)])
    reader=threading.Thread(target=drain,daemon=True);reader.start()
    timed_out=False
    try:process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        timed_out=True;process.kill();process.wait()
    finally:
        # Only the unique container created by this invocation is eligible for cleanup.
        subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=10)
    reader.join(timeout=3)
    text=output.decode('utf-8',errors='replace')
    result=dict(runner='docker-restricted-linux/0.1',profile=profile,image=image,exit_code=process.returncode,
                timed_out=timed_out,output=text,output_truncated=total[0]>65536,
                expected_stdout_matches=None if expected_stdout is None else text==expected_stdout,
                claim_scope='One explicit process run; this does not establish full feature, memory or ABI correctness.')
    (directory/'result.json').write_text(json.dumps(result,indent=2))
    return result
