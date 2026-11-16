#!/usr/bin/env python3
"""Theme Studio: user-level transactions and a restricted system login-theme helper."""
import os, sys, json, shutil, subprocess, time, tempfile, fcntl
import components
from pathlib import Path
P=Path(__file__).resolve().parent
H=Path.home(); C=H/'.config'; S=H/'.local/state/mosslight'; S.mkdir(parents=True,exist_ok=True)
PROFILE='mosslight'
F=P/'files'
PROFILES=json.loads((P/'profiles.json').read_text()) if (P/'profiles.json').exists() else {}
def select_profile(ident):
 global PROFILE,F
 if ident!='mosslight' and ident not in PROFILES: raise RuntimeError('Unknown theme: '+ident)
 PROFILE=ident; F=P/'files' if ident=='mosslight' else P/'variants'/ident/'files'
def title(): return '苔光 · Mosslight' if PROFILE=='mosslight' else PROFILES[PROFILE]['name']
FILES=sorted(str(p.relative_to(P/'files')) for p in (P/'files').rglob('*') if p.is_file())+['hypr/hyprland.lua']

def env():
 e=os.environ.copy(); e['XDG_RUNTIME_DIR']=f'/run/user/{os.getuid()}'
 e['DBUS_SESSION_BUS_ADDRESS']='unix:path='+e['XDG_RUNTIME_DIR']+'/bus'
 try:
  items=json.loads(subprocess.check_output(['hyprctl','instances','-j'],env=e))
  if items: e.update(HYPRLAND_INSTANCE_SIGNATURE=items[0]['instance'],WAYLAND_DISPLAY=items[0]['wl_socket'])
 except (ValueError,subprocess.SubprocessError): pass
 return e
E=env()
def run(args,check=False):
 return subprocess.run(args,env=E,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=check)
def snapshot(dest):
 dest.mkdir(parents=True); manifest={}
 for name in FILES:
  src=C/name; manifest[name]=src.exists()
  if src.exists():
   target=dest/name; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,target)
 (dest/'manifest.json').write_text(json.dumps(manifest,indent=2))
 components.capture(dest,E)
def copy_atomic(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True)
 temp=dst.with_name(dst.name+'.mosslight-tmp'); shutil.copy2(src,temp); os.replace(temp,dst)
def recover(dest):
 for name,present in json.loads((dest/'manifest.json').read_text()).items():
  if present: copy_atomic(dest/name,C/name)
  else: (C/name).unlink(missing_ok=True)
def baseline():
 if (S/'original/manifest.json').exists():
  # Extend old manifests only for newly managed files; never replace old backups.
  if not (S/'pre-v4/manifest.json').exists():
   snapshot(S/'pre-v4')
   (S/'pre-v4/active').write_text((S/'active').read_text() if (S/'active').exists() else 'mosslight')
  for dest in (S/'original',S/'previous',S/'pre-v4',S/'pre-reatheme'):
   if not (dest/'manifest.json').exists(): continue
   manifest=json.loads((dest/'manifest.json').read_text())
   for name in FILES:
    if name in manifest: continue
    src=C/name; manifest[name]=src.exists()
    if src.exists(): copy_atomic(src,dest/name)
   (dest/'manifest.json').write_text(json.dumps(manifest,indent=2))
   if not (dest/'components.json').exists(): components.capture(dest,E)
   else:
    # Newly managed preferences retain their state from before the upgrade.
    data=json.loads((dest/'components.json').read_text())
    for key in components.KEYS:
     if key not in data: data[key]=components.call(['dconf','read',components.PREFIX+key],E).stdout.strip()
    (dest/'components.json').write_text(json.dumps(data,indent=2))
  return
 snapshot(S/'previous')
 shutil.copytree(S/'previous',S/'original')
 # Adopt the existing pre-customization backup on this machine, without changing it.
 old=sorted((H/'.local/share').glob('pixel-desktop-backup-*/manifest.json'))
 if old:
  source=old[0].parent; mapping=json.loads((S/'original/manifest.json').read_text())
  for name,present in json.loads(old[0].read_text()).items():
   if name not in mapping: continue
   mapping[name]=present
   if present: copy_atomic(source/name,S/'original'/name)
   else: (S/'original'/name).unlink(missing_ok=True)
  (S/'original/manifest.json').write_text(json.dumps(mapping,indent=2))
def stop():
 for name in ('waybar','hyprpaper','mako'): run(['pkill','-u',str(os.getuid()),'-x',name])
