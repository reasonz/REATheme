-- Mosslight: visual overrides only; the user's bindings/input remain intact.
hl.config({
 general = { gaps_in = 5, gaps_out = 14, border_size = 2,
   col = { active_border = "rgba(d4d3e6ff)", inactive_border = "rgba(45455fff)" } },
 decoration = { rounding = 0, active_opacity = 1.0, inactive_opacity = 1.0,
   shadow = { enabled = false }, blur = { enabled = false } },
 misc = { disable_hyprland_logo = true }
})
hl.on("hyprland.start", function () hl.exec_cmd("@PACKAGE@/theme.py start") end)
