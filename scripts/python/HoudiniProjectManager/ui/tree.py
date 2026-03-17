from hutil.Qt import QtWidgets, QtCore, QtGui
import os
import subprocess
import hou # We need hou to load files

class ProjectTreeView(QtWidgets.QWidget):
    def __init__(self):
        super(ProjectTreeView, self).__init__()
        
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        # Navigation Bar
        self.nav_bar = QtWidgets.QHBoxLayout()
        self.back_btn = QtWidgets.QPushButton("← Back to Gallery")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                color: #4a90e2; 
                text-align: left;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { text-decoration: underline; }
        """)
        self.nav_bar.addWidget(self.back_btn)
        self.nav_bar.addStretch()
        self.layout.addLayout(self.nav_bar)
        
        # The Tree
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #2b2b2b;
                border: none;
                color: #eee;
            }
            QTreeWidget::item {
                padding: 6px;
            }
            QTreeWidget::item:hover {
                background-color: #333;
            }
            QTreeWidget::item:selected {
                background-color: #444;
                color: #4a90e2;
            }
        """)
        self.tree.itemDoubleClicked.connect(self.handle_double_click)
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.layout.addWidget(self.tree)

    def load_project(self, project_path, structure_data):
        self.tree.clear()
        self.current_project_path = project_path
        
        # Build tree from the dictionary returned by scanner
        root_item = QtWidgets.QTreeWidgetItem(self.tree)
        root_item.setText(0, os.path.basename(project_path))
        root_item.setData(0, QtCore.Qt.UserRole, project_path)
        root_item.setData(0, QtCore.Qt.UserRole + 1, "folder")
        root_item.setExpanded(True)
        
        self._populate_tree(root_item, structure_data)

    def _populate_tree(self, parent_item, data):
        for child in data.get("children", []):
            item = QtWidgets.QTreeWidgetItem(parent_item)
            item.setText(0, child["name"])
            item.setData(0, QtCore.Qt.UserRole, child["path"])
            item.setData(0, QtCore.Qt.UserRole + 1, child["type"])
            
            if child["type"] == "folder":
                item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
                if child.get("children"):
                    self._populate_tree(item, child)
            else:
                item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_FileIcon))

    def handle_double_click(self, item, column):
        path = item.data(0, QtCore.Qt.UserRole)
        type_ = item.data(0, QtCore.Qt.UserRole + 1)
        
        if type_ == "file":
             if hou.hipFile.hasUnsavedChanges():
                 res = hou.ui.displayMessage("Save current file?", buttons=("Yes", "No", "Cancel"))
                 if res == 2: return
                 if res == 0: hou.hipFile.save()
            
             print(f"Loading {path}...")
             hou.hipFile.load(path)

    def show_context_menu(self, position):
        """Show context menu for folder/file actions."""
        item = self.tree.itemAt(position)
        if not item:
            return
        
        path = item.data(0, QtCore.Qt.UserRole)
        type_ = item.data(0, QtCore.Qt.UserRole + 1)
        
        menu = QtWidgets.QMenu()
        
        # Common actions
        open_explorer_action = menu.addAction("📂 Open in Explorer")
        
        if type_ == "folder":
            menu.addSeparator()
            create_subfolder_action = menu.addAction("📁 Create Subfolder...")
            rename_action = menu.addAction("✏️ Rename...")
            menu.addSeparator()
            delete_action = menu.addAction("🗑️ Delete Folder")
        else:
            menu.addSeparator()
            rename_action = menu.addAction("✏️ Rename...")
            menu.addSeparator()
            delete_action = menu.addAction("🗑️ Delete File")
            create_subfolder_action = None
        
        action = menu.exec_(self.tree.viewport().mapToGlobal(position))
        
        if action == open_explorer_action:
            self.open_in_explorer(path, type_)
        elif action == rename_action:
            self.rename_item(item, path)
        elif action == delete_action:
            self.delete_item(item, path, type_)
        elif create_subfolder_action and action == create_subfolder_action:
            self.create_subfolder(item, path)

    def open_in_explorer(self, path, type_):
        """Open the folder/file location in Windows Explorer."""
        if type_ == "folder":
            target = path
        else:
            target = os.path.dirname(path)
        
        # Windows-specific
        subprocess.Popen(f'explorer "{os.path.normpath(target)}"')

    def create_subfolder(self, parent_item, parent_path):
        """Create a new subfolder."""
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Create Subfolder", "Folder name:"
        )
        if ok and name:
            new_path = os.path.join(parent_path, name)
            try:
                os.makedirs(new_path, exist_ok=True)
                # Add to tree
                new_item = QtWidgets.QTreeWidgetItem(parent_item)
                new_item.setText(0, name)
                new_item.setData(0, QtCore.Qt.UserRole, new_path)
                new_item.setData(0, QtCore.Qt.UserRole + 1, "folder")
                new_item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
                parent_item.setExpanded(True)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not create folder: {e}")

    def rename_item(self, item, path):
        """Rename a file or folder."""
        old_name = os.path.basename(path)
        new_name, ok = QtWidgets.QInputDialog.getText(
            self, "Rename", "New name:", text=old_name
        )
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(path), new_name)
            try:
                os.rename(path, new_path)
                item.setText(0, new_name)
                item.setData(0, QtCore.Qt.UserRole, new_path)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not rename: {e}")

    def delete_item(self, item, path, type_):
        """Delete a file or folder after confirmation."""
        msg = f"Are you sure you want to delete '{os.path.basename(path)}'?"
        if type_ == "folder":
            msg += "\n\nThis will delete ALL contents inside!"
        
        res = QtWidgets.QMessageBox.warning(
            self, "Delete?", msg,
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if res == QtWidgets.QMessageBox.Yes:
            try:
                if type_ == "folder":
                    import shutil
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                
                # Remove from tree
                parent = item.parent()
                if parent:
                    parent.removeChild(item)
                else:
                    index = self.tree.indexOfTopLevelItem(item)
                    self.tree.takeTopLevelItem(index)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not delete: {e}")

