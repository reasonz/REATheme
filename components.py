"""Transactional desktop integration; snapshots retain unset dconf values exactly."""
import json, shutil, subprocess, os
from pathlib import Path
P=Path(__file__).resolve().parent
H=Path.home(); S=H/'.local/state/mosslight'
KEYS=('gtk-theme','icon-theme','cursor-theme','cursor-size','color-scheme','font-name','monospace-font-name','document-font-name')
PREFIX='/org/gnome/desktop/interface/'
HELPER='/usr/local/sbin/mosslight-login-theme'
CONF=Path('/etc/sddm.conf.d/99-mosslight.conf')
def call(args,e,check=True):
 return subprocess.run(args,env=e,text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=check)
def capture(dest,e):
 data={key:call(['dconf','read',PREFIX+key],e).stdout.strip() for key in KEYS}
 data['sddm']=CONF.read_text().strip().split('Current=mosslight-')[-1] if CONF.exists() and 'Current=mosslight-' in CONF.read_text() else 'original'
 (dest/'components.json').write_text(json.dumps(data,indent=2))
def recover(dest,e):
 path=dest/'components.json'
 if not path.exists(): return
 data=json.loads(path.read_text())
 for key in KEYS:
  value=data.get(key,'')
  call(['dconf','write',PREFIX+key,value] if value else ['dconf','reset',PREFIX+key],e)
 if Path(HELPER).exists():
  args=['restore'] if data['sddm']=='original' else ['set',data['sddm']]
  call(['sudo','-n',HELPER,*args],e)
 # Hyprland's runtime cursor is separate from GTK preferences.
 theme=call(['gsettings','get','org.gnome.desktop.interface','cursor-theme'],e).stdout.strip().strip("'")
 size=call(['gsettings','get','org.gnome.desktop.interface','cursor-size'],e).stdout.strip()
 call(['hyprctl','setcursor',theme,size],e,False)
 # setcursor may publish cursor preferences; retain original unset values too.
 for key in ('cursor-theme','cursor-size'):
  value=data[key]
  call(['dconf','write',PREFIX+key,value] if value else ['dconf','reset',PREFIX+key],e)
def install_assets(ident):
 name='ThemeStudio-'+ident
 for source,target in [(P/'components/icons'/name,H/'.local/share/icons'/name),(P/'components/gtk'/name,H/'.themes'/name)]:
  shutil.copytree(source,target,dirs_exist_ok=True)
def apply(ident,e):
 name='ThemeStudio-'+ident
 install_assets(ident)
 # Reload CSS after upgrading an already selected palette.
 current=call(['gsettings','get','org.gnome.desktop.interface','gtk-theme'],e).stdout.strip().strip("'")
 if current==name: call(['gsettings','set','org.gnome.desktop.interface','gtk-theme','Adwaita'],e)
 values={'gtk-theme':name,'icon-theme':name,'cursor-theme':name,'cursor-size':'24','color-scheme':'prefer-dark','font-name':'Alibaba PuHuiTi 3.0 10','document-font-name':'Alibaba PuHuiTi 3.0 10','monospace-font-name':'monospace 10'}
 for key,value in values.items(): call(['gsettings','set','org.gnome.desktop.interface',key,value],e)
 call(['hyprctl','setcursor',name,'24'],e)
 if not Path(HELPER).exists(): raise RuntimeError('登录页组件尚未安装，请先运行 sudo ./Install-System.py')
 call(['sudo','-n',HELPER,'set',ident],e)