def start():
 for name in ('waybar','hyprpaper','mako'):
  if run(['pgrep','-u',str(os.getuid()),'-x',name]).returncode:
   with (S/(name+'.log')).open('a') as log:
    subprocess.Popen([name],env=E,stdout=log,stderr=log,stdin=subprocess.DEVNULL,start_new_session=True)
def validate():
 for args in (['foot','--check-config'],['rofi','-dump-theme']):
  r=run(args)
  if r.returncode: raise RuntimeError(r.stdout)
 r=run(['hyprctl','reload'])
 if r.returncode: raise RuntimeError(r.stdout)
 time.sleep(.5)
 errors=run(['hyprctl','configerrors'])
 if errors.returncode==0 and errors.stdout.strip(): raise RuntimeError(errors.stdout)
def install_launchers():
 apps=H/'.local/share/applications'; apps.mkdir(parents=True,exist_ok=True)
 for old in ('mosslight','mosslight-apply','mosslight-restore','mosslight-components-restore'):
  (apps/(old+'.desktop')).unlink(missing_ok=True)
 (apps/'REATheme.desktop').write_text(f'[Desktop Entry]\nType=Application\nName=REATheme\nGenericName=桌面主题应用\nComment=横向壁纸卡片 · 全套主题切换与回退\nExec="{P}/REATheme"\nIcon={P}/app/reatheme.svg\nTerminal=false\nStartupWMClass=REATheme\nCategories=Settings;DesktopSettings;\nKeywords=theme;主题;壁纸;REA;\nActions=Manage;Reapply;Restore;\n\n[Desktop Action Manage]\nName=管理与回退\nExec="{P}/theme.py" manage\n\n[Desktop Action Reapply]\nName=重新应用上次主题\nExec="{P}/theme.py" reapply\n\n[Desktop Action Restore]\nName=恢复组件升级前桌面\nExec="{P}/theme.py" upgrade-restore\n')
 binary=H/'.local/bin';binary.mkdir(parents=True,exist_ok=True)
 wrapper=binary/'REATheme';wrapper.write_text('#!/bin/sh\nexec "'+str(P/'REATheme')+'" "$@"\n');wrapper.chmod(0o755)
def apply():
 for name in ('hyprctl','waybar','hyprpaper','mako','rofi','foot','hyprlock','gsettings','dconf'):
  if not shutil.which(name): raise RuntimeError('缺少组件: '+name)
 wallpaper=P/'wallpaper.png' if PROFILE=='mosslight' else P/'variants'/PROFILE/'wallpaper.png'
 if not wallpaper.is_file(): raise RuntimeError('壁纸缺失')
 baseline()
 txn=Path(tempfile.mkdtemp(prefix='transaction-',dir=S)); txn.rmdir(); snapshot(txn)
 try:
  components.install_assets(PROFILE)
  for name in FILES:
   if name=='hypr/hyprland.lua': continue
   src=F/name
   if name.startswith('waybar/') and (S/'bar-style').exists() and (S/'bar-style').read_text()=='classic':
    src=P/'bar-presets/v2.1'/PROFILE/Path(name).name
   text=src.read_text().replace('@PACKAGE@',str(P))
   target=C/name; target.parent.mkdir(parents=True,exist_ok=True)
   tmp=target.with_name(target.name+'.mosslight-tmp'); tmp.write_text(text); os.replace(tmp,target)
  # Preserve current input/bindings on repeat apply. First application starts from pre-theme config.
  current=(C/'hypr/hyprland.lua').read_text()
  if '-- MOSS-BEGIN' in current: base=current.split('-- MOSS-BEGIN')[0]
  elif (S/'active').exists() and (S/'active').read_text()=='original': base=current
  else: base=(S/'original/hypr/hyprland.lua').read_text()
  base=base.replace('local menu = "rofi -show run"','local menu = "rofi -show drun"')
  (C/'hypr/hyprland.lua').write_text(base.rstrip()+'\n\n-- MOSS-BEGIN\ndofile(os.getenv("HOME") .. "/.config/hypr/mosslight.lua")\n-- MOSS-END\n')
  validate(); components.apply(PROFILE,E); stop(); start(); time.sleep(1)
  for name in ('waybar','hyprpaper','mako'):
   if run(['pgrep','-u',str(os.getuid()),'-x',name]).returncode: raise RuntimeError(name+' failed; see '+str(S/(name+'.log')))
  (S/'active').write_text(PROFILE); (S/'last-theme').write_text(PROFILE); install_launchers()
 except Exception:
  recover(txn); run(['hyprctl','reload']); time.sleep(.3); components.recover(txn,E); stop()
  for name,config in [('waybar','waybar/config.jsonc'),('hyprpaper','hypr/hyprpaper.conf'),('mako','mako/config')]:
   if (C/config).exists():
    with (S/(name+'.log')).open('a') as log: subprocess.Popen([name],env=E,stdout=log,stderr=log,start_new_session=True)
  raise
 finally: shutil.rmtree(txn)
 print(title()+' 已应用。')
