import shutil
from pathlib import Path
from Profile import Profile  # import your Profile class
from Subject import Subject

class PipelineOrganizer:
    def __init__(self, profile):
       
        if not isinstance(profile, Profile):
            raise TypeError("profile must be a Profile instance")
        self.profile = profile
        self.rules = profile.rules

    @classmethod
    def load_profile(cls, profile_name, folder="profiles"):
        profile = Profile.load(profile_name, folder=folder)
        return cls(profile)

    def create_subject(self, subject_name, destination_root):
      
        subject = Subject(subject_name, destination_root, self.profile)
        subject.create()
        # track subject with its destination root in profile
        self.profile.add_subject(subject.name, subject.destination_root)
        return subject

    def get_category(self, file_extension):
        for category, extensions in self.rules.items():
            # normalize to include leading dot if user rules might not include it
            normalized_exts = [e if e.startswith('.') else f".{e}" for e in extensions]
            if file_extension.lower() in (e.lower() for e in normalized_exts):
                return category
        return "Others"

    def organize_to_subject(self, source_folder, subject, copy_function=shutil.copy2):
        
        source = Path(source_folder)
        if not source.exists():
            print(f"⚠️ Source folder '{source}' does not exist.")
            return False

        if not isinstance(subject, Subject):
            raise TypeError("subject must be a Subject instance")

        # ensure subject folders exist
        subject.create()

        copied = 0
        for item in source.iterdir():
            if item.is_file():
                category = self.get_category(item.suffix)
                dest_dir = subject.destination_path / category
                dest_dir.mkdir(parents=True, exist_ok=True)
                try:
                    copy_function(str(item), str(dest_dir / item.name))
                    copied += 1
                except Exception as e:
                    print(f"Failed to copy '{item}': {e}")

        print(f"✅ Copied {copied} files into subject '{subject.name}' at '{subject.destination_path}'")
        return True

    def summarize_subject(self, subject):
        if not isinstance(subject, Subject):
            raise TypeError("subject must be a Subject instance")

        print(f"\n📦 Summary for subject '{subject.name}':")
        if not subject.destination_path.exists():
            print("No files or subject folder found.")
            return

        for folder in subject.destination_path.iterdir():
            if folder.is_dir():
                count = len([p for p in folder.iterdir() if p.is_file()])
                print(f"  • {folder.name}: {count} files")


def main():
    print("=== Pipeline Organizer Tool ===")
    profiles = Profile.list_profiles()
    if not profiles:
        print("No profiles found. Create one using Profile.create_profile_interactively() or place a JSON in the profiles folder.")
        return

    print("Available profiles:", profiles)
    profile_name = input("Enter profile name to use: ").strip()
    try:
        organizer = PipelineOrganizer.load_profile(profile_name)
    except FileNotFoundError as e:
        print(e)
        return

    subject_name = input("Enter subject/project name to create: ").strip()
    destination_root = input("Enter destination root folder for the subject (full path): ").strip()
    source_folder = input("Enter source folder containing files to organize (full path): ").strip()

    subject = organizer.create_subject(subject_name, destination_root)
    organizer.organize_to_subject(source_folder, subject)
    organizer.summarize_subject(subject)


if __name__ == "__main__":
    main()
