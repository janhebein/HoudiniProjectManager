import os

class ProjectScanner:
    """
    Helper to scan project directories for content.
    """
    def __init__(self, root_path):
        self.root_path = root_path
        
    def scan_structure(self):
        """
        Returns a dictionary representing the folder structure.
        Simple recursive scan for now.
        """
        return self._scan_recursive(self.root_path)

    def _scan_recursive(self, path):
        path = os.path.normpath(path).replace("\\", "/")
        name = os.path.basename(path)
        node = {"name": name, "path": path, "type": "folder", "children": []}
        
        try:
            for entry in os.scandir(path):
                if entry.is_dir():
                    # Skip common junk
                    if entry.name.startswith(".") or entry.name == "__pycache__":
                        continue
                    node["children"].append(self._scan_recursive(os.path.normpath(entry.path)))
                elif entry.is_file():
                    if entry.name.endswith(".hip") or entry.name.endswith(".hiplc") or entry.name.endswith(".hipnc"):
                        node["children"].append({
                            "name": entry.name,
                            "path": os.path.normpath(entry.path).replace("\\", "/"),
                            "type": "file"
                        })
        except PermissionError:
            pass
            
        # Sort folders first, then files
        node["children"].sort(key=lambda x: (x["type"] != "folder", x["name"]))
        return node

    def count_hip_files_and_work_areas(self):
        """
        Count hip files and identify work area folders (folders containing hip files).

        Returns:
            tuple: (hip_count: int, work_areas: list of folder paths)
        """
        work_areas = set()
        hip_count = self._count_recursive(self.root_path, work_areas)
        return hip_count, list(work_areas)

    def _count_recursive(self, path, work_areas):
        """Recursively count hip files and collect work area folders."""
        path = os.path.normpath(path).replace("\\", "/")
        hip_count = 0
        has_hip_here = False

        try:
            for entry in os.scandir(path):
                if entry.is_file():
                    if entry.name.endswith(('.hip', '.hipnc', '.hiplc')):
                        hip_count += 1
                        has_hip_here = True
                elif entry.is_dir():
                    if not entry.name.startswith('.') and entry.name != '__pycache__':
                        hip_count += self._count_recursive(entry.path, work_areas)
        except PermissionError:
            pass

        if has_hip_here:
            work_areas.add(path.replace("\\", "/"))

        return hip_count
