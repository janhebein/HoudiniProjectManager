from hutil.Qt import QtWidgets, QtCore, QtGui

class StructureNode(object):
    def __init__(self, name, type="directory", parent=None):
        self.name = name
        self.type = type
        self.children = []
        self.parent = parent
        self.is_work_area = False
        
        if parent:
            parent.children.append(self)
            
    def to_dict(self):
        data = {
            "type": self.type,
            "name": self.name
        }
        if self.is_work_area:
            data["is_work_area"] = True
            
        if self.children:
            data["children"] = [c.to_dict() for c in self.children]
            
        return data

class EditorDelegate(QtWidgets.QStyledItemDelegate):
    """Custom delegate to force styles on the QLineEdit created by the tree for renaming."""
    def createEditor(self, parent, option, index):
        editor = super(EditorDelegate, self).createEditor(parent, option, index)
        if isinstance(editor, QtWidgets.QLineEdit):
            # Force Palette Colors (overrides Houdini's proxy style)
            pal = editor.palette()
            pal.setColor(QtGui.QPalette.Text, QtGui.QColor("#ffffff"))
            pal.setColor(QtGui.QPalette.Base, QtGui.QColor("#252525"))
            pal.setColor(QtGui.QPalette.Highlight, QtGui.QColor("#3d5a80"))
            pal.setColor(QtGui.QPalette.HighlightedText, QtGui.QColor("#ffffff"))
            editor.setPalette(pal)
            
            # CSS fallback
            editor.setStyleSheet("""
                QLineEdit {
                    background-color: #252525;
                    color: #ffffff;
                    selection-background-color: #3d5a80;
                    selection-color: #ffffff;
                }
            """)
        return editor

