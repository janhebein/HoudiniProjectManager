"""
HoudiniProjectManager - A project management tool for Houdini

Usage in Python Panel:
    from HoudiniProjectManager import app
    def createInterface():
        return app.ProjectManager()

Usage as standalone window:
    from HoudiniProjectManager import app
    panel = app.ProjectManager()
    panel.setParent(hou.qt.mainWindow(), 0)
    panel.show()
"""

__version__ = "1.1.1"
__author__ = "Your Name"

from . import app

def createInterface():
    """Convenience function for Python Panels."""
    return app.ProjectManager()

def launch():
    """Launch as a standalone window."""
    import hou
    panel = app.ProjectManager()
    panel.setParent(hou.qt.mainWindow(), 0)
    panel.setWindowFlags(hou.qt.QtCore.Qt.Window)
    panel.resize(900, 600)
    panel.show()
    return panel
