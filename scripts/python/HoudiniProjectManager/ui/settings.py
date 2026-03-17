from hutil.Qt import QtWidgets, QtCore
from HoudiniProjectManager.core import schema, config
from HoudiniProjectManager.ui import editor, style

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(SettingsDialog, self).__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(600, 500)
        style.apply_theme(self)
        
        self.schema_manager = schema.SchemaManager()
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Tabs
        self.tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.tabs)
        
        # Tab 1: Presets
        self.presets_tab = QtWidgets.QWidget()
        self.setup_presets_tab()
        self.tabs.addTab(self.presets_tab, "Presets")
        
        # Tab 2: General (Placeholder)
        self.general_tab = QtWidgets.QWidget()
        self.setup_general_tab()
        self.tabs.addTab(self.general_tab, "General")
        
        # Close Button
        btn_box = QtWidgets.QHBoxLayout()
        btn_box.addStretch()
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_box.addWidget(close_btn)
        layout.addLayout(btn_box)
        
    def setup_general_tab(self):
        layout = QtWidgets.QVBoxLayout(self.general_tab)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Settings storage path
        import os
        import json
        self.settings_file = config.get_user_settings_path()
        self.settings = self.load_settings()
        
        # Form layout for settings
        form = QtWidgets.QFormLayout()
        form.setSpacing(15)
        
        # Auto-Save Toggle
        self.autosave_check = QtWidgets.QCheckBox("Enable Houdini Auto-Save when opening projects")
        self.autosave_check.setChecked(self.settings.get("autosave_enabled", False))
        self.autosave_check.stateChanged.connect(self.save_settings)
        form.addRow("Auto-Save:", self.autosave_check)
        
        # Default Location
        loc_layout = QtWidgets.QHBoxLayout()
        self.default_loc_edit = QtWidgets.QLineEdit(self.settings.get("default_location", "C:/projects"))
        self.default_loc_edit.textChanged.connect(self.save_settings)
        browse_btn = QtWidgets.QPushButton("...")
        browse_btn.setFixedWidth(40)
        browse_btn.clicked.connect(self.browse_default_location)
        loc_layout.addWidget(self.default_loc_edit)
        loc_layout.addWidget(browse_btn)
        form.addRow("Default Location:", loc_layout)
        
        # Default Category
        self.default_cat_combo = QtWidgets.QComboBox()
        self.default_cat_combo.addItems(["Personal", "Client", "Quick R&D", "Other"])
        current_cat = self.settings.get("default_category", "Personal")
        idx = self.default_cat_combo.findText(current_cat)
        if idx >= 0:
            self.default_cat_combo.setCurrentIndex(idx)
        self.default_cat_combo.currentIndexChanged.connect(self.save_settings)
        form.addRow("Default Category:", self.default_cat_combo)
        
        layout.addLayout(form)
        
        # Info label
        info = QtWidgets.QLabel("Settings are saved automatically.")
        info.setStyleSheet("color: #666; font-size: 10px; margin-top: 10px;")
        layout.addWidget(info)
        
        layout.addStretch()
    
    def load_settings(self):
        import json
        import os
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_settings(self):
        import json
        self.settings = {
            "autosave_enabled": self.autosave_check.isChecked(),
            "default_location": self.default_loc_edit.text(),
            "default_category": self.default_cat_combo.currentText()
        }
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def browse_default_location(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Default Location", self.default_loc_edit.text())
        if d:
            self.default_loc_edit.setText(d.replace("\\", "/"))

    def setup_presets_tab(self):
        layout = QtWidgets.QVBoxLayout(self.presets_tab)
        
        # List of Presets
        self.list_widget = QtWidgets.QListWidget()
        self.list_widget.itemDoubleClicked.connect(self.edit_preset)
        layout.addWidget(self.list_widget)
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        self.new_btn = QtWidgets.QPushButton("New Preset")
        self.new_btn.clicked.connect(self.create_preset)
        
        self.edit_btn = QtWidgets.QPushButton("Edit")
        self.edit_btn.clicked.connect(self.edit_preset)
        
        self.del_btn = QtWidgets.QPushButton("Delete")
        self.del_btn.clicked.connect(self.delete_preset)
        
        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        
        layout.addLayout(btn_layout)
        
        self.refresh_list()
        
    def refresh_list(self):
        self.list_widget.clear()
        self.schema_manager.reload_templates()
        names = self.schema_manager.get_template_names()
        for n in sorted(names):
            self.list_widget.addItem(n)
            
    def create_preset(self):
        # Open blank editor
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("New Preset Structure")
        dlg.resize(600, 500)
        layout = QtWidgets.QVBoxLayout(dlg)
        
        ed = editor.StructureEditor()
        layout.addWidget(ed)
        
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            # Ask for name
            name, ok = QtWidgets.QInputDialog.getText(self, "Preset Name", "Enter name for new preset:")
            if ok and name:
                structure = ed.get_structure_json()
                
                # Create Template Dict
                # Only Standard variable job root supported for now
                data = {
                    "name": name,
                    "root_path": "{root}/{project_name}", # Default assumption
                    "structure": structure,
                    "variables": {"JOB": "{root}/{project_name}"}
                }
                
                self.schema_manager.save_template(name, data)
                self.refresh_list()

    def edit_preset(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        name = item.text()
        template = self.schema_manager.get_template(name)
        if not template: return
        
        # Open Editor
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(f"Edit Preset: {name}")
        dlg.resize(600, 500)
        layout = QtWidgets.QVBoxLayout(dlg)
        
        ed = editor.StructureEditor()
        # Load data!
        if template.get("structure"):
            ed.load_structure_json(template.get("structure"))
        
        layout.addWidget(ed)
        
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            structure = ed.get_structure_json()
            
            # Update Template
            template["structure"] = structure
            
            self.schema_manager.save_template(name, template)
            self.refresh_list()
            
    def delete_preset(self):
        item = self.list_widget.currentItem()
        if not item: return
        
        name = item.text()
        res = QtWidgets.QMessageBox.question(self, "Delete Preset", f"Are you sure you want to delete '{name}'?")
        if res == QtWidgets.QMessageBox.Yes:
            self.schema_manager.delete_template(name)
            self.refresh_list()
