from hutil.Qt import QtWidgets, QtCore, QtGui
from HoudiniProjectManager.core import schema, builder, projects, config
from HoudiniProjectManager.ui import editor


class ProjectCreationWizard(QtWidgets.QDialog):
    project_created = QtCore.Signal(object)  # Emits the new ProjectData

    def __init__(self, parent=None):
        super(ProjectCreationWizard, self).__init__(parent)
        self.setWindowTitle("Create New Project")
        self.resize(520, 750)  # Slightly taller for import section
        self.schema_manager = schema.SchemaManager()
        self.custom_field_rows = []  # Track custom field widgets

        # Import mode state
        self.import_mode = False
        self.scanned_work_areas = []

        # Load user settings for defaults
        import os
        import json
        settings_file = config.get_user_settings_path()
        self.user_settings = {}
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    self.user_settings = json.load(f)
            except:
                pass

        self.setup_ui()
        self.apply_styles()
        self.update_preview()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Header
        header = QtWidgets.QLabel("New Project")
        header.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold; 
            color: #fff;
            padding: 20px 25px;
            background: #252525;
            border-bottom: 2px solid #3d5a80;
        """)
        layout.addWidget(header)
        
        # Scroll area for form
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QtWidgets.QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: #1e1e1e; border: none; }")
        
        form_widget = QtWidgets.QWidget()
        form_widget.setStyleSheet("background: #1e1e1e;") # Explicitly set background
        form_layout = QtWidgets.QVBoxLayout(form_widget)
        form_layout.setSpacing(20)
        form_layout.setContentsMargins(25, 25, 25, 25)
        
        # === MODE TOGGLE ===
        toggle_layout = QtWidgets.QHBoxLayout()
        toggle_layout.setSpacing(0)
        
        self.mode_group = QtWidgets.QButtonGroup(self)
        self.mode_group.setExclusive(True)
        
        self.btn_create = QtWidgets.QPushButton("Create New")
        self.btn_create.setCheckable(True)
        self.btn_create.setChecked(True)
        
        self.btn_import = QtWidgets.QPushButton("Import Existing")
        self.btn_import.setCheckable(True)
        
        # Style the segmented control
        toggle_style = """
            QPushButton {
                background: #2a2a2a;
                color: #888;
                border: 1px solid #333;
                padding: 8px 0px;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:checked {
                background: #3d5a80;
                color: #fff;
                border: 1px solid #3d5a80;
            }
            QPushButton:hover:!checked {
                background: #333;
                color: #aaa;
            }
        """
        self.btn_create.setStyleSheet(toggle_style + "QPushButton { border-top-left-radius: 4px; border-bottom-left-radius: 4px; border-right: none; }")
        self.btn_import.setStyleSheet(toggle_style + "QPushButton { border-top-right-radius: 4px; border-bottom-right-radius: 4px; border-left: none; }")
        
        self.mode_group.addButton(self.btn_create, 0)
        self.mode_group.addButton(self.btn_import, 1)
        self.mode_group.idClicked.connect(self.switch_mode)
        
        toggle_layout.addWidget(self.btn_create)
        toggle_layout.addWidget(self.btn_import)
        
        form_layout.addLayout(toggle_layout)
        form_layout.addSpacing(10)
        
        # Container for the mode-specific options
        self.mode_stack = QtWidgets.QStackedWidget()
        form_layout.addWidget(self.mode_stack)
        
        # --- CREATE MODE PANEL ---
        self.create_panel = QtWidgets.QWidget()
        create_layout = QtWidgets.QVBoxLayout(self.create_panel)
        create_layout.setContentsMargins(0, 0, 0, 0)
        
        # === PRESET & LOCATION ===
        self.preset_group = self.create_group("Template & Location")
        preset_layout = QtWidgets.QFormLayout()
        preset_layout.setSpacing(12)
        
        # Preset Row with Edit Button inline
        preset_row = QtWidgets.QHBoxLayout()
        
        self.preset_combo = QtWidgets.QComboBox()
        templates = self.schema_manager.get_template_names()
        if templates:
            self.preset_combo.addItems(templates)
            self.preset_combo.insertItem(0, "Custom")
            self.preset_combo.setCurrentIndex(0)
        else:
            self.preset_combo.addItem("Custom")
            self.preset_combo.addItem("Default")
        
        self.edit_btn = QtWidgets.QPushButton("✎ Customize")
        self.edit_btn.setToolTip("Modify this preset just for this project")
        self.edit_btn.setStyleSheet("""
            QPushButton {
                 background: #2a2a2a; 
                 color: #bbb; 
                 border: 1px solid #444; 
                 border-radius: 3px;
                 padding: 4px 10px;
                 font-size: 11px;
            }
            QPushButton:hover { background: #333; color: #fff; border-color: #666; }
        """)
        self.edit_btn.clicked.connect(self.open_structure_editor)
        
        preset_row.addWidget(self.preset_combo)
        preset_row.addWidget(self.edit_btn)
        
        preset_layout.addRow("Preset:", preset_row)
        
        loc_layout = QtWidgets.QHBoxLayout()
        default_loc = self.user_settings.get("default_location", "C:/projects")
        self.root_edit = QtWidgets.QLineEdit(default_loc)
        self.root_edit.textChanged.connect(self.update_preview)
        self.browse_btn = QtWidgets.QPushButton("...")
        self.browse_btn.setFixedWidth(40)
        self.browse_btn.clicked.connect(self.browse_root)
        loc_layout.addWidget(self.root_edit)
        loc_layout.addWidget(self.browse_btn)
        preset_layout.addRow("Location:", loc_layout)
        
        # Path preview - subtle gray text below location
        self.path_preview = QtWidgets.QLabel("→ C:/projects/Personal/ProjectName")
        self.path_preview.setStyleSheet("color: #666; font-size: 10px; margin-left: 2px;")
        preset_layout.addRow("", self.path_preview)
        
        self.preset_group.layout().addLayout(preset_layout)
        create_layout.addWidget(self.preset_group)
        self.mode_stack.addWidget(self.create_panel)

        # --- IMPORT MODE PANEL ---
        self.import_panel = QtWidgets.QWidget()
        import_panel_layout = QtWidgets.QVBoxLayout(self.import_panel)
        import_panel_layout.setContentsMargins(0, 0, 0, 0)

        # === IMPORT EXISTING ===
        self.import_group = self.create_group("Import Existing Folder")
        import_layout = QtWidgets.QVBoxLayout()

        import_row = QtWidgets.QHBoxLayout()
        self.import_path_edit = QtWidgets.QLineEdit()
        self.import_path_edit.setPlaceholderText("Browse to existing project folder...")
        self.import_path_edit.textChanged.connect(self.on_import_path_changed)

        self.import_browse_btn = QtWidgets.QPushButton("Browse...")
        self.import_browse_btn.setFixedWidth(80)
        self.import_browse_btn.clicked.connect(self.browse_import_folder)

        import_row.addWidget(self.import_path_edit)
        import_row.addWidget(self.import_browse_btn)
        import_layout.addLayout(import_row)

        # Scan results display (initially hidden)
        self.scan_results = QtWidgets.QLabel("")
        self.scan_results.setStyleSheet("color: #50c878; font-size: 11px; margin-top: 5px;")
        self.scan_results.setVisible(False)
        import_layout.addWidget(self.scan_results)

        self.import_group.layout().addLayout(import_layout)
        import_panel_layout.addWidget(self.import_group)
        import_panel_layout.addStretch()
        self.mode_stack.addWidget(self.import_panel)

        # === PROJECT DETAILS ===
        details_group = self.create_group("Project Details")
        details_layout = QtWidgets.QFormLayout()
        details_layout.setSpacing(12)
        
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("Enter project name...")
        self.name_input.textChanged.connect(self.update_preview)
        details_layout.addRow("Project Name:", self.name_input)
        
        self.client_input = QtWidgets.QLineEdit()
        self.client_input.setPlaceholderText("Client or company name...")
        details_layout.addRow("Client:", self.client_input)
        
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItems(["Personal", "Client", "Quick R&D", "Other"])
        default_cat = self.user_settings.get("default_category", "Personal")
        idx = self.category_combo.findText(default_cat)
        if idx >= 0:
            self.category_combo.setCurrentIndex(idx)
        self.category_combo.currentIndexChanged.connect(self.update_preview)
        details_layout.addRow("Category:", self.category_combo)
        
        self.notes_input = QtWidgets.QTextEdit()
        self.notes_input.setPlaceholderText("Project notes, description, or goals...")
        self.notes_input.setMaximumHeight(80)
        details_layout.addRow("Notes:", self.notes_input)
        
        details_group.layout().addLayout(details_layout)
        form_layout.addWidget(details_group)
        
        # === TAGS ===
        tags_group = self.create_group("Tags")
        tags_layout = QtWidgets.QVBoxLayout()
        
        self.tags_input = QtWidgets.QLineEdit()
        self.tags_input.setPlaceholderText("e.g. vfx, character, urgent (comma separated)")
        tags_layout.addWidget(self.tags_input)
        
        tags_group.layout().addLayout(tags_layout)
        form_layout.addWidget(tags_group)
        
        form_layout.addStretch()
        scroll.setWidget(form_widget)
        layout.addWidget(scroll)
        
        # === FOOTER (Buttons only) ===
        footer = QtWidgets.QWidget()
        footer.setStyleSheet("background: #252525; border-top: 1px solid #333;")
        footer_layout = QtWidgets.QHBoxLayout(footer)
        footer_layout.setContentsMargins(25, 15, 25, 15)
        
        # Removed old Edit button from footer
        
        self.create_btn = QtWidgets.QPushButton("Create Project")
        self.create_btn.setStyleSheet("""
            QPushButton {
                background: #3d5a80;
                color: #fff;
                border: none;
                border-radius: 4px;
                padding: 12px 28px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover { background: #4a6d94; }
        """)
        self.create_btn.clicked.connect(self.create_project)
        
        footer_layout.addStretch()
        footer_layout.addWidget(self.create_btn)
        
        layout.addWidget(footer)

    def create_group(self, title):
        """Create a styled group box."""
        group = QtWidgets.QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #888;
                border: 1px solid #333;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px;
            }
        """)
        layout = QtWidgets.QVBoxLayout(group)
        layout.setContentsMargins(15, 20, 15, 15)
        return group
        
    # ... (Styles and Browse helpers same as before) ...
    def apply_styles(self):
        """Apply dark theme styling."""
        self.setStyleSheet("""
            QDialog {
                background: #1e1e1e;
                color: #ddd;
            }
            QLineEdit, QTextEdit, QComboBox {
                background: #252525;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px 10px;
                color: #ddd;
                font-size: 12px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #3d5a80;
                background: #2a2a2a;
            }
            QComboBox::drop-down {
                border: none;
                padding-right: 10px;
            }
            QLabel {
                color: #aaa;
                background: transparent;
            }
        """)

    def browse_root(self):
        import hou
        d = hou.ui.selectFile(title="Select Root Directory", file_type=hou.fileType.Directory)
        if d:
            self.root_edit.setText(d)

    def switch_mode(self, btn_id):
        is_import = (btn_id == 1)
        self.import_mode = is_import
        
        if is_import:
            self.mode_stack.setCurrentWidget(self.import_panel)
            self.create_btn.setText("Import Project")
        else:
            self.mode_stack.setCurrentWidget(self.create_panel)
            self.create_btn.setText("Create Project")
            self.update_preview()
            
    def update_preview(self):
        # Don't update preview if in import mode
        if self.import_mode:
            return
        root = self.root_edit.text().rstrip("/\\")
        category = self.category_combo.currentText()
        name = self.name_input.text() or "ProjectName"
        # User requested removing category from path
        preview_path = f"{root}/{name}"
        self.path_preview.setText(f"→ {preview_path}")

    def browse_import_folder(self):
        """Open folder selection for import."""
        import hou
        path = hou.ui.selectFile(
            title="Select Existing Project Folder",
            file_type=hou.fileType.Directory
        )
        if path:
            self.import_path_edit.setText(path)

    def on_import_path_changed(self):
        """Called when import path changes - scan the folder."""
        import os
        path = self.import_path_edit.text().strip()

        if not path or not os.path.isdir(path):
            self.clear_import_mode()
            return

        # Scan the folder
        from HoudiniProjectManager.core import scanner
        proj_scanner = scanner.ProjectScanner(path)
        hip_count, work_areas = proj_scanner.count_hip_files_and_work_areas()

        self.import_mode = True
        self.scanned_work_areas = work_areas

        # Update UI
        folder_count = len(work_areas)
        if hip_count > 0:
            self.scan_results.setText(f"Found {hip_count} hip file(s) in {folder_count} folder(s)")
            self.scan_results.setStyleSheet("color: #50c878; font-size: 11px; margin-top: 5px;")
        else:
            self.scan_results.setText("No hip files found (folder will still be imported)")
            self.scan_results.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")
        self.scan_results.setVisible(True)

        # Auto-fill project name from folder name
        folder_name = os.path.basename(path)
        if not self.name_input.text():
            self.name_input.setText(folder_name)

        # Update button text, even though stack takes care of visibility
        self.create_btn.setText("Import Project")

    def clear_import_mode(self):
        """Reset import mode state without breaking toggle layout."""
        self.scanned_work_areas = []
        self.scan_results.setVisible(False)
        self.update_preview()

    def create_project(self):
        import os
        name = self.name_input.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Missing Name", "Please enter a project name.")
            return

        # Collect tags
        raw_tags = self.tags_input.text().split(",")
        tags = [t.strip() for t in raw_tags if t.strip()]

        # === IMPORT MODE ===
        if self.import_mode:
            final_path = self.import_path_edit.text().strip().replace("\\", "/")

            # Store work areas in custom_fields for dashboard highlighting
            custom_fields = {}
            if self.scanned_work_areas:
                custom_fields["_work_areas"] = self.scanned_work_areas

            # Create ProjectData for imported project
            new_proj = projects.ProjectData(
                name,
                final_path,
                project_type="Imported",
                client=self.client_input.text(),
                notes=self.notes_input.toPlainText(),
                category=self.category_combo.currentText(),
                custom_fields=custom_fields,
                tags=tags
            )

            self.project_created.emit(new_proj)
            self.accept()
            return

        # === CREATE MODE (existing logic) ===
        template_name = self.preset_combo.currentText()
        
        if template_name == "Custom":
            # If user didn't customize it, create a basic default or assume empty
            template = None 
        else:
            template = self.schema_manager.get_template(template_name)

        # Build variables
        category = self.category_combo.currentText()
        
        # Expand Houdini env vars (e.g. $HOME, $DESKTOP) and normalize
        import hou
        raw_root = self.root_edit.text().rstrip("/\\")
        expanded_root = hou.text.expandString(raw_root).replace("\\", "/").rstrip("/")
        
        # Safety: if root already ends with the project name, strip it
        # (prevents doubled paths like Desktop/qqq/qqq)
        if expanded_root.lower().endswith("/" + name.lower()):
            expanded_root = expanded_root[:-(len(name) + 1)]
        
        vars = {
            "project_name": name,
            "project": name,
            "client": self.client_input.text(),
            "root": expanded_root,
            "category": category
        }

        # Build folder structure
        if template:
            b = builder.ProjectBuilder(template)
            try:
                final_path = b.build(vars)
                work_area = b.get_work_area()  # Get the folder marked as work area
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", str(e))
                return
        else:
            # Fallback: just create the folder (e.g. Empty Custom or Missing)
            final_path = f"{expanded_root}/{name}".replace("\\", "/")
            os.makedirs(final_path, exist_ok=True)
            work_area = final_path

        starter_hip = ""
        if work_area and os.path.exists(work_area):
            starter_hip = os.path.join(work_area, f"{name}_v001.hip").replace("\\", "/")

        # Create ProjectData
        custom_fields = {}
        if starter_hip:
            custom_fields["_last_hip_path"] = starter_hip

        new_proj = projects.ProjectData(
            name,
            final_path,
            project_type=template_name if template_name != "Custom" else "Custom",
            client=self.client_input.text(),
            notes=self.notes_input.toPlainText(),
            category=self.category_combo.currentText(),
            custom_fields=custom_fields,
            tags=tags
        )

        self.project_created.emit(new_proj)
        self.accept()
    
    def open_structure_editor(self):
        # Create dialog to host the editor
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Customize Project Structure")
        dlg.resize(600, 500)
        
        # Apply standard application theme!
        from HoudiniProjectManager.ui import style
        style.apply_theme(dlg)
        
        layout = QtWidgets.QVBoxLayout(dlg)
        
        # Load current preset data
        current_template_name = self.preset_combo.currentText()
        base_template = None
        
        # Build context from current Wizard values
        context = {
            "project_name": self.name_input.text() or "New Project",
            "location": self.root_edit.text()
        }
        
        ed = editor.StructureEditor(context=context)
        
        if current_template_name == "Custom":
             # Initialize with empty structure
             pass 
        else:
            base_template = self.schema_manager.get_template(current_template_name)
            # Initialize with current structure if available
            if base_template and "structure" in base_template:
                ed.load_structure_json(base_template["structure"])
            
        layout.addWidget(ed)
        
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        layout.addWidget(btns)
        
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            new_structure = ed.get_structure_json()
            
            # If it was "Custom", we give it a name like "Custom - ProjectName" or just internal
            if current_template_name == "Custom":
                custom_name = "Custom Structure"
                new_template = {
                    "name": custom_name,
                    "description": "Custom on-the-fly structure",
                    "root_path": "{root}/{project_name}",  # <- Added this!
                    "variables": {"JOB": "{root}/{project_name}"},
                    "structure": new_structure
                }
            else:
                custom_name = f"{current_template_name} (Custom)"
                new_template = base_template.copy()
                new_template["structure"] = new_structure
                new_template["name"] = custom_name
                if "root_path" not in new_template:
                    new_template["root_path"] = "{root}/{project_name}"
            
            # Store it
            self.schema_manager.templates[custom_name] = new_template
            
            # Update combo
            if self.preset_combo.findText(custom_name) == -1:
                self.preset_combo.addItem(custom_name)
            self.preset_combo.setCurrentText(custom_name)
