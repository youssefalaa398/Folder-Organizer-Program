from pathlib import Path
from datetime import datetime
import shutil

class Subject:
    def __init__(self, name, destination_root, profile, pass_name=None):
        
        self.name = name
        self.profile = profile
        self.pass_name = pass_name
        self.destination_root = Path(destination_root)
        self.destination_path = self.destination_root / self.name
        if pass_name and profile.allow_subsubjects:
            self.destination_path = self.destination_path  / pass_name
        self.folders = list(profile.rules.keys())
        self.notes = profile.notes
        self.created_at = datetime.now().isoformat()

    def create(self):
        self.destination_path.mkdir(parents=True, exist_ok=True)
        for folder in self.folders:
            (self.destination_path / folder).mkdir(exist_ok=True)
        print(f" Subject '{self.name}' created at '{self.destination_path}'")

    def delete(self):
        if self.destination_path.exists() and self.destination_path.is_dir():
            shutil.rmtree(self.destination_path)
            print(f" Subject '{self.name}' deleted from '{self.destination_path}'")
        else:
            print(f" Subject '{self.name}' does not exist at '{self.destination_path}'")
