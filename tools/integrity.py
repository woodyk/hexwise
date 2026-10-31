#!/usr/bin/env python3
"""Verify or intentionally update the public source inventory. No network or execution."""
import argparse,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'.git','__pycache__','.venv','venv','build','dist','work','local-state','local-workspace'}
def files():
 return sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(part in EXCLUDED for part in p.relative_to(ROOT).parts) and p.name not in ('SHA256SUMS','.DS_Store') and p.suffix not in ('.pyc','.pyo'))
def inventory():
 return ''.join(hashlib.sha256(p.read_bytes()).hexdigest()+'  '+p.relative_to(ROOT).as_posix()+'\n' for p in files())
def check_profiles():
 first=ROOT/'framework/prompts';second=ROOT/'studio/profiles'
 a={p.relative_to(first).as_posix():p.read_bytes() for p in first.rglob('*') if p.is_file()}
 b={p.relative_to(second).as_posix():p.read_bytes() for p in second.rglob('*') if p.is_file()}
 if a!=b:raise ValueError('Studio and framework prompt libraries differ.')
def main():
 parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--check',action='store_true');mode.add_argument('--update',action='store_true');args=parser.parse_args()
 check_profiles();expected=inventory();manifest=ROOT/'SHA256SUMS'
 if args.update:manifest.write_text(expected);print('Updated inventory for',len(files()),'files.');return
 if not manifest.exists() or manifest.read_text()!=expected:raise SystemExit('Inventory differs. Inspect changes, then intentionally run --update.')
 print('Integrity and duplicate prompt-library checks passed for',len(files()),'files.')
if __name__=='__main__':main()
