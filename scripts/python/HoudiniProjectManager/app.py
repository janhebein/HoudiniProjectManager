from HoudiniProjectManager.core import projects, scanner, schema, builder, config
from HoudiniProjectManager.ui import gallery, tree, dashboard, wizard, editor, settings, style
from hutil.Qt import QtWidgets, QtCore, QtGui
import importlib
from datetime import datetime
import os

# Development mode block removed - handled by pypanel reload logic

# Migrate old config files on first run
config.migrate_old_config()

class ProjectManager(QtWidgets.QWidget):
    def __init__(self):
        super(ProjectManager, self).__init__()
        self.setWindowTitle("Custom Project Manager")
        style.apply_theme(self) # <--- APPLY THEME
        self.project_manager = projects.ProjectListManager()
        self.current_project = None
        
        self.setup_ui()
        self.refresh_projects()

    def setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0,0,0,0)
        
        # Top Bar (in a widget so we can hide it)
        self.top_bar_widget = QtWidgets.QWidget()
        top_bar = QtWidgets.QHBoxLayout(self.top_bar_widget)
        top_bar.setContentsMargins(10,10,10,10)
        
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search project, tags, client...")
        self.search_bar.setStyleSheet("background-color: #1e1e1e; border-radius: 5px; padding: 5px; color: #ddd;")
        # Connect to gallery filtering
        self.search_bar.textChanged.connect(lambda text: self.gallery.set_search_filter(text))
        
        self.add_btn = QtWidgets.QPushButton("+ New Project")
        self.add_btn.clicked.connect(self.create_new_project)
        
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_projects)
        
        # Settings Button (styled like other buttons)
        self.gear_btn = QtWidgets.QPushButton("Settings")
        icon_path = os.path.join(config.get_icons_dir(), "settings.svg")
        if os.path.exists(icon_path):
            self.gear_btn.setIcon(QtGui.QIcon(icon_path))
        self.gear_btn.clicked.connect(self.open_settings)

        top_bar.addWidget(self.search_bar)
        top_bar.addWidget(self.refresh_btn)
        top_bar.addWidget(self.gear_btn)
        top_bar.addWidget(self.add_btn)
        
        main_layout.addWidget(self.top_bar_widget)
        
        # Stacked Widget for View Switching
        self.stack = QtWidgets.QStackedWidget()
        main_layout.addWidget(self.stack)

        # View 1: Gallery
        self.gallery = gallery.ProjectGallery()
        self.gallery.project_clicked.connect(self.open_project)
        self.gallery.recent_hip_requested.connect(self.open_recent_hip)
        self.gallery.project_removed.connect(self.remove_project_dialog)
        self.gallery.project_updated.connect(self.on_project_updated)
        self.stack.addWidget(self.gallery)
        
        # View 2: Dashboard (The new Premium View)
        self.dashboard_view = dashboard.DashboardView()
        self.dashboard_view.back_clicked.connect(self.go_back_to_gallery)
        self.dashboard_view.current_hip_changed.connect(self.on_current_hip_changed)
        self.stack.addWidget(self.dashboard_view)

    def refresh_projects(self):
        # Check modifiers for Hard Reload (Shift + Click)
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            self.reload_modules_and_restart()
            return
            
        self.gallery.refresh(self.project_manager.projects)

    def reload_modules_and_restart(self):
        """Recursively reload all package modules and restart the interface."""
        print("[HoudiniProjectManager] Reloading modules...")
        import sys
        import importlib
        import HoudiniProjectManager
        
        package_name = "HoudiniProjectManager"
        
        # 1. Reload all submodules
        for name, module in list(sys.modules.items()):
            if name.startswith(package_name + "."):
                try:
                    importlib.reload(module)
                except Exception as e:
                    print(f"Failed to reload {name}: {e}")
                    
        # 2. Reload main package
        try:
            importlib.reload(HoudiniProjectManager)
            importlib.reload(HoudiniProjectManager.app)
        except Exception as e:
            print(f"Failed to reload package root: {e}")
            
        # 3. Notify
        QtWidgets.QMessageBox.information(self, "Reloaded", "Modules reloaded.\nClose and re-open the window to see full changes.")

    def create_new_project(self):
        # Open the Wizard
        self.wizard = wizard.ProjectCreationWizard(self)
        self.wizard.project_created.connect(self.on_project_created)
        self.wizard.show()
        
    def on_project_created(self, project_data):
        # Add the full project data object (with notes, category, custom_fields)
        self.project_manager.projects.append(project_data)
        self.project_manager.save()
        self.refresh_projects()
        
        # Auto open the project immediately (deferred to let wizard close safely first)
        starter_hip = self.normalize_path(project_data.custom_fields.get("_last_hip_path", ""))
        QtCore.QTimer.singleShot(0, lambda: self.open_project(project_data, hip_path=starter_hip or None))

    def open_project(self, project, hip_path=None):
        # Hide the top bar for cleaner dashboard view
        self.top_bar_widget.hide()
        self.current_project = project
        
        # Update last_opened timestamp
        project.last_opened = datetime.now().isoformat()
        normalized_hip_path = self.normalize_path(hip_path)
        if normalized_hip_path and os.path.isfile(normalized_hip_path):
            project.custom_fields["_last_hip_path"] = normalized_hip_path
        self.project_manager.save()
        
        # Set Environment Variables
        import hou
        try:
            hou.putenv("JOB", project.path)
            
            # Enable/Disable auto-save based on setting
            import json
            settings_file = config.get_user_settings_path()
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    user_settings = json.load(f)
                    
                    # Default is False
                    enabled = user_settings.get("autosave_enabled", False)
                    
                    # Use standard hscript command
                    cmd = "autosave on" if enabled else "autosave off"
                    hou.hscript(cmd)
            
            if normalized_hip_path and os.path.isfile(normalized_hip_path):
                hou.hipFile.load(normalized_hip_path, suppress_save_prompt=True)
                self.store_last_hip_for_project(project, normalized_hip_path)
            elif normalized_hip_path:
                hou.hipFile.clear(suppress_save_prompt=True)
                hou.hipFile.save(normalized_hip_path)
                self.store_last_hip_for_project(project, normalized_hip_path)

            # Load Dashboard
            self.dashboard_view.load_project(project)
            if not normalized_hip_path:
                self.store_last_hip_for_project(project)
            self.stack.setCurrentWidget(self.dashboard_view)
            
            self.setWindowTitle(f"Project Manager - {project.name}")
            
        except Exception as e:
            print(f"Error opening project: {e}")

    def go_back_to_gallery(self):
        self.store_last_hip_for_project(self.current_project)
        self.top_bar_widget.show()  # Show the top bar again
        self.gallery.refresh(self.project_manager.projects)
        self.stack.setCurrentWidget(self.gallery)
        self.setWindowTitle("Custom Project Manager")

    def toggle_view_mode(self):
        if self.view_btn.isChecked():
            self.view_btn.setText("Grid View")
            self.gallery.set_view_mode("list")
        else:
            self.view_btn.setText("List View")
            self.gallery.set_view_mode("icon")

    def remove_project_dialog(self, project):
        # Ask for confirmation
        res = QtWidgets.QMessageBox.question(
            self, 
            "Remove Project?", 
            f"Are you sure you want to remove '{project.name}' from the list?\n\n(This will NOT delete files on disk)",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if res == QtWidgets.QMessageBox.Yes:
            self.project_manager.remove_project(project)
            self.refresh_projects()

    def open_settings(self):
        dlg = settings.SettingsDialog(self)
        dlg.exec_()
        # Refresh if needed?
        if hasattr(self, 'wizard'):
            # If wizard was open... but it's modal so it wouldn't be.
            pass
    
    def on_project_updated(self, project):
        """Called when project details are edited."""
        self.project_manager.save()

    def normalize_path(self, path):
        if not path:
            return ""
        return os.path.normpath(path).replace("\\", "/")

    def get_current_hip_path(self):
        import hou

        try:
            current_path = self.normalize_path(hou.hipFile.name())
        except Exception:
            return ""

        if not current_path:
            return ""
        if "untitled" in os.path.basename(current_path).lower():
            return ""
        if not os.path.isfile(current_path):
            return ""
        return current_path

    def is_path_inside_project(self, file_path, project_root):
        normalized_file = os.path.normcase(os.path.normpath(file_path))
        normalized_root = os.path.normcase(os.path.normpath(project_root))

        try:
            return os.path.commonpath([normalized_file, normalized_root]) == normalized_root
        except ValueError:
            return False

    def store_last_hip_for_project(self, project, hip_path=None):
        if not project:
            return

        resolved_path = self.normalize_path(hip_path) if hip_path else self.get_current_hip_path()
        if not resolved_path or not os.path.isfile(resolved_path):
            return
        if not self.is_path_inside_project(resolved_path, project.path):
            return

        if project.custom_fields.get("_last_hip_path") == resolved_path:
            return

        project.custom_fields["_last_hip_path"] = resolved_path
        self.project_manager.save()

    def on_current_hip_changed(self, hip_path):
        self.store_last_hip_for_project(self.current_project, hip_path)

    def open_recent_hip(self, project, hip_path):
        self.open_project(project, hip_path=hip_path)

def createInterface():
    return ProjectManager()
