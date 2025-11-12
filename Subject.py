from pathlib import Path
from datetime import datetime
import shutil

class Subject:
    def __init__(self, name, destination_root, profile):
        """
        name: Name of the project/subject
        destination_root: Root path where the subject folder will be created
        profile: Profile object, used to get folder rules
        """
        self.name = name
        self.destination_root = Path(destination_root)
        self.profile = profile
        self.destination_path = self.destination_root / self.name
        self.folders = list(profile.rules.keys())  # automatically take profile folders
        self.notes = profile.notes
        self.created_at = datetime.now().isoformat()

    def create(self):
        """Create the subject/project folder and all folders from the profile."""
        self.destination_path.mkdir(parents=True, exist_ok=True)
        for folder in self.folders:
            (self.destination_path / folder).mkdir(exist_ok=True)
        print(f"✅ Subject '{self.name}' created under profile '{self.profile.name}'")

    def delete(self):
        """Delete the subject folder entirely."""
        if self.destination_path.exists() and self.destination_path.is_dir():
            shutil.rmtree(self.destination_path)
            print(f"🗑️ Subject '{self.name}' deleted from '{self.destination_path}'")
        else:
            print(f"⚠️ Subject '{self.name}' does not exist at '{self.destination_path}'")
