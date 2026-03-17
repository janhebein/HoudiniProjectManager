from hutil.Qt import QtWidgets, QtCore, QtGui
import os
import re

class SortableTreeWidgetItem(QtWidgets.QTreeWidgetItem):
    def __lt__(self, other):
        column = self.treeWidget().sortColumn()
        
        # Helper to strip non-alphanumeric chars (like UI list markers) specifically for the Name column
        def clean_val(val):
            if val is None: return ""
            # Remove structural chars but leave actual names intact
            return re.sub(r'^[▼└●\s]+', '', val).lower()

        text1 = self.text(column)
        text2 = other.text(column)

        if column == 0:  # Name
            return clean_val(text1) < clean_val(text2)
        elif column == 1:  # Date
            return text1 < text2
        elif column == 2:  # Ver
            # Extract just numeric value if possible
            v1_match = re.search(r'\d+', text1)
            v2_match = re.search(r'\d+', text2)
            if v1_match and v2_match:
                return int(v1_match.group()) < int(v2_match.group())
            return text1 < text2
            
        return text1 < text2


def iter_tree_items(tree_widget):
    """Safe python generator to replace C++ QTreeWidgetItemIterator which causes segfaults."""
    def traverse(parent):
        for i in range(parent.childCount()):
            child = parent.child(i)
            yield child
            yield from traverse(child)
    yield from traverse(tree_widget.invisibleRootItem())


# Path to Houdini icon
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOUDINI_ICON_PATH = os.path.join(SCRIPT_DIR, "icons", "Houdini3D_icon.jpg")

