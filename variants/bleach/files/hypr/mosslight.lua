-- Mosslight: visual overrides only; the user's bindings/input remain intact.
hl.config({
 general = { gaps_in = 3, gaps_out = 3, border_size = 1,
   col = { active_border = "rgba(d4d3e6ff)", inactive_border = "rgba(45455fff)" } },
 decoration = { rounding = 0, active_opacity = 1.0, inactive_opacity = 1.0,
   shadow = { enabled = false }, blur = { enabled = false } },
 misc = { disable_hyprland_logo = true }
})
hl.on("hyprland.start", function () hl.exec_cmd("@PACKAGE@/theme.py start") end)

-- COMPONENTS-BEGIN
hl.env("XCURSOR_THEME", "ThemeStudio-bleach")
hl.bind("SUPER + L", hl.dsp.exec_cmd("@PACKAGE@/desktop.py lock"))
hl.bind("SUPER + SHIFT + P", hl.dsp.exec_cmd("@PACKAGE@/desktop.py power"))
-- COMPONENTS-END
