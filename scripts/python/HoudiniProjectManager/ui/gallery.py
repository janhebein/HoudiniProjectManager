from hutil.Qt import QtWidgets, QtCore, QtGui
import os

HOUDINI_ICON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons", "Houdini3D_icon.jpg")

class DoubleClickToolButton(QtWidgets.QToolButton):
    double_clicked = QtCore.Signal()

    def mouseDoubleClickEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.double_clicked.emit()
            event.accept()
            return
        super(DoubleClickToolButton, self).mouseDoubleClickEvent(event)

class ProjectGallery(QtWidgets.QWidget):
    project_clicked = QtCore.Signal(object)
    recent_hip_requested = QtCore.Signal(object, str)
    project_removed = QtCore.Signal(object)
    project_updated = QtCore.Signal(object)

    def __init__(self):
        super(ProjectGallery, self).__init__()
        self.all_projects = []  # Store all projects for filtering
        self.recent_hip_project = None
        self.recent_hip_path = ""
        
        # Load heart icon
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")
        heart_path = os.path.join(icons_dir, "heart.svg")
        self.heart_icon = QtGui.QIcon(heart_path) if os.path.exists(heart_path) else None
        self.houdini_icon = QtGui.QIcon(HOUDINI_ICON_PATH) if os.path.exists(HOUDINI_ICON_PATH) else None
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Filter Bar
        self.setup_filter_bar(layout)
        
        # Project List (Table View)
        self.table = QtWidgets.QTreeWidget()
        self.table.setHeaderLabels(["", "Name", "Client", "Category", "Status", "Tags", "Notes"])
        self.table.setColumnWidth(0, 30)   # Favorite star
        self.table.setColumnWidth(1, 160)  # Name
        self.table.setColumnWidth(2, 90)   # Client
        self.table.setColumnWidth(3, 70)   # Category
        self.table.setColumnWidth(4, 100)  # Status
        self.table.setColumnWidth(5, 150)  # Tags
        self.table.setColumnWidth(6, 180)  # Notes
        self.table.setRootIsDecorated(False)
        self.table.setAlternatingRowColors(False)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)  # Multi-select
        self.table.itemDoubleClicked.connect(self.handle_click)
        self.table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        self.table.setStyleSheet("""
            QTreeWidget {
                background-color: #1a1a1a;
                border: none;
                color: #ddd;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 10px 8px;
                border-bottom: 1px solid #2a2a2a;
            }
            QTreeWidget::item:selected {
                background-color: #3d5a80;
                color: #fff;
            }
            QTreeWidget::item:hover {
                background-color: #252525;
            }
            QHeaderView::section {
                background-color: #252525;
                color: #888;
                padding: 8px 10px;
                border: none;
                border-bottom: 2px solid #3d5a80;
                font-size: 11px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.table)
    
    def setup_filter_bar(self, parent_layout):
        bar = QtWidgets.QFrame()
        bar.setFixedHeight(40)
        bar.setStyleSheet("background-color: #252525;")
        
        bar_layout = QtWidgets.QHBoxLayout(bar)
        bar_layout.setContentsMargins(15, 5, 15, 5)
        bar_layout.setSpacing(15)
        
        bar_layout.setContentsMargins(15, 5, 15, 5)
        bar_layout.setSpacing(15)
        
        # Search (Removed internal search input as we use the main window one)
        # We just keep the state for filtering
        self._external_search_text = ""
        
        # Status Filter (with labels)
        self.status_filter = QtWidgets.QComboBox()
        self.status_filter.addItems(["All", "Not Started", "In Progress", "Done"])
        self.status_filter.setStyleSheet("""
            QComboBox {
                background: transparent;
                color: #ccc;
                border: none;
                padding: 5px 8px;
            }
        """)
        self.status_filter.setFixedWidth(130)
        self.status_filter.currentIndexChanged.connect(self.apply_filters)
        bar_layout.addWidget(self.status_filter)
        
        # Favorites Only (using heart icon)
        self.fav_checkbox = QtWidgets.QCheckBox(" Favorites")
        if self.heart_icon:
            self.fav_checkbox.setIcon(self.heart_icon)
        self.fav_checkbox.setStyleSheet("color: #888;")
        self.fav_checkbox.stateChanged.connect(self.apply_filters)
        bar_layout.addWidget(self.fav_checkbox)

        self.recent_hip_btn = DoubleClickToolButton()
        self.recent_hip_btn.setVisible(False)
        self.recent_hip_btn.setAutoRaise(True)
        self.recent_hip_btn.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.recent_hip_btn.setCursor(QtCore.Qt.PointingHandCursor)
        self.recent_hip_btn.setMaximumWidth(220)
        self.recent_hip_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                color: #7f8b99;
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 3px 8px;
                font-size: 11px;
            }
            QToolButton:hover {
                background: #2b2b2b;
                color: #d6dde6;
                border-color: #333;
            }
        """)
        if self.houdini_icon:
            self.recent_hip_btn.setIcon(self.houdini_icon)
            self.recent_hip_btn.setIconSize(QtCore.QSize(14, 14))
        self.recent_hip_btn.double_clicked.connect(self.open_recent_hip)
        bar_layout.addWidget(self.recent_hip_btn)
        
        bar_layout.addStretch()
        
        # Sort (minimal)
        self.sort_combo = QtWidgets.QComboBox()
        self.sort_combo.addItems(["Recent", "A-Z"])
        self.sort_combo.setStyleSheet("""
            QComboBox {
                background: transparent;
                color: #888;
                border: none;
                padding: 5px 8px;
            }
        """)
        self.sort_combo.setFixedWidth(80)
        self.sort_combo.currentIndexChanged.connect(self.apply_filters)
        bar_layout.addWidget(self.sort_combo)
        
        parent_layout.addWidget(bar)
    
    def get_status_display(self, status):
        """Convert status code to display string."""
        status_map = {
            "not_started": "NOT STARTED",
            "in_progress": "IN PROGRESS",
            "done": "DONE"
        }
        return status_map.get(status, "NOT STARTED")
    
    def get_status_color(self, status):
        """Get background color for status badge."""
        color_map = {
            "not_started": "#8B0000",  # Dark red
            "in_progress": "#B8860B",  # Dark golden
            "done": "#228B22"           # Forest green
        }
        return color_map.get(status, "#8B0000")
    
    def refresh(self, projects):
        """Refresh the gallery with projects."""
        self.all_projects = projects
        self.apply_filters()

    def set_search_filter(self, text):
        """Called by parent window to update search."""
        self._external_search_text = text
        self.apply_filters()
    
    def apply_filters(self):
        """Apply search, status filter, and sorting."""
        self.table.clear()
        self.update_recent_hip_button()
        
        search_text = self._external_search_text.lower()
        status_filter = self.status_filter.currentIndex()
        fav_only = self.fav_checkbox.isChecked()
        sort_by = self.sort_combo.currentText()
        
        # Filter
        filtered = []
        for proj in self.all_projects:
            # Search filter (Name, Client, or Tags)
            if search_text:
                in_tags = any(search_text in t.lower() for t in getattr(proj, 'tags', []))
                if search_text not in proj.name.lower() and search_text not in proj.client.lower() and not in_tags:
                    continue
            
            # Status filter
            if status_filter == 1 and proj.status != "not_started":
                continue
            elif status_filter == 2 and proj.status != "in_progress":
                continue
            elif status_filter == 3 and proj.status != "done":
                continue
            
            # Favorites filter
            if fav_only and not proj.favorite:
                continue
            
            filtered.append(proj)
        
        # Sort
        if sort_by == "Recent":
            filtered.sort(key=lambda p: p.last_opened or "", reverse=True)
        elif sort_by == "A-Z":
            filtered.sort(key=lambda p: p.name.lower())
        
        # Display
        for proj in filtered:
            item = QtWidgets.QTreeWidgetItem(self.table)
            
            # Column 0: Color dot, favorite, or warning
            path_exists = os.path.exists(proj.path)
            proj_color = getattr(proj, 'color', '')
            
            if not path_exists:
                item.setIcon(0, self.table.style().standardIcon(QtWidgets.QStyle.SP_MessageBoxWarning))
                item.setToolTip(0, f"Path not found: {proj.path}")
            else:
                # Combine Color and Favorite status
                # Create a 16x16 pixmap
                pixmap = QtGui.QPixmap(16, 16)
                pixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(pixmap)
                painter.setRenderHint(QtGui.QPainter.Antialiasing)
                
                # Draw Color Circle if present
                if proj_color:
                    painter.setBrush(QtGui.QColor(proj_color))
                    painter.setPen(QtCore.Qt.NoPen)
                    painter.drawEllipse(2, 2, 12, 12)
                
                # Draw Heart if Favorite (Overlay or Standalone)
                if proj.favorite and self.heart_icon:
                    # If colored, draw heart smaller or overlay?
                    # Let's draw the heart icon. If user provided a "Clean Outline", it works on top of colors.
                    # We render the SVG icon into the pixmap
                    self.heart_icon.paint(painter, QtCore.QRect(0, 0, 16, 16))
                
                painter.end()
                
                # Only set icon if we drew something (color or favorite)
                if proj_color or proj.favorite:
                    item.setIcon(0, QtGui.QIcon(pixmap))
                
                if proj.favorite and not proj_color and not self.heart_icon:
                     # Fallback if no icon file but is favorite
                     item.setText(0, "❤️")
            
            # Name (with warning style if path missing)
            item.setText(1, proj.name)
            if not path_exists:
                item.setForeground(1, QtGui.QBrush(QtGui.QColor("#ff6666")))
            
            item.setText(2, proj.client)
            
            # Category
            category = getattr(proj, 'category', 'Personal')
            item.setText(3, category)
            
            # Status badge (column 4)
            status_text = self.get_status_display(proj.status)
            item.setText(4, status_text)
            item.setBackground(4, QtGui.QBrush(QtGui.QColor(self.get_status_color(proj.status))))
            item.setForeground(4, QtGui.QBrush(QtGui.QColor("#ffffff")))
            
            # Tags (column 5) - replaces custom metadata
            tags = getattr(proj, 'tags', [])
            if tags:
                tag_text = ", ".join(tags)
                if len(tag_text) > 35:
                    tag_text = tag_text[:35] + "..."
                item.setText(5, tag_text)
                item.setForeground(5, QtGui.QBrush(QtGui.QColor("#4a90e2"))) # Blueish for tags
            
            # Notes (column 6)
            notes_text = proj.notes[:40] + "..." if len(proj.notes) > 40 else proj.notes
            item.setText(6, notes_text)
            
            item.setData(0, QtCore.Qt.UserRole, proj)

    def normalize_path(self, path):
        if not path:
            return ""
        return os.path.normpath(path).replace("\\", "/")

    def is_path_inside_project(self, file_path, project_root):
        normalized_file = os.path.normcase(os.path.normpath(file_path))
        normalized_root = os.path.normcase(os.path.normpath(project_root))

        try:
            return os.path.commonpath([normalized_file, normalized_root]) == normalized_root
        except ValueError:
            return False

    def format_relative_time(self, value):
        from datetime import datetime

        try:
            last_opened = datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return value or "recent"

        delta = datetime.now() - last_opened
        seconds = max(int(delta.total_seconds()), 0)
        minutes = seconds // 60
        hours = minutes // 60
        days = delta.days

        if seconds < 60:
            return "just now"
        if minutes < 60:
            return f"{minutes} min ago"
        if hours < 24:
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        if days == 1:
            return "yesterday"
        if days < 7:
            return f"{days} days ago"
        return last_opened.strftime("%Y-%m-%d")

    def get_recent_hip_candidate(self):
        projects_by_recent = [
            project for project in self.all_projects
            if getattr(project, "last_opened", "")
        ]
        projects_by_recent.sort(key=lambda project: getattr(project, "last_opened", ""), reverse=True)

        for project in projects_by_recent:
            hip_path = self.normalize_path(getattr(project, "custom_fields", {}).get("_last_hip_path", ""))
            if hip_path and os.path.isfile(hip_path) and self.is_path_inside_project(hip_path, project.path):
                return project, hip_path

            latest_hip = self.find_latest_hip_in_project(project.path)
            if latest_hip:
                return project, latest_hip

        return None, ""

    def find_latest_hip_in_project(self, project_root):
        normalized_root = self.normalize_path(project_root)
        if not normalized_root or not os.path.isdir(normalized_root):
            return ""

        latest_path = ""
        latest_mtime = -1
        hip_extensions = {".hip", ".hipnc", ".hiplc"}

        for root, dirs, files in os.walk(normalized_root):
            dirs[:] = [d for d in dirs if not d.startswith(".") and d != "__pycache__"]
            for file_name in files:
                ext = os.path.splitext(file_name)[1].lower()
                if ext not in hip_extensions:
                    continue

                full_path = self.normalize_path(os.path.join(root, file_name))
                try:
                    modified = os.path.getmtime(full_path)
                except OSError:
                    continue

                if modified > latest_mtime:
                    latest_mtime = modified
                    latest_path = full_path

        return latest_path

    def update_recent_hip_button(self):
        project, hip_path = self.get_recent_hip_candidate()
        self.recent_hip_project = project
        self.recent_hip_path = hip_path

        if not project or not hip_path:
            self.recent_hip_btn.hide()
            self.recent_hip_btn.setToolTip("")
            return

        file_name = os.path.basename(hip_path)
        text_width = max(self.recent_hip_btn.maximumWidth() - 42, 80)
        button_text = self.recent_hip_btn.fontMetrics().elidedText(
            file_name,
            QtCore.Qt.ElideRight,
            text_width
        )
        relative_time = self.format_relative_time(project.last_opened)
        self.recent_hip_btn.setText(button_text)
        self.recent_hip_btn.setToolTip(
            f"{project.name}\n{hip_path}\nLast opened {relative_time}\nDouble-click to resume"
        )
        self.recent_hip_btn.show()

    def open_recent_hip(self):
        if self.recent_hip_project and self.recent_hip_path:
            self.recent_hip_requested.emit(self.recent_hip_project, self.recent_hip_path)
    
    def show_context_menu(self, position):
        selected_items = self.table.selectedItems()
        if not selected_items:
            return
        
        # Get all selected projects
        selected_projects = [item.data(0, QtCore.Qt.UserRole) for item in selected_items]
        is_multi = len(selected_projects) > 1
        project = selected_projects[0]  # For single-item actions
        
        menu = QtWidgets.QMenu()
        
        if is_multi:
            # Multi-select menu
            menu.addAction(f"{len(selected_projects)} projects selected").setEnabled(False)
            menu.addSeparator()
            remove_action = menu.addAction(f"Remove {len(selected_projects)} Projects")
            open_action = edit_action = fav_action = None
        else:
            # Single-select menu
            open_action = menu.addAction("Open Project")
            edit_action = menu.addAction("Edit Details...")
            menu.addSeparator()
            
            fav_text = "Unfavorite" if project.favorite else "Favorite"
            if self.heart_icon:
                fav_action = menu.addAction(self.heart_icon, fav_text)
            else:
                fav_action = menu.addAction(fav_text)
                
            menu.addSeparator()
            remove_action = menu.addAction("Remove Project")
        
        action = menu.exec_(self.table.viewport().mapToGlobal(position))
        
        if action == open_action and open_action:
            self.project_clicked.emit(project)
        elif action == edit_action and edit_action:
            self.edit_project(project)
        elif action == fav_action and fav_action:
            project.favorite = not project.favorite
            self.project_updated.emit(project)
            self.apply_filters()
        elif action == remove_action:
            # Remove all selected projects
            for proj in selected_projects:
                self.project_removed.emit(proj)
    
    def edit_project(self, project):
        """Open edit dialog for project details."""
        dialog = EditProjectDialog(project, self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.project_updated.emit(project)
            self.apply_filters()
    
    def handle_click(self, item, column):
        project = item.data(0, QtCore.Qt.UserRole)
        if project:
            self.project_clicked.emit(project)

    def set_view_mode(self, mode):
        # Keep for compatibility, but we only use list view now
        pass


class EditProjectDialog(QtWidgets.QDialog):
    """Dialog to edit project details."""
    
    # Preset colors for quick selection
    COLOR_PRESETS = ["#ff5555", "#ff9944", "#ffdd44", "#77dd77", "#55aaff", "#aa77ff", "#ff77aa", ""]
    
    def __init__(self, project, parent=None):
        super(EditProjectDialog, self).__init__(parent)
        self.project = project
        self.current_color = getattr(project, 'color', '')
        
        self.setWindowTitle(f"Edit: {project.name}")
        self.resize(420, 450) # Use resize instead of fixed size to allow growth
        self.setMinimumWidth(400)
        self.setStyleSheet("""
            QDialog { background: #1e1e1e; color: #ddd; }
            QLabel { color: #888; font-size: 11px; background: transparent; }
            QLineEdit, QTextEdit, QComboBox {
                background: #252525;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
                color: #ddd;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #3d5a80;
                background: #2a2a2a;
            }
        """)
        
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Form layout for fields
        form = QtWidgets.QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(QtCore.Qt.AlignRight)
        
        # Client
        self.client_input = QtWidgets.QLineEdit(project.client)
        form.addRow("Client:", self.client_input)
        
        # Status (text-based, no emoji)
        self.status_combo = QtWidgets.QComboBox()
        self.status_combo.addItems(["Not Started", "In Progress", "Done"])
        status_map = {"not_started": 0, "in_progress": 1, "done": 2}
        self.status_combo.setCurrentIndex(status_map.get(project.status, 0))
        form.addRow("Status:", self.status_combo)
        
        # Color swatches
        color_widget = QtWidgets.QWidget()
        color_layout = QtWidgets.QHBoxLayout(color_widget)
        # Add margins to prevent top clipping
        color_layout.setContentsMargins(0, 4, 0, 4)
        color_layout.setSpacing(6)
        
        self.color_buttons = []
        for color in self.COLOR_PRESETS:
            btn = QtWidgets.QPushButton()
            btn.setFixedSize(24, 24)
            if color:
                btn.setStyleSheet(f"""
                    QPushButton {{ background: {color}; border: 2px solid transparent; border-radius: 4px; }}
                    QPushButton:hover {{ border-color: #fff; }}
                """)
            else:
                btn.setText("×")
                btn.setStyleSheet("""
                    QPushButton { background: #333; color: #666; border: 2px solid transparent; border-radius: 4px; }
                    QPushButton:hover { border-color: #666; }
                """)
            # Fix: Use *x to ignore any arguments (checked or not) sent by the signal
            btn.clicked.connect(lambda *x, c=color: self.set_color(c))
            self.color_buttons.append((btn, color))
            color_layout.addWidget(btn)
        
        # Custom color picker
        custom_btn = QtWidgets.QPushButton("...")
        custom_btn.setFixedSize(24, 24)
        custom_btn.setStyleSheet("background: #333; color: #888; border-radius: 4px;")
        custom_btn.clicked.connect(self.pick_custom_color)
        color_layout.addWidget(custom_btn)
        color_layout.addStretch()
        
        form.addRow("Color:", color_widget)
        self.update_color_selection()
        
        layout.addLayout(form)
        
        # Notes
        notes_label = QtWidgets.QLabel("Notes:")
        notes_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")
        layout.addWidget(notes_label)
        
        self.notes_input = QtWidgets.QTextEdit()
        self.notes_input.setText(project.notes)
        self.notes_input.setMaximumHeight(80)
        layout.addWidget(self.notes_input)
        
        # Tags Section
        tags_label = QtWidgets.QLabel("Tags (comma separated):")
        tags_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 10px; background: transparent;")
        layout.addWidget(tags_label)
        
        current_tags = getattr(project, 'tags', [])
        tags_str = ", ".join(current_tags)
        self.tags_input = QtWidgets.QLineEdit(tags_str)
        self.tags_input.setPlaceholderText("e.g. vfx, character, urgent")
        layout.addWidget(self.tags_input)
        
        layout.addStretch()
        
        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.setSpacing(10)
        
        cancel_btn = QtWidgets.QPushButton("Cancel")
        cancel_btn.setStyleSheet("background: #333; color: #888; padding: 10px 20px; border: none; border-radius: 4px;")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QtWidgets.QPushButton("Save")
        save_btn.setStyleSheet("background: #3d5a80; color: #fff; padding: 10px 24px; border: none; border-radius: 4px; font-weight: bold;")
        save_btn.clicked.connect(self.save_and_close)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)
    
    def set_color(self, color):
        self.current_color = color
        self.update_color_selection()
    
    def update_color_selection(self):
        for btn, color in self.color_buttons:
            if color == self.current_color:
                if color:
                    btn.setStyleSheet(f"background: {color}; border: 2px solid #fff; border-radius: 4px;")
                else:
                    btn.setStyleSheet("background: #333; color: #fff; border: 2px solid #fff; border-radius: 4px;")
            else:
                if color:
                    btn.setStyleSheet(f"background: {color}; border: 2px solid transparent; border-radius: 4px;")
                else:
                    btn.setStyleSheet("background: #333; color: #666; border: 2px solid transparent; border-radius: 4px;")
    
    def pick_custom_color(self):
        color = QtWidgets.QColorDialog.getColor(
            QtGui.QColor(self.current_color) if self.current_color else QtGui.QColor("#ff5500"),
            self, "Pick Project Color"
        )
        if color.isValid():
            self.current_color = color.name()
            self.update_color_selection()
    
    def save_and_close(self):
        self.project.client = self.client_input.text()
        status_map = {0: "not_started", 1: "in_progress", 2: "done"}
        self.project.status = status_map.get(self.status_combo.currentIndex(), "not_started")
        self.project.notes = self.notes_input.toPlainText()
        self.project.color = self.current_color
        
        self.project.notes = self.notes_input.toPlainText()
        self.project.color = self.current_color
        
        # Save Tags
        raw_tags = self.tags_input.text().split(",")
        clean_tags = [t.strip() for t in raw_tags if t.strip()]
        self.project.tags = clean_tags
        
        # Preserve internal custom fields if any (though UI doesn't touch them now)
        # We don't need to rebuild custom_fields since we didn't touch them
        
        self.accept()



