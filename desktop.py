#!/usr/bin/env python3
"""User-invoked lock and power controls; never run power actions during theme apply."""
import subprocess, sys, os, time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from theme import E, run, P, S, PROFILES

def lock():
 if run(['pgrep','-u',str(os.getuid()),'-x','hyprlock']).returncode == 0: return
 with (S/'hyprlock.log').open('a') as log:
  subprocess.Popen(['hyprlock'],env=E,stdout=log,stderr=log,start_new_session=True)

def choose(items,prompt,message):
 result=subprocess.run(['rofi','-dmenu','-i','-no-custom','-p',prompt,'-mesg',message,'-theme-str','window { width: 400px; } listview { lines: 5; fixed-height: false; }'],input='\n'.join(items),text=True,stdout=subprocess.PIPE,env=E)
 return result.stdout.strip() if result.returncode==0 else None

def power():
 active=(S/'active').read_text() if (S/'active').exists() else 'mosslight'
 label=PROFILES.get(active,{}).get('label','MOSS')
 selected=choose(['锁屏','注销','重新启动','关机','取消'],label+' / POWER','选择操作 · Esc 关闭')
 if selected=='锁屏': lock(); return
 if selected not in ('注销','重新启动','关机'): return
 if choose(['取消','确认'+selected],label+' / CONFIRM','即将'+selected+'，请先保存工作')!='确认'+selected: return
 args={'注销':['hyprctl','dispatch','hl.dsp.exit()'],'重新启动':['systemctl','reboot'],'关机':['systemctl','poweroff']}[selected]
 run(args,check=True)

if __name__=='__main__':
 action=sys.argv[1] if len(sys.argv)>1 else 'power'
 if action=='lock': lock()
 elif action=='power': power()
 else: raise SystemExit('Usage: desktop.py lock|power')
