#!/usr/bin/env python3
"""Explicit integration validation; temporarily switches themes and restores selection.
Never authenticates, locks the real session, logs out, or invokes a power action.
"""
import sys, os, json, tempfile, ctypes as c, hashlib, fcntl, re, subprocess
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import theme as t
import components
os.environ.update(t.E)
gtk=c.CDLL('libgtk-3.so.0'); assert gtk.gtk_init_check(None,None)
gtk.gtk_css_provider_new.restype=c.c_void_p
gtk.gtk_css_provider_load_from_path.argtypes=[c.c_void_p,c.c_char_p,c.POINTER(c.c_void_p)]
xc=c.CDLL('libXcursor.so.1'); xc.XcursorFilenameLoadImage.argtypes=[c.c_char_p,c.c_int]; xc.XcursorFilenameLoadImage.restype=c.c_void_p
report=[]
def record(message): print(message,flush=True);report.append(message)
def compare(dest):
 for name,present in json.loads((dest/'manifest.json').read_text()).items():
  target=t.C/name
  assert target.exists()==present,name
  if present: assert target.read_bytes()==(dest/name).read_bytes(),name
 with tempfile.TemporaryDirectory(dir=t.S) as tmp:
  components.capture(Path(tmp),t.E)
  assert json.loads((Path(tmp)/'components.json').read_text())==json.loads((dest/'components.json').read_text())
with (t.S/'manager.lock').open('w') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX)
 active=(t.S/'active').read_text(); assert active in ['mosslight']+list(t.PROFILES)
 starting_main=(t.C/'hypr/hyprland.lua').read_text()
 try:
  for ident in ['mosslight']+list(t.PROFILES):
   t.select_profile(ident); t.apply()
   monitor=json.loads(t.run(['hyprctl','monitors','-j']).stdout)[0]
   assert monitor['reserved'][1]==20,monitor['reserved']
   assert monitor['scale']==1,monitor['scale']
   for option,field,value in [('general:border_size','int',1),('general:gaps_in','custom','3'),('general:gaps_out','custom','3')]:
    result=t.run(['hyprctl','getoption',option,'-j']); assert result.returncode==0
    if field=='int': assert json.loads(result.stdout)[field]==value
    else: assert '3' in result.stdout
   config=t.C/'hypr/hyprlock.conf'
   result=t.run(['hyprlock','--display','theme-studio-validation-does-not-exist','--config',str(config),'-v'])
   assert "Couldn't connect to a wayland compositor" in result.stdout,result.stdout
   assert not re.search(r'Config threw|Config error|config option .*does not exist',result.stdout,re.I),result.stdout
   path=t.H/'.themes'/('ThemeStudio-'+ident)/'gtk-3.0/gtk.css'
   error=c.c_void_p(); assert gtk.gtk_css_provider_load_from_path(gtk.gtk_css_provider_new(),str(path).encode(),c.byref(error))==1
   cursor=t.H/'.local/share/icons'/('ThemeStudio-'+ident)/'cursors/left_ptr'
   assert xc.XcursorFilenameLoadImage(str(cursor).encode(),24)
   e=t.E.copy(); e.update(QT_QPA_PLATFORM='offscreen',QT_FORCE_STDERR_LOGGING='1')
   proc=subprocess.Popen(['sddm-greeter-qt6','--test-mode','--theme','/usr/share/sddm/themes/mosslight-'+ident],env=e,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   try:
    output=proc.communicate(timeout=1.5)[0]; raise AssertionError('Greeter exited: '+output)
   except subprocess.TimeoutExpired:
    proc.terminate();output=proc.communicate(timeout=5)[0]
   assert 'Loading file:' in output,output
   assert not re.search('is not installed|is not a type|ReferenceError|TypeError|Cannot assign|failed to load',output,re.I),output
   assert ('Current=mosslight-'+ident) in components.CONF.read_text()
   record(ident+': apply / 20px bar / 1px border / 3px gaps / scale 1 / lock parser / GTK CSS / cursor decode / SDDM test mode PASS')
  t.upgrade_restore(); compare(t.S/'pre-v4'); record('Upgrade rollback: file bytes, absence, dconf values and SDDM state match pre-v4 PASS')
  t.select_profile(active);t.apply()
  t.restore('original');compare(t.S/'original');record('Original rollback: file bytes, absence, dconf values and SDDM state match baseline PASS')
  hashes=json.loads((t.S/'v3-baseline-hashes.json').read_text())
  for path,digest in hashes.items():
   if not path.endswith('/manifest.json'): assert hashlib.sha256((t.S/path).read_bytes()).hexdigest()==digest,path
  record('Existing baseline backup file contents preserved PASS')
 finally:
  # Retain all current monitor, input and shortcut preferences after testing historical restore.
  (t.C/'hypr/hyprland.lua').write_text(starting_main)
  t.select_profile(active);t.apply();record('Returned to user selection: '+active)
 (t.P/'VALIDATION-v4.0.txt').write_text('\n'.join(report)+'\n\nLock configuration parsed without connecting to a compositor; real unlock authentication was not exercised. SDDM validated in test mode; real login was not exercised.\n')
