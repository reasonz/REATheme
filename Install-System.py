#!/usr/bin/env python3
"""One-time system asset installation. Never restarts the display manager."""
import json, os, pwd, shutil, subprocess, sys
from pathlib import Path
P=Path(__file__).resolve().parent
if os.geteuid()!=0: raise SystemExit('Run with sudo: sudo ./Install-System.py')
user=os.environ.get('SUDO_USER','')
if not user or user=='root' or not all(c.isalnum() or c in '_-' for c in user): raise SystemExit('Run via sudo from your desktop account')
pwd.getpwnam(user)
fonts=Path('/usr/local/share/fonts/REATheme');fonts.mkdir(parents=True,exist_ok=True)
for source in (P/'fonts').glob('*.ttf'):
 shutil.copyfile(source,fonts/source.name);(fonts/source.name).chmod(0o644)
subprocess.run(['fc-cache','-f',str(fonts)],check=True)
ids=['mosslight']+list(json.loads((P/'profiles.json').read_text()))
state=Path('/var/lib/mosslight-login'); state.mkdir(mode=0o755,exist_ok=True)
conf=Path('/etc/sddm.conf.d/99-mosslight.conf')
if not (state/'original.json').exists():
 (state/'original.json').write_text(json.dumps({'exists':conf.exists(),'text':conf.read_text() if conf.exists() else ''}))
for ident in ids:
 dest=Path('/usr/share/sddm/themes')/('mosslight-'+ident); dest.mkdir(exist_ok=True)
 for name in ('theme.conf','metadata.desktop'): shutil.copyfile(P/'sddm'/ident/name,dest/name)
 shutil.copyfile(P/'sddm/Main.qml',dest/'Main.qml')
 shutil.copyfile(P/'wallpaper.png' if ident=='mosslight' else P/'variants'/ident/'wallpaper.png',dest/'wallpaper.png')
 for file in dest.iterdir(): file.chmod(0o644)
 dest.chmod(0o755)
helper=Path('/usr/local/sbin/mosslight-login-theme'); helper.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(P/'components/login-helper.py',helper); helper.chmod(0o755)
commands=[str(helper)+' set '+ident for ident in ids]+[str(helper)+' restore']
sudoers=Path('/etc/sudoers.d/mosslight-login-theme')
temp=sudoers.with_suffix('.pending'); temp.write_text(user+' ALL=(root) NOPASSWD: '+', '.join(commands)+'\n'); temp.chmod(0o440)
try: subprocess.run(['visudo','-cf',str(temp)],check=True); os.replace(temp,sudoers)
finally: temp.unlink(missing_ok=True)
print('Installed seven login themes and a restricted selection helper; SDDM was not restarted.')
