import os
import json

class ProjectBuilder:
    """
    Creates folder structures based on a JSON template and user variables.
    """
    def __init__(self, template_data):
        self.template = template_data
        self.work_area = None

    def build(self, variables):
        """
        Executes the build process.
        variables: dict of values like {'root': 'P:/jobs', 'client': 'CocaCola', ...}
        """
        self.work_area = None # Reset
        
        try:
            root_path = self.template["root_path"].format(**variables)
        except KeyError as e:
            raise KeyError(f"Root path template requires missing variable: {e}")
            
        root_path = os.path.normpath(root_path).replace("\\", "/")

        
        # 1. Create Root
        if not os.path.exists(root_path):
            try:
                os.makedirs(root_path)
                pass
            except Exception as e:
                raise Exception(f"Failed to create root {root_path}: {e}")
            
        # 2. Build recursive structure
        structure = self.template.get("structure")
        if structure:
            self._build_node(root_path, structure, variables)
            
        return root_path
    
    def get_work_area(self):
        """Returns the absolute path to the folder marked as is_work_area"""
        return self.work_area

    def _build_node(self, parent_path, node, variables):
        # Resolve name
        try:
            # If variable is empty string, we treat it as "Skip this node"
            # But we must check if the format *result* is empty.
            # e.g. "{sequence}" -> ""
            name_pattern = node["name"]
            
            # Check if any required var is empty in the variables dict
            # (Simple heuristic: if the pattern contains {var} and variables[var] is empty)
            import re
            required = re.findall(r"\{(\w+)\}", name_pattern)
            for r in required:
                if not variables.get(r):
                    return  # Skip node if variable is empty

            node_name = name_pattern.format(**variables)
        except KeyError as e:
            # If a variable is missing entirely
            return

        if not node_name:
            return

        current_path = os.path.normpath(os.path.join(parent_path, node_name)).replace("\\", "/")
        
        if node["type"] == "directory":
            if not os.path.exists(current_path):
                os.makedirs(current_path)
            
            # Check for work area tag
            if node.get("is_work_area"):
                self.work_area = current_path.replace("\\", "/")
                
            # Process children
            children = node.get("children", [])
            for child in children:
                self._build_node(current_path, child, variables)
