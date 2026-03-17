import os
import json
from HoudiniProjectManager.core import config

CONFIG_FILE = config.get_projects_config_path()

class ProjectData:
    """represents a single project"""
    # Status constants
    STATUS_NOT_STARTED = "not_started"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_DONE = "done"
    
    # Category constants
    CATEGORY_PERSONAL = "Personal"
    CATEGORY_CLIENT = "Client"
    CATEGORY_RND = "Quick R&D"
    CATEGORY_OTHER = "Other"
    
    def __init__(self, name, path, icon=None, project_type="simple", 
                 client="", status="not_started", favorite=False, 
                 notes="", last_opened="", category="Personal", custom_fields=None, color="", tags=None):
        self.name = name
        self.path = path.replace("\\", "/")
        self.icon = icon
        self.project_type = project_type
        self.client = client
        self.status = status
        self.favorite = favorite
        self.notes = notes
        self.last_opened = last_opened
        self.category = category
        self.custom_fields = custom_fields or {}
        self.color = color  # e.g. "#ff5500" or "" for no color
        self.tags = tags or []

    def to_dict(self):
        return {
            "name": self.name,
            "path": self.path,
            "icon": self.icon,
            "project_type": self.project_type,
            "client": self.client,
            "status": self.status,
            "favorite": self.favorite,
            "notes": self.notes,
            "last_opened": self.last_opened,
            "category": self.category,
            "custom_fields": self.custom_fields,
            "color": self.color,
            "tags": self.tags
        }

class ProjectListManager:
    """Manages the list of all projects"""
    def __init__(self):
        self.projects = []
        self.load()

    def add_project(self, name, path, save=True):
        # Check for duplicates
        for p in self.projects:
            if p.path == path.replace("\\", "/"):
                return
        
        self.projects.append(ProjectData(name, path))
        if save:
            self.save()

    def remove_project(self, project_to_remove):
        # Filter out the project by path (assuming unique paths)
        self.projects = [p for p in self.projects if p.path.replace("\\", "/") != project_to_remove.path.replace("\\", "/")]
        self.save()

    def get_project_by_path(self, path):
        """Find existing project by path."""
        normalized = path.replace("\\", "/")
        for project in self.projects:
            if project.path == normalized:
                return project
        return None

    def save(self):
        data = [p.to_dict() for p in self.projects]
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def load(self):
        self.projects = []
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        self.projects.append(ProjectData(
                            item["name"], 
                            item["path"], 
                            item.get("icon"),
                            item.get("project_type", "simple"),
                            item.get("client", ""),
                            item.get("status", "not_started"),
                            item.get("favorite", False),
                            item.get("notes", ""),
                            item.get("last_opened", ""),
                            item.get("category", "Personal"),
                            item.get("custom_fields", {}),
                            item.get("color", ""),
                            item.get("tags", [])
                        ))
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            # Add a demo project if empty
            self.add_project("Demo Project", "C:/temp/demo_project", save=False)
