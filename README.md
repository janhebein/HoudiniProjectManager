# HoudiniProjectManager

Small project manager panel for SideFX Houdini.

## Install

1. Copy this folder into:
   `C:\Users\<you>\Documents\houdini21.0\HoudiniProjectManager`
2. Copy `HoudiniProjectManager.json` into:
   `C:\Users\<you>\Documents\houdini21.0\packages\HoudiniProjectManager.json`
3. Restart Houdini.

The package file points to `$HOUDINI_USER_PREF_DIR/HoudiniProjectManager`.
If you keep the plugin somewhere else, update `HPM_LOCATION` in `HoudiniProjectManager.json`.

## Features

- Create new projects or import existing ones
- Browse folders and `.hip` files inside Houdini
- Quick open the latest recent Houdini file
- Sort project folders in the dashboard
- Save here and version up fast

## Open

- Add a **Project Manager** pane tab in Houdini
- Optional shelf button: create a normal shelf tool and paste the script from `shelf_tool_script.py`

## Notes

- Tested on Houdini 21
- `JOB` is set automatically when a project opens
- Project data is stored in your Houdini user prefs
