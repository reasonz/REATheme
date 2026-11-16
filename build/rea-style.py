#!/usr/bin/env python3
"""Apply REATheme typography to generated palettes and legacy bar presets."""
from pathlib import Path
import json,re
P=Path(__file__).resolve().parents[1]
FONT='Alibaba PuHuiTi 3.0'
FONTCONF='''<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">
<fontconfig>
  <alias binding="strong"><family>sans-serif</family><prefer><family>Alibaba PuHuiTi 3.0</family><family>Noto Sans CJK SC</family></prefer></alias>
  <alias binding="strong"><family>system-ui</family><prefer><family>Alibaba PuHuiTi 3.0</family></prefer></alias>
  <alias binding="strong"><family>monospace</family><prefer><family>Noto Sans Mono</family><family>Noto Sans Mono CJK SC</family></prefer></alias>
</fontconfig>
'''
for f in [P/'files']+list((P/'variants').glob('*/files')):
 dest=f/'fontconfig/conf.d/60-reatheme.conf';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(FONTCONF)
 path=f/'gtk-3.0/settings.ini';s=path.read_text();s=re.sub(r'^gtk-font-name=.*\n','',s,flags=re.M);path.write_text(s+'gtk-font-name='+FONT+' 10\n')
 path=f/'foot/foot.ini';path.write_text(re.sub(r'^font=.*$', 'font=monospace:size=10.5',path.read_text(),flags=re.M))
 path=f/'rofi/config.rasi';path.write_text(re.sub(r'font: ".*?";', 'font: "'+FONT+' 11";',path.read_text()))
 path=f/'mako/config';path.write_text(re.sub(r'^font=.*$', 'font='+FONT+' 10',path.read_text(),flags=re.M))
 path=f/'hypr/hyprlock.conf';s=path.read_text().replace('font_family = Adwaita Mono','font_family = '+FONT);s=s.replace('text = $TIME\n    color', 'text = $TIME\n    color');s=re.sub(r'(text = \$TIME.*?font_family = )[^\n]+',r'\1monospace',s,flags=re.S);path.write_text(s)
for path in [P/'files/waybar/style.css']+list((P/'variants').glob('*/files/waybar/style.css'))+list((P/'bar-presets').glob('*/*/style.css')):
 s=path.read_text().split('/* REATHEME FONTS */')[0];s=re.sub(r'font-family:[^;]+;', 'font-family: "'+FONT+'", sans-serif;',s,count=1)
 path.write_text(s+'\n/* REATHEME FONTS */\n#clock, #cpu, #memory, #battery, #workspaces { font-family: monospace; }\n')
for path in [P/'files/waybar/config.jsonc']+list((P/'variants').glob('*/files/waybar/config.jsonc'))+list((P/'bar-presets').glob('*/*/config.jsonc')):
 s=path.read_text().replace('@PACKAGE@/theme.py menu','@PACKAGE@/REATheme');path.write_text(s)
path=P/'sddm/Main.qml';s=path.read_text().replace('Adwaita Mono','monospace').replace('Noto Sans CJK SC',FONT).replace('THEME STUDIO','REATHEME');path.write_text(s)
print('REATheme typography generated')
