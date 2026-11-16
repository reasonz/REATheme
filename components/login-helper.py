#!/usr/bin/python3 -I
"""Root-owned helper: only select one of seven preinstalled login themes or restore."""
import sys, os, json, fcntl
from pathlib import Path
ALLOWED=('mosslight','dragonball','bleach','gundam','pacific-rim','goku-mature','halo-fusion')
CONF=Path('/etc/sddm.conf.d/99-mosslight.conf')
STATE=Path('/var/lib/mosslight-login')
def main():
 if os.geteuid()!=0: raise SystemExit('root required')
 args=sys.argv[1:]
 if args==['restore']:
  original=json.loads((STATE/'original.json').read_text())
  if not original['exists']: CONF.unlink(missing_ok=True); return
  text=original['text']
 elif len(args)==2 and args[0]=='set' and args[1] in ALLOWED:
  theme='mosslight-'+args[1]
  if not (Path('/usr/share/sddm/themes')/theme/'Main.qml').is_file(): raise SystemExit('Theme not installed')
  text='[Theme]\nCurrent='+theme+'\n'
 else: raise SystemExit('Invalid action')
 CONF.parent.mkdir(exist_ok=True)
 temp=CONF.with_suffix('.tmp')
 with temp.open('w') as f: f.write(text)
 temp.chmod(0o644); os.replace(temp,CONF)
if __name__=='__main__':
 with (STATE/'lock').open('w') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX); main()
