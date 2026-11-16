#!/usr/bin/env python3
"""Generate the seven matching desktop component palettes and original vector icons."""
import json, struct
from pathlib import Path
P=Path(__file__).resolve().parents[1]
profiles={'mosslight':dict(name='苔光 · 雨夜庭院',label='MOSS',bg='111b16',panel='2d3d2e',accent='b4c398',fg='d3dbc6',muted='788b74',border='344637'),**json.loads((P/'profiles.json').read_text())}
def put(p,s):
 p.parent.mkdir(parents=True,exist_ok=True); p.write_text(s)
def cursor(accent):
 # Original angular arrow, encoded as standard Xcursor images at 24/32/48px.
 polygon=[(2,1),(2,20),(7,15),(11,23),(15,21),(11,13),(19,13)]
 def inside(x,y):
  result=False
  for (ax,ay),(bx,by) in zip(polygon,polygon[1:]+polygon[:1]):
   if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax: result=not result
  return result
 chunks=[]
 for size in (24,32,48):
  pixels=[]
  for y in range(size):
   for x in range(size):
    xx=(x+.5)*24/size; yy=(y+.5)*24/size
    if not inside(xx,yy): value=0
    elif any(not inside(xx+dx,yy+dy) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]): value=0xff11151a
    else: value=0xff000000|int(accent,16)
    pixels.append(value)
  chunks.append(struct.pack('<9I',36,0xfffd0002,size,1,size,size,round(size*2/24),round(size/24),0)+struct.pack('<%dI'%len(pixels),*pixels))
 offset=16+12*3; toc=b''
 for size,data in zip((24,32,48),chunks):
  toc+=struct.pack('<3I',0xfffd0002,size,offset); offset+=len(data)
 return struct.pack('<4I',0x72756358,16,0x10000,3)+toc+b''.join(chunks)