def restore(which):
 source=S/which
 if not (source/'manifest.json').exists(): raise RuntimeError('尚无备份，请先应用主题。')
 recover(source); stop(); run(['hyprctl','reload']); time.sleep(.3); components.recover(source,E); (S/'active').write_text(which)
 if which=='previous': start()
 print('已恢复'+('美化前原始配置' if which=='original' else '本次修改前配置')+'。注销重新登录可清除旧背景残留。')
def upgrade_restore():
 source=S/'pre-v4'
 if not (source/'manifest.json').exists(): raise RuntimeError('没有 v4 升级前备份')
 recover(source); run(['hyprctl','reload']); time.sleep(.3); components.recover(source,E); stop(); start()
 (S/'active').write_text((source/'active').read_text())
 print('已恢复组件升级前桌面；重新应用任意主题即可恢复完整组件。')
def reapply():
 ident=(S/'last-theme').read_text() if (S/'last-theme').exists() else 'mosslight'
 select_profile(ident); apply()
def bar_style(style):
 if style not in ('classic','designed'): raise RuntimeError('bar-style: classic or designed')
 active=(S/'active').read_text() if (S/'active').exists() else 'mosslight'
 if active not in ['mosslight']+list(PROFILES): raise RuntimeError('请先选择一个主题')
 previous=(S/'bar-style').read_text() if (S/'bar-style').exists() else 'designed'
 (S/'bar-style').write_text(style)
 try:
  select_profile(active); apply()
 except Exception:
  (S/'bar-style').write_text(previous); raise
def menu():
 options=[('mosslight','苔光 · 雨夜庭院')]+[(key,val['name']) for key,val in PROFILES.items()]
 choices='\n'.join([name for _,name in options]+['重新应用上次主题','锁屏','电源菜单','顶部栏：恢复旧版','顶部栏：应用专属设计','恢复组件升级前桌面','恢复美化前原始桌面','恢复最初像素桌面','打开主题文件夹'])
 current=(S/'active').read_text() if (S/'active').exists() else 'none'
 r=subprocess.run(['rofi','-dmenu','-i','-p','REATheme', '-mesg','管理与回退  /  '+current],input=choices,text=True,stdout=subprocess.PIPE,env=E)
 if r.returncode: return
 selected=r.stdout.strip()
 for ident,name in options:
  if selected==name: select_profile(ident); apply(); return
 if selected=='顶部栏：恢复旧版': bar_style('classic')
 elif selected=='重新应用上次主题': reapply()
 elif selected=='锁屏': subprocess.Popen([str(P/'desktop.py'),'lock'],env=E)
 elif selected=='电源菜单': subprocess.Popen([str(P/'desktop.py'),'power'],env=E)
 elif selected=='恢复组件升级前桌面': upgrade_restore()
 elif selected=='顶部栏：应用专属设计': bar_style('designed')
 elif selected.startswith('恢复美化前'): restore('original')
 elif selected.startswith('恢复最初'): restore('previous')
 elif selected.startswith('打开'): subprocess.Popen(['xdg-open',str(P)],env=E)
if __name__=='__main__':
 try:
  action=sys.argv[1] if len(sys.argv)>1 else 'menu'
  if action=='menu': os.execv(str(P/'REATheme'),[str(P/'REATheme')])
  with (S/'manager.lock').open('w') as lock:
   fcntl.flock(lock,fcntl.LOCK_EX)
   action=sys.argv[1] if len(sys.argv)>1 else 'menu'
   if action=='apply':
    select_profile(sys.argv[2] if len(sys.argv)>2 else 'mosslight'); apply()
   elif action=='bar-style': bar_style(sys.argv[2])
   elif action=='restore': restore('original')
   elif action=='previous': restore('previous')
   elif action=='upgrade-restore': upgrade_restore()
   elif action=='reapply': reapply()
   elif action=='start': start()
   elif action=='manage': menu()
   elif action=='status': print((S/'active').read_text() if (S/'active').exists() else '未应用')
   else: raise RuntimeError('Usage: theme.py [menu|apply|restore|previous|status]')
 except Exception as exc:
  print(str(exc),file=sys.stderr)
  if shutil.which('notify-send'): run(['notify-send','苔光主题操作失败',str(exc)[:500]])
  sys.exit(1)