class StructureEditor(QtWidgets.QWidget):
    """
    A Miller Column-style or Tree-style editor for Folder Structures.
    For simplicity, we start with a Tree View which handles hierarchy natively.
    """
    def __init__(self, parent=None, context=None):
        super(StructureEditor, self).__init__(parent)
        
        # Context includes useful variables like 'project_name', 'root_path', 'client'
        self.context = context or {}
        self.root_node = StructureNode("root")
        
        self.setup_ui()
        
    def load_structure_json(self, structure):
        """
        Populates the tree from a structure dictionary.
        """
        self.root_node = StructureNode("root")
        
        def parse_node(dict_node, parent_obj):
            name = dict_node.get("name", "Unnamed")
            
            new_node = StructureNode(name, type=dict_node.get("type", "directory"), parent=parent_obj)
            if dict_node.get("is_work_area"):
                new_node.is_work_area = True
                
            for child_dict in dict_node.get("children", []):
                parse_node(child_dict, new_node)

        if structure:
            # Check if structure is a wrapper (name=".")
            if structure.get("name") == ".":
                # Load children directly into root_node
                for child_dict in structure.get("children", []):
                    parse_node(child_dict, self.root_node)
            else:
                # Legacy or single-root structure: import as is
                parse_node(structure, self.root_node)
            
        self.refresh_tree()

    def setup_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        
        # Toolbar
        toolbar = QtWidgets.QHBoxLayout()
        
        self.add_btn = QtWidgets.QPushButton("+ Add Folder")
        self.add_btn.clicked.connect(self.add_folder)
        
        self.remove_btn = QtWidgets.QPushButton("- Remove")
        self.remove_btn.clicked.connect(self.remove_folder)
        
        self.work_area_btn = QtWidgets.QPushButton("* Set Work Area")
        self.work_area_btn.setCheckable(True)
        self.work_area_btn.clicked.connect(self.toggle_work_area)
        
        toolbar.addWidget(self.add_btn)
        toolbar.addWidget(self.remove_btn)
        toolbar.addWidget(self.work_area_btn)
        layout.addLayout(toolbar)
        
        # Tree View
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderLabels(["Structure"])
        self.tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.tree.itemChanged.connect(self.on_item_changed)  # Sync edits
        
        # Attach our custom delegate for renaming items
        self.delegate = EditorDelegate(self.tree)
        self.tree.setItemDelegate(self.delegate)
        
        self.tree.setStyleSheet("""
            QLineEdit {
                background-color: #252525;
                color: #ffffff;
                selection-background-color: #3d5a80;
                selection-color: #ffffff;
                border: 1px solid #3d5a80;
            }
        """)
        layout.addWidget(self.tree)
        
        # Dynamic Instructions based on Context
        proj_name = self.context.get("project_name", "your Project")
        loc_path = self.context.get("location", "C:/")
        
        # Format the actual path if loc_path doesn't end in slash
        if not loc_path.endswith("/") and not loc_path.endswith("\\"):
            loc_path += "/"
            
        example_path = f"{loc_path}{proj_name}"
        
        instruction_text = (
            f"<b>{proj_name}</b> represents your main Project Folder (<i>{example_path}</i>).<br>"
            "Any folders added <b>below</b> it will be created <b>inside</b> that main folder."
        )
        self.instructions = QtWidgets.QLabel(instruction_text)
        self.instructions.setWordWrap(True)
        layout.addWidget(self.instructions)
        
        self.refresh_tree()
        
    def refresh_tree(self):
        self.tree.clear()
        
        def add_items(parent_node, parent_item):
            for child in parent_node.children:
                item = QtWidgets.QTreeWidgetItem(parent_item)
                item.setText(0, child.name)
                item.setData(0, QtCore.Qt.UserRole, child)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
                
                if child.is_work_area:
                    item.setForeground(0, QtGui.QColor("#ffcc00"))
                    item.setText(0, f"{child.name}  [ WORK AREA ]")
                
                add_items(child, item)
                
        # Root is invisible container, show children
        root_item = QtWidgets.QTreeWidgetItem(self.tree)
        
        # Let's dynamically display the live Project Name if we have it
        display_root = self.context.get("project_name", "Project Root (Top Level)")
        
        root_item.setText(0, display_root)
        
        # Make root bold to signify it's the master folder
        font = root_item.font(0)
        font.setBold(True)
        root_item.setFont(0, font)
        
        root_item.setData(0, QtCore.Qt.UserRole, self.root_node)
        
        add_items(self.root_node, root_item)
        
        # Explicitly keep the root item expanded
        root_item.setExpanded(True)
        self.tree.expandAll()
        
    def add_folder(self):
        # Add to currently selected item
        selection = self.tree.selectedItems()
        if not selection:
            parent_node = self.root_node
        else:
            parent_node = selection[0].data(0, QtCore.Qt.UserRole)
            
        new_node = StructureNode("New Folder", parent=parent_node)
        self.refresh_tree()
        
    def remove_folder(self):
        selection = self.tree.selectedItems()
        if not selection: return
        
        node = selection[0].data(0, QtCore.Qt.UserRole)
        if node == self.root_node: return # Can't delete root
        
        if node.parent:
            node.parent.children.remove(node)
            
        self.refresh_tree()
        
    def toggle_work_area(self):
        selection = self.tree.selectedItems()
        if not selection: return
        
        node = selection[0].data(0, QtCore.Qt.UserRole)
        node.is_work_area = not node.is_work_area
        self.refresh_tree()
        
    def on_selection_changed(self):
        selection = self.tree.selectedItems()
        if not selection:
            self.work_area_btn.setChecked(False)
            return
            
        node = selection[0].data(0, QtCore.Qt.UserRole)
        self.work_area_btn.setChecked(node.is_work_area)
    
    def on_item_changed(self, item, column):
        """Sync tree item text changes back to node data."""
        node = item.data(0, QtCore.Qt.UserRole)
        if node and node != self.root_node:
            new_name = item.text(0)
            # Strip "(Work Area)" suffix if present
            if new_name.endswith(" (Work Area)"):
                new_name = new_name[:-12]
            node.name = new_name

    def get_structure_json(self):
        # Convert root_node tree to JSON structure dict
        # We skip the root wrapper itself for the 'structure' key
        # Or we return the children as the root structure?
        # Our schema expects a single root node in 'structure' usually
        
        # Let's assume the user builds the CONTENT of the project folder
        # So we wrap it in a generic root
        
        # Helper
        def node_to_dict(n):
            d = {"type": "directory", "name": n.name}
            if n.is_work_area: d["is_work_area"] = True
            if n.children:
                d["children"] = [node_to_dict(c) for c in n.children]
            return d

        # Standardizing: The user defines children of Project.
        # But our schema is: Root -> Sequence -> Shot.
        # Our Editor starts at Root.
        
        # If root has multiple children, we wrap them? 
        # Actually our schema supports 'structure' being a dict.
        
        # Always return a wrapper with period "." to signify "Project Root"
        # This ensures the Builder treats these items as contents of the project folder
        # rather than the project folder definition itself.
        wrapper = {"type": "directory", "name": ".", "children": []}
        wrapper["children"] = [node_to_dict(c) for c in self.root_node.children]
        return wrapper

            
        self.refresh_tree()
