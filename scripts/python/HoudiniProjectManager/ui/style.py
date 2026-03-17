from hutil.Qt import QtWidgets, QtGui

def get_stylesheet():
    return """
    QWidget {
        background-color: #2b2b2b;
        color: #dddddd;
        font-family: 'Segoe UI', sans-serif;
        font-size: 10pt;
    }

    /* Buttons */
    QPushButton {
        background-color: #444444;
        border: 1px solid #555555;
        border-radius: 4px;
        padding: 6px 12px;
        color: #ffffff;
    }
    QPushButton:hover {
        background-color: #555555;
        border-color: #666666;
    }
    QPushButton:pressed {
        background-color: #333333;
    }
    QPushButton:checked {
        background-color: #4a90e2;
        border-color: #4a90e2;
    }

    /* Primary Button (Use objectName="primary") */
    QPushButton#primary {
        background-color: #dba038; /* Houdini Orange-ish */
        color: #111;
        font-weight: bold;
        border: none;
    }
    QPushButton#primary:hover {
        background-color: #fcb844;
    }

    /* Input Fields */
    QLineEdit, QComboBox, QPlainTextEdit {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 4px;
        padding: 4px;
        color: #eee;
    }
    QLineEdit:focus, QComboBox:focus {
        border: 1px solid #dba038;
    }

    /* Lists and Trees */
    QListWidget, QTreeWidget {
        background-color: #1e1e1e;
        border: 1px solid #333;
        border-radius: 4px;
        outline: none;
    }
    QListWidget::item, QTreeWidgetItem {
        padding: 4px;
    }
    QListWidget::item:selected, QTreeWidgetItem:selected {
        background-color: #3d5a80;
        color: white;
        border-radius: 2px;
    }
    QListWidget::item:hover, QTreeWidgetItem:hover {
        background-color: #2a2a2a;
    }

    /* Tab Widget */
    QTabWidget::pane {
        border: 1px solid #333;
        background-color: #2b2b2b;
    }
    QTabBar::tab {
        background-color: #333;
        color: #888;
        padding: 8px 16px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
        margin-right: 2px;
    }
    QTabBar::tab:selected {
        background-color: #2b2b2b;
        color: #dba038;
        border-bottom: 2px solid #dba038;
    }

    /* Scrollbars (Subtle) */
    QScrollBar:vertical {
        border: none;
        background: #2b2b2b;
        width: 10px;
        margin: 0px;
    }
    QScrollBar::handle:vertical {
        background: #555;
        min-height: 20px;
        border-radius: 5px;
    }
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    """

def apply_theme(widget):
    widget.setStyleSheet(get_stylesheet())