for ident,p in profiles.items():
 root=P if ident=='mosslight' else P/'variants'/ident
 f=root/'files'; name='ThemeStudio-'+ident
 wall='@PACKAGE@/wallpaper.png' if ident=='mosslight' else '@PACKAGE@/variants/'+ident+'/wallpaper.png'
 bg,panel,acc,fg,muted,border=[p[k] for k in ('bg','panel','accent','fg','muted','border')]
 put(f/'hypr/hyprlock.conf',f'''# Theme Studio / {p['name']}
general {{
    hide_cursor = true
}}
background {{
    monitor =
    path = {wall}
    color = rgb({bg})
    blur_passes = 0
    brightness = 0.65
}}
label {{
    monitor =
    text = {p['label']}  /  SESSION LOCKED
    color = rgb({acc})
    font_family = Adwaita Mono
    font_size = 12
    position = 64, 294
    halign = left
    valign = bottom
}}
label {{
    monitor =
    text = $TIME
    color = rgb({fg})
    font_family = Adwaita Mono
    font_size = 54
    position = 60, 200
    halign = left
    valign = bottom
}}
label {{
    monitor =
    text = cmd[update:60000] date +"%Y.%m.%d  /  %A"
    color = rgb({muted})
    font_family = Adwaita Mono
    font_size = 12
    position = 64, 164
    halign = left
    valign = bottom
}}
input-field {{
    monitor =
    size = 320, 40
    position = 64, 96
    halign = left
    valign = bottom
    outline_thickness = 1
    rounding = 0
    inner_color = rgba({bg}ee)
    outer_color = rgb({border})
    check_color = rgb({acc})
    fail_color = rgb(d47f78)
    font_color = rgb({fg})
    font_family = Adwaita Mono
    placeholder_text = Password · Enter to unlock
    fail_text = $PAMFAIL
    fade_on_empty = false
    dots_size = 0.22
    dots_spacing = 0.35
}}
''')
 put(f/'gtk-3.0/settings.ini',f'''[Settings]
gtk-theme-name={name}
gtk-icon-theme-name={name}
gtk-cursor-theme-name={name}
gtk-cursor-theme-size=24
gtk-application-prefer-dark-theme=true
''')
 css=f'''@import url("resource:///org/gtk/libgtk/theme/Adwaita/gtk-contained-dark.css");
@define-color theme_bg_color #{bg};
@define-color theme_fg_color #{fg};
@define-color theme_base_color #{bg};
@define-color theme_text_color #{fg};
@define-color theme_selected_bg_color #{panel};
@define-color theme_selected_fg_color #{acc};
@define-color insensitive_fg_color #{muted};
@define-color borders #{border};
window, .background {{ background-color: #{bg}; color: #{fg}; }}
headerbar, toolbar, menubar, statusbar {{ background-image: none; background-color: #{panel}; color: #{fg}; box-shadow: none; }}
button, entry, combobox, menu, notebook, frame {{ border-radius: 0; }}
button {{ background-image: none; background-color: #{panel}; color: #{fg}; border-color: #{border}; box-shadow: none; text-shadow: none; }}
button:hover, button:checked {{ background-color: #{border}; color: #{acc}; }}
entry {{ background: #{bg}; color: #{fg}; border-color: #{border}; box-shadow: none; }}
entry:focus {{ border-color: #{acc}; }}
treeview, iconview, .view, list {{ background-color: #{bg}; color: #{fg}; }}
treeview:selected, iconview:selected, row:selected, selection {{ background-color: #{panel}; color: #{acc}; }}
.view:selected, .view:selected:focus, treeview.view:selected, treeview.view:selected:focus, treeview.view:selected:backdrop {{ background-color: #{panel}; color: #{acc}; }}
menu, menuitem {{ background-color: #{panel}; color: #{fg}; }}
menuitem:hover {{ background-color: #{border}; color: #{acc}; }}
notebook > header {{ background-color: #{panel}; }}
notebook > header tab:checked {{ box-shadow: inset 0 -1px #{acc}; }}
scrollbar slider {{ background-color: #{border}; min-width: 5px; min-height: 5px; border-radius: 0; }}
separator {{ background-color: #{border}; }}
'''
 put(P/'components/gtk'/name/'gtk-3.0/gtk.css',css)
 put(P/'components/gtk'/name/'gtk-3.0/gtk-dark.css',css)
 icons=P/'components/icons'/name
 put(icons/'index.theme',f'''[Icon Theme]
Name={name}
Comment=Theme Studio precision line icons and accent cursor
Inherits=Adwaita,breeze-dark,hicolor
Directories=scalable/places
[scalable/places]
Size=48
Type=Scalable
MinSize=16
MaxSize=256
Context=Places
''')
 marks={'folder':'','user-home':'M19 29l5-4 5 4v7h-10z','folder-documents':'M21 24h7v12h-7z M23 28h3 M23 31h3','folder-download':'M24 24v11m-4-4 4 4 4-4','folder-pictures':'M18 35l6-7 4 4 3-3 3 6','folder-music':'M23 34v-9l7-1v9 M19 34h4 M26 33h4','folder-videos':'M20 25l10 6-10 5z','folder-desktop':'M18 25h14v9H18z M25 34v3','folder-publicshare':'M19 29h11 M26 25l4 4-4 4','folder-templates':'M20 25h10v11H20z','folder-saved-search':'M20 25h7v7h-7z M27 32l5 5','user-trash':'M20 25h10l-1 12h-8z M18 23h14 M23 20h4'}
 for icon,mark in marks.items():
  svg=f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48"><path d="M5 12h15l4 5h19v23H5z" fill="#{panel}" stroke="#{acc}" stroke-width="1.3"/><path d="M5 19h38 M8 36v-5 M35 36h5" fill="none" stroke="#{muted}" stroke-width="1"/><path d="{mark}" fill="none" stroke="#{acc}" stroke-width="1.4" stroke-linejoin="miter"/></svg>'
  put(icons/'scalable/places'/f'{icon}.svg',svg)
 (icons/'cursors').mkdir(exist_ok=True)
 for alias in ('left_ptr','default','arrow','top_left_arrow'):
  (icons/'cursors'/alias).write_bytes(cursor(acc))
 lua=f/'hypr/mosslight.lua'; text=lua.read_text().split('-- COMPONENTS-BEGIN')[0].rstrip()
 put(lua,text+f'''\n\n-- COMPONENTS-BEGIN
hl.env("XCURSOR_THEME", "{name}")
hl.bind("SUPER + L", hl.dsp.exec_cmd("@PACKAGE@/desktop.py lock"))
hl.bind("SUPER + SHIFT + P", hl.dsp.exec_cmd("@PACKAGE@/desktop.py power"))
-- COMPONENTS-END
''')
 bar=f/'waybar/config.jsonc'; data=json.loads(bar.read_text())
 data['custom/power']={'format':'⏻','tooltip-format':'电源菜单 · Super Shift P\n右键：锁屏 · Super L','on-click':'@PACKAGE@/desktop.py power','on-click-right':'@PACKAGE@/desktop.py lock'}
 if 'custom/power' not in data['modules-right']: data['modules-right'].append('custom/power')
 put(bar,json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 style=f/'waybar/style.css'; text=style.read_text().split('/* COMPONENTS */')[0]
 put(style,text+f'\n/* COMPONENTS */\n#custom-power {{ color: #{acc}; padding: 0 8px; margin: 0; min-height: 0; border: none; }}\n')
 conf=f'''[General]
title={p['label']}
subtitle={p['name']}
background=wallpaper.png
bg=#{bg}
panel=#{panel}
accent=#{acc}
fg=#{fg}
muted=#{muted}
border=#{border}
'''
 put(P/'sddm'/ident/'theme.conf',conf)
 put(P/'sddm'/ident/'metadata.desktop',f'''[SddmGreeterTheme]
Name=Theme Studio · {p['name']}
Description=Theme Studio matched login screen
Author=Theme Studio
Type=sddm-theme
Version=4.0
MainScript=Main.qml
ConfigFile=theme.conf
Theme-Id=mosslight-{ident}
Theme-API=2.0
QtVersion=6
''')
print('Generated',len(profiles),'component palettes')
import runpy
if (P/'build/rea-style.py').exists(): runpy.run_path(str(P/'build/rea-style.py'))
