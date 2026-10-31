"""Bounded file-structure checks. No execution and no claims about behavior or ABI."""
import json
import struct
from core import detect, sha


def check_candidate(data, filename='', profile=''):
    errors=[]; warnings=[]; details={}
    kind='unknown'
    def need(condition,message):
        if not condition:errors.append(message)
        return condition
    if data.startswith(b'\x7fELF'):
        kind='ELF'
        if need(len(data)>=16,'Truncated ELF identification.'):
            bits,encoding=data[4],data[5]
            need(bits in (1,2),'Invalid ELF class.')
            need(encoding in (1,2),'Invalid ELF byte order.')
            need(data[6]==1,'Unsupported ELF identification version.')
            if bits in (1,2) and encoding in (1,2):
                size=52 if bits==1 else 64;order='<' if encoding==1 else '>'
                if need(len(data)>=size,'Truncated ELF header.'):
                    fields=struct.unpack_from(order+('HHIIIIIHHHHHH' if bits==1 else 'HHIQQQIHHHHHH'),data,16)
                    typ,machine,version,entry,phoff,shoff,flags,ehsize,phsize,phnum,shsize,shnum,shstr=fields
                    details.update(bits=32 if bits==1 else 64,machine=machine,entry=entry,program_headers=phnum,sections=shnum)
                    need(version==1,'Unsupported ELF header version.')
                    need(ehsize>=size and ehsize<=len(data),'Invalid ELF header size.')
                    if phnum==65535 or (shoff and shnum==0) or shstr==65535:
                        warnings.append('Extended ELF numbering needs a full loader validator.')
                    else:
                        if phnum and need(phsize>=(32 if bits==1 else 56),'Invalid program header size.') and need(phoff>=ehsize and phoff+phsize*phnum<=len(data),'Program header table extends outside file.'):
                            for i in range(phnum):
                                h=struct.unpack_from(order+('IIIIIIII' if bits==1 else 'IIQQQQQQ'),data,phoff+i*phsize)
                                segment_offset,filesz,memsz=(h[1],h[4],h[5]) if bits==1 else (h[2],h[5],h[6])
                                need(segment_offset+filesz<=len(data),'Segment extends outside file.')
                                if h[0]==1:need(filesz<=memsz,'Load segment file size exceeds memory size.')
                        if shnum and need(shsize>=(40 if bits==1 else 64),'Invalid section header size.'):
                            need(shoff>=ehsize and shoff+shsize*shnum<=len(data),'Section header table extends outside file.')
    elif data.startswith(b'MZ'):
        kind='PE'
        if need(len(data)>=64,'Truncated DOS header.'):
            offset=int.from_bytes(data[60:64],'little')
            if need(offset>=64 and offset+24<=len(data),'PE header offset is outside file.') and need(data[offset:offset+4]==b'PE\0\0','Missing PE signature.'):
                machine,sections,_,_,_,optional_size,_=struct.unpack_from('<HHIIIHH',data,offset+4)
                details.update(machine=machine,sections=sections)
                start=offset+24;table=start+optional_size
                if need(optional_size>=2 and table<=len(data),'Invalid PE optional header.'):
                    need(int.from_bytes(data[start:start+2],'little') in (0x10b,0x20b),'Unknown PE optional header format.')
                if need(table+sections*40<=len(data),'PE section table extends outside file.'):
                    for i in range(sections):
                        section=table+i*40;size,location=struct.unpack_from('<II',data,section+16)
                        if size:need(location+size<=len(data),'PE section data extends outside file.')
    elif data[:4] in (b'\xcf\xfa\xed\xfe',b'\xce\xfa\xed\xfe',b'\xfe\xed\xfa\xcf',b'\xfe\xed\xfa\xce'):
        kind='Mach-O';little=data[:1] in (b'\xcf',b'\xce');bits=64 if data[:4] in (b'\xcf\xfa\xed\xfe',b'\xfe\xed\xfa\xcf') else 32
        size=32 if bits==64 else 28;order='<' if little else '>'
        if need(len(data)>=size,'Truncated Mach-O header.'):
            cpu,subtype,typ,count,cmdsize,flags=struct.unpack_from(order+'IIIIII',data,4)
            details.update(bits=bits,cpu=cpu,commands=count)
            if need(size+cmdsize<=len(data),'Mach-O load commands extend outside file.'):
                end=size+cmdsize;position=size
                if need(count<=cmdsize//8,'Invalid Mach-O command count.'):
                    for _ in range(count):
                        if not need(position+8<=end,'Truncated Mach-O load command.'):break
                        command,length=struct.unpack_from(order+'II',data,position)
                        if not need(length>=8 and length%4==0 and position+length<=end,'Invalid Mach-O load command size.'):break
                        position+=length
                    need(position==end,'Mach-O command sizes do not match header.')
    elif data.startswith(b'\0asm'):
        kind='WebAssembly'
        if need(len(data)>=8,'Truncated WebAssembly header.'):
            need(data[4:8] in (b'\x01\0\0\0',b'\x0d\0\x01\0'),'Unknown WebAssembly binary version.')
            pos=8
            while pos<len(data):
                section=data[pos];pos+=1;length=0;shift=0
                while True:
                    if pos>=len(data) or shift>=35:
                        errors.append('Invalid WebAssembly section length.');pos=len(data);break
                    value=data[pos];pos+=1;length|=(value&127)<<shift;shift+=7
                    if not value&128:break
                if not need(pos+length<=len(data),'WebAssembly section extends outside file.'):break
                pos+=length
            warnings.append('Section payloads, instructions and imports require a matching WASM validator.')
    elif profile=='web-document':
        kind='text'
        try:
            text=data.decode('utf-8');details['utf8']=True
            if filename.lower().endswith('.json'):json.loads(text);details['json_syntax']=True
            if filename.lower().endswith('.py'):compile(text,filename,'exec');details['python_syntax']=True
        except (UnicodeDecodeError,ValueError,SyntaxError) as error:errors.append('Document syntax or encoding failed: '+str(error)[:300])
    else:warnings.append('Unrecognized format; choose a target profile and matching validator.')
    detected=detect(data,filename)
    if detected and profile and detected!=profile and detected!='web-document':
        warnings.append('Header suggests '+detected+'; confirm the selected platform and ABI ('+profile+').')
    return dict(sha256=sha(data),bytes=len(data),format=kind,detected_profile=detected,structural='failed' if errors else 'basic_checks_passed' if kind!='unknown' else 'unverified',errors=errors,warnings=warnings,details=details,behavior='not_run',native_execution='not_run',claim_scope='Basic bounds and syntax checks only; full loader, ABI, signatures and behavior remain unverified.')
