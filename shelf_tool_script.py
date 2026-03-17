"""
Standard Shelf Tool Script for Houdini Project Manager.
Use this for normal production usage.
"""
import hou
from HoudiniProjectManager import app
from hutil.Qt import QtCore

# Close existing instance if open (prevents multiple windows)
if hasattr(hou.session, "my_project_manager") and hou.session.my_project_manager:
    try:
        hou.session.my_project_manager.close()
    except:
        pass

# Create new instance
panel = app.ProjectManager()

# Keep reference alive in session to prevent garbage collection
hou.session.my_project_manager = panel

# Parent to main window and show
panel.setParent(hou.qt.mainWindow(), QtCore.Qt.Window)
panel.resize(900, 600)
panel.show()