class DashboardView(QtWidgets.QWidget):
    back_clicked = QtCore.Signal()
    current_hip_changed = QtCore.Signal(str)

    def __init__(self):
        super(DashboardView, self).__init__()
        self.project_path = None
        self.current_folder = None  # Track current folder for Explorer

        # Load Houdini icon
        if os.path.exists(HOUDINI_ICON_PATH):
            self.houdini_icon = QtGui.QIcon(HOUDINI_ICON_PATH)
        else:
            self.houdini_icon = None

        # File system watcher for live updates
        self.file_watcher = QtCore.QFileSystemWatcher()
        self.file_watcher.directoryChanged.connect(self.on_directory_changed)
        self.watched_folders = set()

        # Main Layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.setSpacing(0)
        
        # Top Bar
        self.setup_top_bar(layout)
        
        # Content Area: Splitter
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.setStyleSheet("""
            QSplitter::handle { background: #333; width: 2px; }
        """)
        
        # Left: Folder Tree with Toolbar
        left_container = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_container)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_container.setStyleSheet("background-color: #252525;")
        
        # --- Tree Toolbar ---
        tree_toolbar = QtWidgets.QWidget()
        tree_toolbar.setFixedHeight(30)
        tree_toolbar.setStyleSheet("border-bottom: 1px solid #333; background-color: #222;")
        tree_tb_layout = QtWidgets.QHBoxLayout(tree_toolbar)
        tree_tb_layout.setContentsMargins(5, 0, 5, 0)
        
        # Expand Hips Button
        self.expand_hips_btn = QtWidgets.QPushButton(" Show Hips")
        self.expand_hips_btn.setToolTip("Expand all folders containing HIP files")
        if self.houdini_icon:
             self.expand_hips_btn.setIcon(self.houdini_icon)
             self.expand_hips_btn.setIconSize(QtCore.QSize(14, 14))
        
        self.expand_hips_btn.setStyleSheet("""
            QPushButton { 
                border: 1px solid #333; 
                border-radius: 3px;
                background: #2a2a2a; 
                color: #bbb;
                padding: 2px 8px;
                font-size: 10px;
            }
            QPushButton:hover { background: #333; color: #fff; border-color: #555; }
        """)
        
        tree_tb_layout.addWidget(self.expand_hips_btn)
        
        # Collapse All Button
        self.collapse_all_btn = QtWidgets.QPushButton(" Collapse All")
        self.collapse_all_btn.setToolTip("Collapse all folders")
        
        self.collapse_all_btn.setStyleSheet("""
            QPushButton { 
                border: 1px solid #333; 
                border-radius: 3px;
                background: #2a2a2a; 
                color: #bbb;
                padding: 2px 8px;
                font-size: 10px;
            }
            QPushButton:hover { background: #333; color: #fff; border-color: #555; }
        """)
        
        tree_tb_layout.addWidget(self.collapse_all_btn)
        
        # Refresh Tree Button
        self.refresh_tree_btn = QtWidgets.QPushButton(" Refresh")
        self.refresh_tree_btn.setToolTip("Refresh folder tree")
        # Use standard refresh/reload icon
        refresh_icon = QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload)
        self.refresh_tree_btn.setIcon(refresh_icon)
        self.refresh_tree_btn.setIconSize(QtCore.QSize(14, 14))
        
        self.refresh_tree_btn.setStyleSheet("""
            QPushButton { 
                border: 1px solid #333; 
                border-radius: 3px;
                background: #2a2a2a; 
                color: #bbb;
                padding: 2px 8px;
                font-size: 10px;
            }
            QPushButton:hover { background: #333; color: #fff; border-color: #555; }
        """)
        
        tree_tb_layout.addWidget(self.refresh_tree_btn)
        
        combo_style = """
            QComboBox {
                background: #2a2a2a;
                color: #bbb;
                border: 1px solid #333;
                border-radius: 3px;
                padding: 2px 8px;
                font-size: 10px;
            }
            QComboBox:hover {
                background: #333;
                color: #fff;
                border-color: #555;
            }
            QComboBox::drop-down {
                border: none;
                width: 16px;
            }
        """

        self.tree_sort_mode_combo = QtWidgets.QComboBox()
        self.tree_sort_mode_combo.addItems(["A-Z", "Date"])
        self.tree_sort_mode_combo.setToolTip("Sort tree by alphabetic order or modified date")
        self.tree_sort_mode_combo.setFixedWidth(64)
        self.tree_sort_mode_combo.setStyleSheet(combo_style)
        tree_tb_layout.addWidget(self.tree_sort_mode_combo)

        self.tree_sort_order_combo = QtWidgets.QComboBox()
        self.tree_sort_order_combo.addItems(["Asc", "Desc"])
        self.tree_sort_order_combo.setToolTip("Toggle ascending or descending order")
        self.tree_sort_order_combo.setFixedWidth(64)
        self.tree_sort_order_combo.setStyleSheet(combo_style)
        tree_tb_layout.addWidget(self.tree_sort_order_combo)

        tree_tb_layout.addStretch() 
        
        left_layout.addWidget(tree_toolbar)
        
        # Tree Widget
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMinimumWidth(250)
        self.tree.setStyleSheet("""
            QTreeWidget {
                background-color: #252525;
                border: none;
                color: #ccc;
                font-size: 11px;
            }
            QTreeWidget::item {
                padding: 6px 4px;
            }
            QTreeWidget::item:selected {
                background-color: #3d5a80;
                color: #fff;
            }
            QTreeWidget::item:hover {
                background-color: #2a2a2a;
            }
        """)
        self.tree.itemClicked.connect(self.on_tree_click)
        self.tree.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_tree_context_menu)
        
        # Connect toolbar button signals now that tree exists
        self.expand_hips_btn.clicked.connect(self.expand_all_hip_folders)
        self.collapse_all_btn.clicked.connect(self.tree.collapseAll)
        self.refresh_tree_btn.clicked.connect(self.refresh_tree)
        self.tree_sort_mode_combo.currentIndexChanged.connect(self.refresh_tree)
        self.tree_sort_order_combo.currentIndexChanged.connect(self.refresh_tree)
        
        left_layout.addWidget(self.tree)
        
        splitter.addWidget(left_container)
        
        # Right: Content Area
        right_container = QtWidgets.QWidget()
        right_layout = QtWidgets.QVBoxLayout(right_container)
        right_layout.setContentsMargins(15, 15, 15, 15)
        right_container.setStyleSheet("background-color: #1e1e1e;")
        
        # Current Path Label
        self.path_label = QtWidgets.QLabel("Select a folder")
        self.path_label.setStyleSheet("color: #888; font-size: 10px; margin-bottom: 10px;")
        right_layout.addWidget(self.path_label)
        
        # Header
        self.header_label = QtWidgets.QLabel("Project Dashboard")
        self.header_label.setStyleSheet("font-size: 20px; font-weight: bold; color: #fff; margin-bottom: 10px;")
        right_layout.addWidget(self.header_label)
        
        # File Table (Tree Widget for columns)
        self.file_table = QtWidgets.QTreeWidget()
        self.file_table.setHeaderLabels(["Name", "Date", "Ver", "Notes"])
        self.file_table.setColumnWidth(0, 280)
        self.file_table.setColumnWidth(1, 130)
        self.file_table.setColumnWidth(2, 50)
        self.file_table.setColumnWidth(3, 250)
        self.file_table.setAlternatingRowColors(False)
        self.file_table.setRootIsDecorated(True)
        self.file_table.setIndentation(20)
        self.file_table.setUniformRowHeights(True)
        self.file_table.itemDoubleClicked.connect(self.open_file_from_table)
        self.file_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.file_table.customContextMenuRequested.connect(self.show_file_context_menu)
        self.file_table.setSortingEnabled(True)
        self.file_table.sortByColumn(1, QtCore.Qt.DescendingOrder)
        self.file_table.setStyleSheet("""
            QTreeWidget { 
                background: #1a1a1a; 
                border: none; 
                outline: none;
                color: #ddd;
                font-size: 11px;
            }
            QTreeWidget::item { 
                padding: 8px 10px;
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
                font-size: 10px;
                font-weight: bold;
                text-transform: uppercase;
            }
        """)
        right_layout.addWidget(self.file_table)
        
        splitter.addWidget(right_container)
        splitter.setSizes([250, 600])
        
        layout.addWidget(splitter)

    def setup_top_bar(self, parent_layout):
        top_bar = QtWidgets.QFrame()
        top_bar.setFixedHeight(50)
        top_bar.setStyleSheet("background-color: #252525; border-bottom: 1px solid #111;")
        
        bar_layout = QtWidgets.QHBoxLayout(top_bar)
        bar_layout.setContentsMargins(15, 0, 15, 0)
        
        # Back Button
        self.back_btn = QtWidgets.QPushButton("← Back")
        self.back_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                font-weight: bold;
                border: none;
                padding: 8px 12px;
            }
            QPushButton:hover { color: #fff; }
        """)
        self.back_btn.clicked.connect(self.back_clicked.emit)
        bar_layout.addWidget(self.back_btn)
        
        # Environment Info Widget
        env_widget = QtWidgets.QWidget()
        env_widget.setStyleSheet("background: transparent;")
        env_layout = QtWidgets.QHBoxLayout(env_widget)
        env_layout.setContentsMargins(20, 0, 0, 0)
        env_layout.setSpacing(20)
        
        # Icon paths
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")
        save_icon_path = os.path.join(icons_dir, "save.svg")
        version_icon_path = os.path.join(icons_dir, "version.svg")
        copy_icon_path = os.path.join(icons_dir, "copy.svg")
        
        # Style for labels and values
        label_style = "color: #555; font-weight: bold; font-size: 10px; font-family: Segoe UI, sans-serif; padding-top: 1px;"
        path_style = "color: #999; font-size: 11px; font-family: Consolas, monospace; background: transparent; border: none;"
        
        # Shared button style
        copy_btn_style = """
            QPushButton { 
                border: none; 
                background: transparent; 
                padding: 0px;
            }
            QPushButton:hover { background: #333; border-radius: 2px; }
        """
        
        # JOB Label
        job_layout = QtWidgets.QHBoxLayout()
        job_layout.setSpacing(4) # Tighter spacing
        
        job_label = QtWidgets.QLabel("JOB")
        job_label.setStyleSheet(label_style)
        
        # Minimal copy button (Now on Left)
        copy_job_btn = QtWidgets.QPushButton("")
        copy_job_btn.setFixedSize(20, 20)
        copy_job_btn.setToolTip("Copy JOB Path")
        if os.path.exists(copy_icon_path):
            copy_job_btn.setIcon(QtGui.QIcon(copy_icon_path))
            copy_job_btn.setIconSize(QtCore.QSize(14, 14))
        else:
            copy_job_btn.setText("❐")
            
        copy_job_btn.setStyleSheet(copy_btn_style)
        copy_job_btn.clicked.connect(self.copy_job_path)
        
        self.job_path_input = QtWidgets.QLineEdit("...")
        self.job_path_input.setReadOnly(True)
        self.job_path_input.setFixedWidth(250)
        self.job_path_input.setStyleSheet(path_style)
        self.job_path_input.setCursorPosition(0)
        
        # Order: Label -> Icon -> Text
        job_layout.addWidget(job_label)
        job_layout.addWidget(copy_job_btn)
        job_layout.addWidget(self.job_path_input)
        env_layout.addLayout(job_layout)
        
        # HIP Label
        hip_layout = QtWidgets.QHBoxLayout()
        hip_layout.setSpacing(4)
        
        hip_label = QtWidgets.QLabel("HIP")
        hip_label.setStyleSheet(label_style)
        
        copy_hip_btn = QtWidgets.QPushButton("")
        copy_hip_btn.setFixedSize(20, 20)
        copy_hip_btn.setToolTip("Copy HIP Path")
        if os.path.exists(copy_icon_path):
            copy_hip_btn.setIcon(QtGui.QIcon(copy_icon_path))
            copy_hip_btn.setIconSize(QtCore.QSize(14, 14))
        else:
            copy_hip_btn.setText("❐")
            
        copy_hip_btn.setStyleSheet(copy_btn_style)
        copy_hip_btn.clicked.connect(self.copy_hip_path)

        self.hip_path_input = QtWidgets.QLineEdit("...")
        self.hip_path_input.setReadOnly(True)
        self.hip_path_input.setFixedWidth(250)
        self.hip_path_input.setStyleSheet(path_style)
        self.hip_path_input.setCursorPosition(0)
        
        # Expand Hips Button (More visible with label)
        self.expand_hips_btn = QtWidgets.QPushButton(" Show Hips")
        self.expand_hips_btn.setToolTip("Expand all folders containing HIP files")
        if self.houdini_icon:
             self.expand_hips_btn.setIcon(self.houdini_icon)
             self.expand_hips_btn.setIconSize(QtCore.QSize(14, 14))
        
        # Make it look clean/minimal but clickable
        self.expand_hips_btn.setStyleSheet("""
            QPushButton { 
                border: 1px solid #444; 
                border-radius: 3px;
                background: #2a2a2a; 
                color: #bbb;
                padding: 2px 8px;
                font-size: 10px;
                margin-left: 10px;
            }
            QPushButton:hover { background: #333; color: #fff; border-color: #666; }
        """)
        self.expand_hips_btn.clicked.connect(self.expand_all_hip_folders)
        
        # Order: Label -> Icon -> Text
        hip_layout.addWidget(hip_label)
        hip_layout.addWidget(copy_hip_btn)
        hip_layout.addWidget(self.hip_path_input)
        env_layout.addLayout(hip_layout)
        
        bar_layout.addWidget(env_widget)
        
        bar_layout.addStretch()
        
        # Icon paths
        icons_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "icons")
        save_icon_path = os.path.join(icons_dir, "save.svg")
        version_icon_path = os.path.join(icons_dir, "version.svg")
        
        # Save Hip Here Button
        self.save_btn = QtWidgets.QPushButton(" Save")
        if os.path.exists(save_icon_path):
            self.save_btn.setIcon(QtGui.QIcon(save_icon_path))
        self.save_btn.setStyleSheet("""
            QPushButton {
                background: #3d5a80;
                color: #fff;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #4a6d94; }
        """)
        self.save_btn.clicked.connect(self.save_hip_here)
        bar_layout.addWidget(self.save_btn)
        
        # Version Up Button
        self.version_btn = QtWidgets.QPushButton(" Version Up")
        if os.path.exists(version_icon_path):
            self.version_btn.setIcon(QtGui.QIcon(version_icon_path))
        self.version_btn.setStyleSheet("""
            QPushButton {
                background: #50c878;
                color: #111;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #5fd88a; }
        """)
        self.version_btn.clicked.connect(self.save_next_version)
        bar_layout.addWidget(self.version_btn)
        
        parent_layout.addWidget(top_bar)

    def copy_job_path(self):
        job = self.job_path_input.text()
        if job and job != "...":
            QtWidgets.QApplication.clipboard().setText(job)
            
    def copy_hip_path(self):
        hip = self.hip_path_input.text()
        if hip and hip != "...":
            QtWidgets.QApplication.clipboard().setText(hip)

    def _normalize_path(self, path):
        if not path:
            return None
        return os.path.normpath(path).replace("\\", "/")

    def _resolve_folder_path(self, path):
        normalized = self._normalize_path(path)
        if not normalized:
            return None
        if os.path.isfile(normalized):
            return self._normalize_path(os.path.dirname(normalized))
        return normalized

    def _get_tree_sort_mode(self):
        if not hasattr(self, "tree_sort_mode_combo"):
            return "name"
        return "date" if self.tree_sort_mode_combo.currentText() == "Date" else "name"

    def _is_tree_sort_descending(self):
        if not hasattr(self, "tree_sort_order_combo"):
            return False
        return self.tree_sort_order_combo.currentText() == "Desc"

    def _get_tree_entries(self, path):
        entries = list(os.scandir(path))
        sort_mode = self._get_tree_sort_mode()
        reverse = self._is_tree_sort_descending()

        def sort_key(entry):
            if sort_mode == "date":
                try:
                    return entry.stat().st_mtime
                except OSError:
                    return 0
            return entry.name.lower()

        directories = [entry for entry in entries if entry.is_dir()]
        files = [entry for entry in entries if not entry.is_dir()]
        directories.sort(key=sort_key, reverse=reverse)
        files.sort(key=sort_key, reverse=reverse)
        return directories + files

    def load_project(self, project_data):
        import hou
        # Normalize immediately to prevent mixed slashes globally
        self.project_path = hou.text.expandString(project_data.path)
        self.project_path = os.path.normpath(self.project_path).replace("\\", "/")
        self.current_folder = self.project_path  # Default to project root

        # Update Environment Header
        self.job_path_input.setText(self.project_path)
        self.job_path_input.setCursorPosition(0)
        self.hip_path_input.setText("...")

        self.tree.clear()
        self.file_table.clear()
        self.header_label.setText(f"{project_data.name}")

        if not os.path.exists(self.project_path):
            self.header_label.setText(f"Path Not Found: {self.project_path}")
            return

        # Clear old file watcher paths
        if self.watched_folders:
            self.file_watcher.removePaths(list(self.watched_folders))
            self.watched_folders.clear()

        # Set up the tree properly
        self.refresh_tree()

        # Watch all folders for live hip file detection
        self.setup_folder_watching(self.project_path)
        
        # Auto-navigate to active context
        self.expand_to_active_context()
    def build_tree(self, path, parent_item, depth=0):
        if depth > 10:  # Increased depth limit for deep pipelines
            return
            
        if not os.path.exists(path):
            return

        try:
            entries = self._get_tree_entries(path)
            for entry in entries:
                if entry.name.startswith("."):
                    continue
                if entry.is_dir():
                    item = QtWidgets.QTreeWidgetItem(parent_item)
                    item.setText(0, entry.name)
                    item.setData(0, QtCore.Qt.UserRole, entry.path)
                    
                    # Heuristic: Check if this is a "Work Area" (contains standard subfolders)
                    is_work_area = False
                    try:
                        subs = [e.name for e in os.scandir(entry.path) if e.is_dir()]
                        # If it has at least 2 common pipeline folders, treat as work area
                        common_folders = {'geo', 'render', 'tex', 'sim', 'cache', 'comp'}
                        if len(set(subs) & common_folders) >= 2:
                            is_work_area = True
                    except:
                        pass

                    # Check if this folder contains hip files or is named 'hip'
                    has_hips = entry.name.lower() == 'hip' or self.folder_has_hip_files(entry.path)
                    
                    if has_hips:
                        item.setForeground(0, QtGui.QColor("#ff7b00"))  # Orange for hip folders
                        if self.houdini_icon:
                            # Composite icon: Folder + Mini Houdini
                            item.setIcon(0, self.get_badged_icon(self.houdini_icon))
                    elif is_work_area:
                        # It's a work area but empty of hips - giving it a hint color
                        item.setForeground(0, QtGui.QColor("#ffcc00")) # Yellow-ish
                        item.setText(0, f"{entry.name}  [WORK AREA]")
                    
                    self.build_tree(entry.path, item, depth + 1)
                else:
                    # It's a file
                    item = QtWidgets.QTreeWidgetItem(parent_item)
                    item.setText(0, entry.name)
                    item.setData(0, QtCore.Qt.UserRole, entry.path)
                    if entry.name.endswith('.hip') or entry.name.endswith('.hipnc'):
                        item.setForeground(0, QtGui.QColor("#ffaa00"))
                        if self.houdini_icon:
                            item.setIcon(0, self.houdini_icon)
        except PermissionError:
            pass
            
    def get_badged_icon(self, badge_icon):
        """Create a folder icon with a small badge overlay."""
        # Get standard directory icon
        base_icon = self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon)
        base_pixmap = base_icon.pixmap(32, 32) # Work at 32x32 for quality
        
        # Create painter
        painter = QtGui.QPainter(base_pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        
        # Draw badge (Houdini icon) in bottom-right corner
        # Scale to 14x14 approximately
        if badge_icon:
            badge_pixmap = badge_icon.pixmap(14, 14)
            # Position: x=14, y=14 (for 32x32, we want it at bottom right, say x=18, y=18)
            # Let's try bottom right
            target_rect = QtCore.QRect(16, 16, 16, 16)
            badge_icon.paint(painter, target_rect)
            
        painter.end()
        return QtGui.QIcon(base_pixmap)
    
    def folder_has_hip_files(self, folder_path):
        """Check if a folder directly contains any hip files."""
        try:
            for entry in os.scandir(folder_path):
                if entry.is_file():
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext in ['.hip', '.hipnc', '.hiplc']:
                        return True
        except:
            pass
        return False

    def open_selected_in_explorer(self):
        """Open the currently selected folder in Windows Explorer."""
        import subprocess
        current = self.tree.currentItem()
        if current:
            path = current.data(0, QtCore.Qt.UserRole)
            if path and os.path.exists(path):
                # Open in Explorer and select the folder
                subprocess.Popen(f'explorer /select,"{path}"')
        else:
            # No selection, open project root
            if self.project_path and os.path.exists(self.project_path):
                subprocess.Popen(f'explorer "{self.project_path}"')
    
    def refresh_tree(self):
        """Refresh the folder tree structure."""
        if not self.project_path:
            return
            
        # Store current selection
        current = self.tree.currentItem()
        selected_path = None
        if current:
            selected_path = current.data(0, QtCore.Qt.UserRole)
        
        # Disable file watcher temporarily to prevent race conditions during rebuild
        was_watching = False
        if hasattr(self, 'file_watcher'):
            was_watching = True
            self.file_watcher.blockSignals(True)
        
        # Rebuild tree
        self.tree.clear()
        
        # Explicitly add the root item so it doesn't get lost in Qt's widget hierarchy during fast rebuilds
        root_item = QtWidgets.QTreeWidgetItem()
        root_item.setText(0, os.path.basename(self.project_path))
        root_item.setData(0, QtCore.Qt.UserRole, self.project_path)
        root_item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
        
        self.tree.addTopLevelItem(root_item)
        root_item.setExpanded(True)
        
        self.build_tree(self.project_path, root_item)
        
        # Try to restore selection
        if selected_path:
            for item in iter_tree_items(self.tree):
                if item.data(0, QtCore.Qt.UserRole) == selected_path:
                    self.tree.setCurrentItem(item)
                    break
        
        # Re-enable file watcher
        if was_watching:
            self.file_watcher.blockSignals(False)

    def expand_all_hip_folders(self):
        """Expand all tree items that contain hip files."""
        self.tree.collapseAll()
        
        for item in iter_tree_items(self.tree):
            path = item.data(0, QtCore.Qt.UserRole)
            if path:
                # Check if it has hip files
                if self.folder_has_hip_files(path):
                    item.setExpanded(True)
                    # Ensure parents are expanded
                    parent = item.parent()
                    while parent:
                        parent.setExpanded(True)
                        parent = parent.parent()

    def expand_to_active_context(self):
        """Expand and select the folder matching the current HIP file context."""
        import hou
        try:
            current_hip_path = hou.hipFile.name()
            # Handle untitled/unsaved
            if "untitled" in current_hip_path.lower():
                current_dir = None
            else:
                current_dir = os.path.dirname(current_hip_path).replace("\\", "/")
        except:
            current_dir = None
            
        target_item = None
        hip_folder_item = None
        
        # Iterator to traverse the entire tree
        for item in iter_tree_items(self.tree):
            path = item.data(0, QtCore.Qt.UserRole)
            if path:
                # Normalize both for comparison
                path_clean = path.replace("\\", "/").lower()
                
                # Priority 1: Exact match (case-insensitive)
                if current_dir:
                     current_dir_clean = current_dir.lower()
                     if os.path.normpath(path_clean) == os.path.normpath(current_dir_clean):
                        target_item = item
                        break 
                
                # Priority 2: Folder named 'hip'
                if not hip_folder_item and item.text(0).lower() == "hip":
                    hip_folder_item = item
            
        # Decision
        final_target = target_item or hip_folder_item
        
        if final_target:
            self.tree.scrollToItem(final_target)
            self.tree.setCurrentItem(final_target)
            final_target.setExpanded(True)
            # Ensure parents are expanded
            parent = final_target.parent()
            while parent:
                parent.setExpanded(True)
                parent = parent.parent()
            
            # Trigger selection logic (load files)
            self.on_tree_click(final_target, 0)


    def update_tree_item_for_folder(self, folder_path):
        """Update the tree item icon/color for a folder after hip files change."""
        folder_path = folder_path.replace("\\", "/")

        # Find the tree item for this folder
        def find_item(parent_item, target_path):
            for i in range(parent_item.childCount()):
                child = parent_item.child(i)
                item_path = child.data(0, QtCore.Qt.UserRole)
                if item_path:
                    item_path = item_path.replace("\\", "/")
                    if item_path == target_path:
                        return child
                    # Check children
                    found = find_item(child, target_path)
                    if found:
                        return found
            return None

        item = find_item(self.tree.invisibleRootItem(), folder_path)
        if item:
            # Update icon based on whether folder now has hip files
            if self.folder_has_hip_files(folder_path):
                item.setForeground(0, QtGui.QColor("#ff7b00"))  # Orange
                if self.houdini_icon:
                    item.setIcon(0, self.get_badged_icon(self.houdini_icon))
                else:
                    item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
            else:
                # Check for heuristic work area to reset to yellow if needed?
                # For simplicity, if no files, check heuristic again or just reset to default/yellow
                # Since heuristic is cheap, let's just reset to default for now or check work area if I want to be 100% consistent
                # I'll stick to default restoration to keep it simple, or I'd need to duplicate the work area logic here.
                # Actually, let's keep it simple: if files gone, revert to simple folder.
                # Ideally we check 'is_work_area' again but let's assume gray for now unless requested.
                item.setForeground(0, QtGui.QColor("#ccc"))  # Default
                item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))

    def setup_folder_watching(self, root_path, depth=0):
        """Recursively add folders to the file watcher."""
        if depth > 10: # Match build_tree limit
            return

        try:
            # Add this folder to watcher
            self.file_watcher.addPath(root_path)
            self.watched_folders.add(root_path)

            # Recursively add subfolders
            for entry in os.scandir(root_path):
                if entry.is_dir() and not entry.name.startswith('.'):
                    self.setup_folder_watching(entry.path, depth + 1)
        except PermissionError:
            pass

    def on_directory_changed(self, path):
        """Called when a watched directory changes (file added/removed)."""
        # Update the tree item icon for this folder
        self.update_tree_item_for_folder(path)

        # Also refresh the file list if we're viewing this folder
        if self.current_folder and os.path.normpath(self.current_folder) == os.path.normpath(path):
            self.load_files_from(self.current_folder)

    def show_tree_context_menu(self, position):
        """Right-click menu for folder tree."""
        item = self.tree.itemAt(position)
        if not item:
            return
            
        path = item.data(0, QtCore.Qt.UserRole)
        if not path or os.path.isfile(path):
            return
            
        menu = QtWidgets.QMenu()
        
        # Create actions
        new_shot_action = menu.addAction("➕ New Shot Here")
        new_seq_action = menu.addAction("➕ New Sequence Here")
        new_folder_action = menu.addAction("📁 Create Subfolder...")
        menu.addSeparator()
        rename_action = menu.addAction("✏️ Rename...")
        menu.addSeparator()
        open_folder_action = menu.addAction("📂 Open in Explorer")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Delete Folder")
        
        action = menu.exec_(self.tree.viewport().mapToGlobal(position))
        
        if action == new_shot_action:
            self.create_new_shot(path)
        elif action == new_seq_action:
            self.create_new_sequence(path)
        elif action == new_folder_action:
            self.create_subfolder(item, path)
        elif action == rename_action:
            self.rename_folder(item, path)
        elif action == open_folder_action:
            os.startfile(path)
        elif action == delete_action:
            self.delete_folder(item, path)
    
    def create_new_shot(self, parent_path):
        """Create a new shot folder with standard subfolders."""
        name, ok = QtWidgets.QInputDialog.getText(
            self, "New Shot", "Shot name (e.g., shot_020):"
        )
        if not ok or not name:
            return
            
        shot_path = os.path.join(parent_path, name).replace("\\", "/")
        
        # Standard shot subfolders
        # Standard shot subfolders (updated to match "latest" structure: no hip folder, added playback)
        subfolders = ["render", "geo", "sim", "tex", "comp", "cache", "playback"]
        
        try:
            os.makedirs(shot_path, exist_ok=True)
            for sub in subfolders:
                os.makedirs(os.path.join(shot_path, sub).replace("\\", "/"), exist_ok=True)
            
            # Refresh tree
            self.refresh_tree()
            
            QtWidgets.QMessageBox.information(self, "Created", f"Shot '{name}' created with subfolders.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create shot:\n{e}")
    
    def create_new_sequence(self, parent_path):
        """Create a new sequence folder."""
        name, ok = QtWidgets.QInputDialog.getText(
            self, "New Sequence", "Sequence name (e.g., seq_020):"
        )
        if not ok or not name:
            return
            
        seq_path = os.path.join(parent_path, name).replace("\\", "/")
        
        try:
            os.makedirs(seq_path, exist_ok=True)
            
            # Refresh tree
            self.refresh_tree()
            
            QtWidgets.QMessageBox.information(self, "Created", f"Sequence '{name}' created.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create sequence:\n{e}")

    def create_subfolder(self, parent_item, parent_path):
        """Create a new subfolder."""
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Create Subfolder", "Folder name:"
        )
        if ok and name:
            new_path = os.path.join(parent_path, name).replace("\\", "/")
            try:
                os.makedirs(new_path, exist_ok=True)
                # Add to tree
                new_item = QtWidgets.QTreeWidgetItem(parent_item)
                new_item.setText(0, name)
                new_item.setData(0, QtCore.Qt.UserRole, new_path)
                new_item.setIcon(0, self.style().standardIcon(QtWidgets.QStyle.SP_DirIcon))
                parent_item.setExpanded(True)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not create folder: {e}")

    def rename_folder(self, item, path):
        """Rename a folder."""
        old_name = os.path.basename(path)
        new_name, ok = QtWidgets.QInputDialog.getText(
            self, "Rename Folder", "New name:", text=old_name
        )
        if ok and new_name and new_name != old_name:
            new_path = os.path.join(os.path.dirname(path), new_name).replace("\\", "/")
            
            # Remove from watcher temporarily to avoid Access Denied on Windows
            if path in self.watched_folders:
                self.file_watcher.removePath(path)
                self.watched_folders.discard(path)
                
            try:
                os.rename(path, new_path)
                item.setText(0, new_name)
                item.setData(0, QtCore.Qt.UserRole, new_path)
                
                # Re-add to watcher
                self.setup_folder_watching(new_path)
                
            except Exception as e:
                # Try to re-add old path if failed
                self.setup_folder_watching(path)
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not rename:\n{e}\n\nCheck if files are open.")

    def delete_folder(self, item, path):
        """Delete a folder after confirmation."""
        folder_name = os.path.basename(path)
        res = QtWidgets.QMessageBox.warning(
            self, "Delete Folder?", 
            f"Are you sure you want to delete '{folder_name}'?\n\nThis will delete ALL contents inside!",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if res == QtWidgets.QMessageBox.Yes:
            try:
                import shutil
                shutil.rmtree(path)
                
                # Remove from tree
                parent = item.parent()
                if parent:
                    parent.removeChild(item)
                else:
                    index = self.tree.indexOfTopLevelItem(item)
                    self.tree.takeTopLevelItem(index)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not delete: {e}")

    def on_tree_click(self, item, column):
        path = item.data(0, QtCore.Qt.UserRole)
        if path:
            normalized_path = self._normalize_path(path)
            self.current_folder = self._resolve_folder_path(normalized_path)
            self.hip_path_input.setText(normalized_path)
            self.hip_path_input.setCursorPosition(0)
            self.load_files_from(self.current_folder)

    def load_files_from(self, folder_path):
        folder_path = self._resolve_folder_path(folder_path)
        self.file_table.clear()
        self.current_folder = folder_path
        if not folder_path or not os.path.isdir(folder_path):
            self.header_label.setText("Invalid Folder")
            self.path_label.setText(folder_path or "")
            return

        folder_name = os.path.basename(folder_path)
        self.header_label.setText(folder_name)
        self.path_label.setText(folder_path)
        
        import re
        from datetime import datetime
        
        # Get currently open hip file to highlight it
        try:
            import hou
            current_hip = os.path.normpath(hou.hipFile.name())
        except:
            current_hip = ""
        
        try:
            entries = list(os.scandir(folder_path))
            
            # Group files by base name (strip version number)
            file_groups = {}
            version_pattern = r'_[vV]\d+'
            
            for entry in entries:
                if not entry.is_file():
                    continue
                    
                name = entry.name
                ext = os.path.splitext(name)[1].lower()
                
                # Only process hip files for grouping
                if ext in ['.hip', '.hipnc', '.hiplc']:
                    # Extract base name without version
                    base_name = re.sub(version_pattern, '', os.path.splitext(name)[0])
                    
                    # Extract version number
                    ver_match = re.search(r'_[vV](\d+)', name)
                    version = int(ver_match.group(1)) if ver_match else 0
                    
                    if base_name not in file_groups:
                        file_groups[base_name] = []
                    
                    # Get file info
                    stat = entry.stat()
                    mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    mtime_raw = stat.st_mtime
                    
                    # Check for notes
                    notes_path = self.get_notes_path(entry.path)
                    notes_preview = ""
                    if os.path.exists(notes_path):
                        with open(notes_path, 'r') as f:
                            notes_preview = f.read()[:50].replace('\n', ' ')
                            if len(notes_preview) == 50:
                                notes_preview += "..."
                    
                    file_groups[base_name].append({
                        'name': name,
                        'path': os.path.normpath(entry.path).replace("\\", "/"),
                        'version': version,
                        'date': mod_time,
                        'mtime': mtime_raw,
                        'notes': notes_preview,
                        'ext': ext
                    })
            
            # Sort each group by modification time (latest first), then version as tiebreaker
            for base_name in file_groups:
                file_groups[base_name].sort(key=lambda x: (x['mtime'], x['version']), reverse=True)
            
            # Build tree
            for base_name in sorted(file_groups.keys()):
                versions = file_groups[base_name]
                
                if len(versions) == 1:
                    # Single file, no grouping needed
                    f = versions[0]
                    item = SortableTreeWidgetItem(self.file_table)
                    item.setText(0, f['name'])
                    item.setText(1, f['date'])
                    item.setText(2, f"v{f['version']:03d}" if f['version'] else "-")
                    item.setText(3, f['notes'])
                    item.setData(0, QtCore.Qt.UserRole, f['path'])
                    
                    # Highlight if this is the current file
                    if os.path.normpath(f['path']) == current_hip:
                        self.highlight_current_item(item)
                else:
                    # Multiple versions - create parent with latest
                    latest = versions[0]
                    parent = SortableTreeWidgetItem(self.file_table)
                    parent.setText(0, f"▼ {latest['name']} (+{len(versions)-1} older)")
                    parent.setText(1, latest['date'])
                    parent.setText(2, f"v{latest['version']:03d}")
                    parent.setText(3, latest['notes'])
                    parent.setData(0, QtCore.Qt.UserRole, latest['path'])
                    
                    # Highlight if latest is the current file
                    if os.path.normpath(latest['path']) == current_hip:
                        self.highlight_current_item(parent)
                    
                    # Add older versions as children
                    for f in versions[1:]:
                        child = SortableTreeWidgetItem(parent)
                        child.setText(0, f"   └ {f['name']}")
                        child.setText(1, f['date'])
                        child.setText(2, f"v{f['version']:03d}")
                        child.setText(3, f['notes'])
                        child.setData(0, QtCore.Qt.UserRole, f['path'])
                        
                        # Check if this older version is the current file
                        if os.path.normpath(f['path']) == current_hip:
                            self.highlight_current_item(child)
                            parent.setExpanded(True)  # Expand to show highlighted version
                        else:
                            child.setForeground(0, QtGui.QColor("#888"))
            
            # Show non-hip files at the bottom (optional, skip notes files)
            for entry in entries:
                if entry.is_file():
                    # Skip notes sidecar files
                    if entry.name.endswith('_notes.txt'):
                        continue
                    
                    ext = os.path.splitext(entry.name)[1].lower()
                    if ext not in ['.hip', '.hipnc', '.hiplc']:
                        item = SortableTreeWidgetItem(self.file_table)
                        item.setText(0, entry.name)
                        stat = entry.stat()
                        mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                        item.setText(1, mod_time)
                        item.setText(2, "-")
                        item.setData(0, QtCore.Qt.UserRole, os.path.normpath(entry.path).replace("\\", "/"))
                        item.setForeground(0, QtGui.QColor("#666"))
            
            if self.file_table.topLevelItemCount() == 0:
                empty_item = SortableTreeWidgetItem(self.file_table)
                empty_item.setText(0, "No files in this folder")
                empty_item.setFlags(QtCore.Qt.NoItemFlags)
                
                # Check if this looks like a work area (heuristic)
                is_work_area = False
                try:
                    if os.path.exists(folder_path) and os.path.isdir(folder_path):
                        subs = [e.name for e in os.scandir(folder_path) if e.is_dir()]
                        common_folders = {'geo', 'render', 'tex', 'sim', 'cache', 'comp', 'playback'}
                        if len(set(subs) & common_folders) >= 2:
                            is_work_area = True
                except:
                    pass
                 
                # We removed the button as per request.
                # If we want to bring back the "Smart Work Area" hint later, we can do it subtly.
                
        except Exception as e:
            print(f"Error loading files: {e}")
                
        except Exception as e:
            print(f"Error loading files: {e}")

    def show_file_context_menu(self, position):
        item = self.file_table.itemAt(position)
        if not item:
            return
            
        path = item.data(0, QtCore.Qt.UserRole)
        if not path:
            return
        
        # Check if notes exist for this file
        notes_path = self.get_notes_path(path)
        has_notes = os.path.exists(notes_path)
            
        menu = QtWidgets.QMenu()
        open_action = menu.addAction("Open File")
        folder_action = menu.addAction("Open Containing Folder")
        menu.addSeparator()
        
        if has_notes:
            view_notes_action = menu.addAction("📝 View Notes")
        add_notes_action = menu.addAction("Add/Edit Note")
        
        menu.addSeparator()
        version_up_action = menu.addAction("Save as Next Version")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Delete File")
        
        action = menu.exec_(self.file_table.viewport().mapToGlobal(position))
        
        if action == open_action:
            self.open_file_from_table(item, 0)
        elif action == folder_action:
            import subprocess
            subprocess.Popen(f'explorer /select,"{path}"')
        elif has_notes and action == view_notes_action:
            self.view_notes(path)
        elif action == add_notes_action:
            self.add_notes(path)
        elif action == version_up_action:
            self.version_up(path)
        elif action == delete_action:
            self.delete_file(path)

    def delete_file(self, file_path):
        """Delete a file with confirmation."""
        import os
        name = os.path.basename(file_path)
        res = QtWidgets.QMessageBox.question(
            self, "Delete File", 
            f"Are you sure you want to delete '{name}'?\nThis cannot be undone.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )
        
        if res == QtWidgets.QMessageBox.Yes:
            try:
                os.remove(file_path)
                # Notes file?
                notes = self.get_notes_path(file_path)
                if os.path.exists(notes):
                    os.remove(notes)
                self.load_files_from(self.current_folder)
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Could not delete file: {e}")

    def get_notes_path(self, file_path):
        """Get the notes sidecar file path for a given file."""
        base = os.path.splitext(file_path)[0]
        return base + "_notes.txt"
    
    def view_notes(self, file_path):
        """Display notes for a file."""
        notes_path = self.get_notes_path(file_path)
        if os.path.exists(notes_path):
            with open(notes_path, 'r') as f:
                content = f.read()
            QtWidgets.QMessageBox.information(
                self, f"Notes: {os.path.basename(file_path)}", 
                content
            )
    
    def add_notes(self, file_path):
        """Add or edit notes for a file."""
        notes_path = self.get_notes_path(file_path)
        
        # Load existing notes if any
        existing = ""
        if os.path.exists(notes_path):
            with open(notes_path, 'r') as f:
                existing = f.read()
        
        notes, ok = QtWidgets.QInputDialog.getMultiLineText(
            self, f"Notes: {os.path.basename(file_path)}", 
            "Enter notes:",
            existing
        )
        
        if ok:
            with open(notes_path, 'w') as f:
                f.write(notes)
            # Refresh to show indicator
            self.load_files_from(self.current_folder)

    def version_up(self, file_path=None):
        """Create the next version of a file."""
        # Handle case where button click sends bool or None
        if not file_path or isinstance(file_path, bool):
            # Try to get selected item
            items = self.file_table.selectedItems()
            if items:
                file_path = items[0].data(0, QtCore.Qt.UserRole)
            else:
                QtWidgets.QMessageBox.warning(self, "Selection", "Please select a file to version up.")
                return

        import re
        import shutil
        import os
        
        if not os.path.exists(file_path):
             return
        
        dir_name = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        name_root, ext = os.path.splitext(base_name)
        
        # Parse version
        # Look for _v001 or _v1 at end of name
        match = re.search(r'(_[vV])(\d+)$', name_root)
        if match:
            prefix = match.group(1)
            num_str = match.group(2)
            new_num = int(num_str) + 1
            # Preserve padding
            new_ver = f"{prefix}{str(new_num).zfill(len(num_str))}"
            new_name = name_root[:match.start()] + new_ver + ext
        else:
            # No version found, append _v002
            new_name = name_root + "_v002" + ext
            
        new_path = os.path.join(dir_name, new_name).replace("\\", "/")
        
        if os.path.exists(new_path):
             QtWidgets.QMessageBox.warning(self, "Error", f"File exists: {new_name}")
             return

        try:
            shutil.copy2(file_path, new_path)
            self.load_files_from(self.current_folder)
            
            # Ask to open it?
            res = QtWidgets.QMessageBox.question(
                self, "Version Up", 
                f"Created {new_name}.\nOpen it now?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            if res == QtWidgets.QMessageBox.Yes:
                self.open_file_from_table(None, 0, path_override=new_path)
                
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))

    def open_file_from_table(self, item, column, path_override=None):
        """Open file from table double-click."""
        if path_override:
            path = path_override
        else:
            path = item.data(0, QtCore.Qt.UserRole)
            
        if path:
            path = os.path.normpath(path).replace("\\", "/") # Ensure clean path
            
        if path and os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in ['.hip', '.hipnc', '.hiplc']:
                import hou
                hou.hipFile.load(path)
                self.current_hip_changed.emit(path)
                # Refresh after a short delay to ensure file is loaded
    
    def refresh_current_view(self):
        """Refresh the current folder view to update highlights."""
        if self.current_folder:
            self.load_files_from(self.current_folder)

    def open_in_explorer(self):
        # Open the current folder, not project root
        folder = self._resolve_folder_path(self.current_folder or self.project_path)
        if folder and os.path.exists(folder):
            os.startfile(folder)

    def save_hip_here(self):
        """Save the current hip file to the current folder."""
        folder = self._resolve_folder_path(self.current_folder or self.project_path)
        if not folder or not os.path.exists(folder):
            QtWidgets.QMessageBox.warning(self, "No Folder", "Please select a folder first.")
            return
            
        import hou
        
        # Get current filename or suggest a new one
        current_name = os.path.basename(hou.hipFile.name())
        if current_name == "untitled.hip" or not current_name:
            current_name = "scene_v001.hip"
        
        # Ask for filename
        name, ok = QtWidgets.QInputDialog.getText(
            self, "Save Hip File", 
            f"Filename (will save to: {folder})",
            text=current_name
        )
        
        if ok and name:
            # Ensure .hip extension
            if not name.endswith(('.hip', '.hipnc', '.hiplc')):
                name += '.hip'
            
            save_path = os.path.join(folder, name).replace("\\", "/")
            
            try:
                hou.hipFile.save(save_path)
                self.current_hip_changed.emit(save_path)
                QtWidgets.QMessageBox.information(self, "Saved", f"Saved to:\n{save_path}")
                # Refresh the file list and update tree icon
                self.load_files_from(folder)
                self.update_tree_item_for_folder(folder)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

    def save_next_version(self):
        """Save with incremented version number - instant, no popup."""
        import hou
        import re
        
        folder = self._resolve_folder_path(self.current_folder or self.project_path)
        if not folder or not os.path.exists(folder):
            QtWidgets.QMessageBox.warning(self, "No Folder", "Please select a folder first.")
            return
        
        # Get current filename
        current_path = hou.hipFile.name()
        current_name = os.path.basename(current_path)
        
        # Extract base name (without version)
        pattern = r'(_[vV])(\d+)'
        match = re.search(pattern, current_name)
        
        if match:
            base_name = current_name[:match.start()]
            ext = current_name[match.end():]
            prefix = match.group(1)
            version_len = len(match.group(2))
        else:
            base_name, ext = os.path.splitext(current_name)
            prefix = "_v"
            version_len = 3
        
        # Find highest existing version in folder
        highest_version = 0
        try:
            for entry in os.scandir(folder):
                if entry.is_file():
                    entry_match = re.search(rf'{re.escape(base_name)}{prefix}(\d+)', entry.name, re.IGNORECASE)
                    if entry_match:
                        v = int(entry_match.group(1))
                        if v > highest_version:
                            highest_version = v
        except:
            pass
        
        # Increment from highest
        new_version = highest_version + 1
        new_version_str = str(new_version).zfill(version_len)
        new_name = f"{base_name}{prefix}{new_version_str}{ext}"
        
        # Construct save path
        save_path = os.path.join(folder, new_name).replace("\\", "/")
        
        try:
            hou.hipFile.save(save_path)
            self.current_hip_changed.emit(save_path)
            self.load_files_from(folder)
            self.update_tree_item_for_folder(folder)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save:\n{e}")

    def get_timestamp(self):
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def highlight_current_item(self, item):
        """Highlight the currently open file with a green accent."""
        accent_color = QtGui.QColor("#50c878")  # Green
        for col in range(4):
            item.setForeground(col, accent_color)
        # Add a marker
        current_text = item.text(0)
        if not current_text.startswith("● "):
            item.setText(0, f"● {current_text}")

    def create_first_version(self, folder_path):
        """Create the first version hip file in this folder."""
        folder_name = os.path.basename(folder_path)
        filename = f"{folder_name}_v001.hip"
        path = os.path.join(folder_path, filename).replace("\\", "/")
        
        try:
            # Create a basic hip file
            import hou
            hou.hipFile.save(path)
            self.current_hip_changed.emit(path)
            
            # Refresh view
            self.load_files_from(folder_path)
            # Update tree icon (it should turn orange now)
            self.update_tree_item_for_folder(folder_path)
            
            QtWidgets.QMessageBox.information(
                self, "Created", 
                f"Created {filename}!\n\nYou can now open it."
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to create file: {e}")
