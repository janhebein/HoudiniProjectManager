"""
Central configuration for HoudiniProjectManager.
Handles paths for user data (stored in Houdini prefs) vs tool data (in install dir).
"""
import os

# Tool version
VERSION = "1.0.0"
TOOL_NAME = "HoudiniProjectManager"

def get_tool_dir():
    """Returns the directory where the tool is installed."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_user_data_dir():
    """
    Returns the directory for user-specific data (projects list, settings).
    Uses Houdini's user prefs directory so data persists across tool updates.
    """
    # Try to get Houdini's prefs directory
    try:
        import hou
        houdini_prefs = hou.homeHoudiniDirectory()
        # Store data in 'prefs' logic to separate from tool installation
        # This allows deleting the tool folder for updates without losing data
        user_dir = os.path.join(houdini_prefs, "prefs", TOOL_NAME)
    except ImportError:
        # Fallback for running outside Houdini (testing)
        user_dir = os.path.join(os.path.expanduser("~"), f".{TOOL_NAME}")

    # Create directory if it doesn't exist
    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    return user_dir

def get_projects_config_path():
    """Path to the projects configuration file."""
    return os.path.join(get_user_data_dir(), "projects_config.json")

def get_user_settings_path():
    """Path to user settings file."""
    return os.path.join(get_user_data_dir(), "user_settings.json")

def get_templates_dir():
    """
    Path to templates directory.
    Templates ship with the tool but users can add custom ones.
    """
    # Built-in templates in tool directory
    return os.path.join(get_tool_dir(), "templates")

def get_user_templates_dir():
    """Path for user-created custom templates."""
    user_templates = os.path.join(get_user_data_dir(), "templates")
    if not os.path.exists(user_templates):
        os.makedirs(user_templates)
    return user_templates

def get_icons_dir():
    """Path to icons directory (ships with tool)."""
    return os.path.join(get_tool_dir(), "icons")

def get_assets_dir():
    """Path to assets directory (ships with tool)."""
    return os.path.join(get_tool_dir(), "assets")

def migrate_old_config():
    """
    Migrate config files from old location (tool dir) to new location (user prefs).
    Called once on first run after update.
    """
    tool_dir = get_tool_dir()
    
    # Check both the package dir and the install root (3 levels up)
    # Because we moved the package deep into scripts/python/...
    install_root = os.path.dirname(os.path.dirname(os.path.dirname(tool_dir)))
    
    user_dir = get_user_data_dir()

    files_to_migrate = [
        ("projects_config.json", get_projects_config_path()),
        ("user_settings.json", get_user_settings_path()),
    ]

    migrated = []
    for old_name, new_path in files_to_migrate:
        # Check package dir first, then install root
        paths_to_check = [
            os.path.join(tool_dir, old_name),
            os.path.join(install_root, old_name)
        ]
        
        old_path = None
        for p in paths_to_check:
            if os.path.exists(p):
                old_path = p
                break
        
        if old_path and not os.path.exists(new_path):
            try:
                import shutil
                shutil.copy2(old_path, new_path)
                migrated.append(old_name)
                # Optionally remove old file
                # os.remove(old_path)
            except Exception as e:
                print(f"[{TOOL_NAME}] Failed to migrate {old_name}: {e}")

    if migrated:
        print(f"[{TOOL_NAME}] Migrated config to: {user_dir}")
        print(f"[{TOOL_NAME}] Files migrated: {', '.join(migrated)}")

    return migrated
