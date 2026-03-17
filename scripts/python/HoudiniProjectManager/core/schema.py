from HoudiniProjectManager.core import config
import shutil
import os
import json
import re

class SchemaManager(object):
    """
    Handles loading and parsing of Project JSON Templates.
    """
    def __init__(self):
        self.templates = {}
        
        # User templates directory (safe from updates)
        self.template_dir = config.get_user_templates_dir()
        
        # Internal default templates directory
        internal_dir = config.get_templates_dir()
        
        # Migration/Initialization:
        # If user dir is empty, copy defaults from internal dir
        if os.path.exists(internal_dir) and not os.listdir(self.template_dir):
            for f in os.listdir(internal_dir):
                if f.endswith(".json"):
                    src = os.path.join(internal_dir, f)
                    dst = os.path.join(self.template_dir, f)
                    try:
                        shutil.copy2(src, dst)
                    except Exception as e:
                        print(f"Error copying default template {f}: {e}")
        
        self.reload_templates()

    def reload_templates(self):
        """Scans the templates directory for .json files."""
        self.templates = {}
        if not os.path.exists(self.template_dir):
            os.makedirs(self.template_dir)
            
        for f in os.listdir(self.template_dir):
            if f.endswith(".json"):
                path = os.path.join(self.template_dir, f)
                try:
                    with open(path, 'r') as fp:
                        data = json.load(fp)
                        if "name" in data:
                            self.templates[data["name"]] = data
                            self.templates[data["name"]]['_filename'] = f
                except Exception as e:
                    print(f"Error loading template {f}: {e}")

    def get_template_names(self):
        return list(self.templates.keys())

    def get_template(self, name):
        return self.templates.get(name)

    def resolve_path(self, template_name, variables):
        """
        Resolves the root path for a project based on variables.
        variables: dict e.g. {'client': 'A', 'project': 'B'}
        """
        template = self.get_template(template_name)
        if not template:
            return None
        
        # Basic variable substitution
        # This is a placeholder. Real implementation needs recursion.
        root_pattern = template.get("root_path", "C:/temp")
        
        # Simple Format substitution
        try:
            return root_pattern.format(**variables)
        except KeyError as e:
            print(f"Missing variable for path resolution: {e}")
            return root_pattern

    def save_template(self, name, data):
        """Saves a template dictionary to a JSON file."""
        # Sanitize name for filename
        filename = "".join([c for c in name if c.isalnum() or c in (' ', '_', '-')]).strip()
        filename = filename.replace(" ", "_").lower() + ".json"
        
        path = os.path.join(self.template_dir, filename)
        
        try:
            with open(path, 'w') as f:
                json.dump(data, f, indent=4)
            
            # Update cache
            self.templates[name] = data
            self.templates[name]['_filename'] = filename
            return True
        except Exception as e:
            print(f"Error saving template: {e}")
            return False

    def delete_template(self, name):
        """Deletes a template file."""
        template = self.get_template(name)
        if not template: return False
        
        filename = template.get('_filename')
        if not filename: return False
        
        path = os.path.join(self.template_dir, filename)
        
        try:
            if os.path.exists(path):
                os.remove(path)
                
            if name in self.templates:
                del self.templates[name]
            return True
        except Exception as e:
            print(f"Error deleting template: {e}")
            return False
