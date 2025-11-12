class Subject:
    def __init__(self, name, destination_path, profile_name, folders=None, notes=None, tags=None):
        self.name = name
        self.destination_path = Path(destination_path)
        self.profile_name = profile_name
        self.folders = folders or []
        self.notes = notes
        self.tags = tags or []
        self.created_at = datetime.now().isoformat()

    def create(self):
        # Create subject folder and subfolders
        self.destination_path.mkdir(parents=True, exist_ok=True)
        for folder in self.folders:
            (self.destination_path / folder).mkdir(exist_ok=True)
        print(f"✅ Subject '{self.name}' created under '{self.profile_name}'")

    @staticmethod
    def list_subjects(profile_name):
        # load all subjects linked to a profile
        pass

    @staticmethod
    def delete_subject(name, profile_name):
        # delete a specific subject folder
        pass
