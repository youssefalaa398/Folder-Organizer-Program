from pathlib import Path
import shutil
from Profile import Profile
from Subject import Subject

class PipelineOrganizer:
    def __init__(self, profile):
        if not isinstance(profile, Profile):
            raise TypeError("profile must be a Profile instance")
        self.profile = profile
        self.rules = profile.rules

    @classmethod
    def load_profile(cls, profile_name):
        profile = Profile.load(profile_name)
        return cls(profile)

    def _next_pass_name(self, subject_name):
        """Return next pass name like 'pass001' for given subject_name."""
        existing = self.profile.subjects.get(subject_name, {})
        if not isinstance(existing, dict):
            return "pass001"
        nums = []
        for key in existing.keys():
            if isinstance(key, str) and key.lower().startswith("pass") and key[4:].isdigit():
                nums.append(int(key[4:]))
        nxt = (max(nums) + 1) if nums else 1
        return f"pass{nxt:03d}"

    def create_subject(self, subject_name, destination_root, pass_name=None):
        # if profile allows subsubjects, auto-create/increment pass if not provided
        if self.profile.allow_subsubjects:
            if pass_name is None:
                pass_name = self._next_pass_name(subject_name)
            subject = Subject(subject_name, destination_root, self.profile, pass_name)
            subject.create()
            # store the pass path (full pass folder) under the subject entry
            self.profile.add_subject(subject_name, subject.destination_path, pass_name)
            return subject
        else:
            subject = Subject(subject_name, destination_root, self.profile, None)
            subject.create()
            self.profile.add_subject(subject_name, subject.destination_path)
            return subject

    def get_category(self, file_extension):
        for category, extensions in self.rules.items():
            normalized_exts = [e if e.startswith('.') else f".{e}" for e in extensions]
            if file_extension.lower() in (e.lower() for e in normalized_exts):
                return category
        return "Others"

    def organize_to_subject(self, source_folder, subject, copy_function=shutil.copy2):
        source = Path(source_folder)
        if not source.exists():
            print(f"Source folder '{source}' does not exist.")
            return False
        if not isinstance(subject, Subject):
            raise TypeError("subject must be a Subject instance")

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

        print(f"Copied {copied} files into subject '{subject.name}' at '{subject.destination_path}'")
        return True

    def summarize_subject(self, subject):
        print(f"\nSummary for subject '{subject.name}':")
        if not subject.destination_path.exists():
            print("No files or folders found for this subject.")
            return
        for folder in subject.destination_path.iterdir():
            if folder.is_dir():
                count = len([p for p in folder.iterdir() if p.is_file()])
                print(f"  • {folder.name}: {count} files")


def main():
    print("=== Pipeline Organizer Tool ===")

    profiles = Profile.list_profiles()
    # If no profiles exist, force creation
    if not profiles:
        print("No profiles found. You need to create a profile first.")
        profile = Profile.create_profile_interactively()
        if profile is None:
            print("Profile creation cancelled. Exiting.")
            return
        organizer = PipelineOrganizer(profile)
    else:
        # Offer choice: create new profile or use existing
        while True:
            choice = input("Create new profile (c) or use existing (u)? (c/u): ").strip().lower()
            if choice in ("c", "u"):
                break
            print("Please enter 'c' to create or 'u' to use an existing profile.")

        if choice == "c":
            profile = Profile.create_profile_interactively()
            if profile is None:
                print("Profile creation cancelled. Exiting.")
                return
            organizer = PipelineOrganizer(profile)
        else:
            print("Available profiles:", profiles)
            profile_name = input("Enter profile name to use: ").strip()
            try:
                organizer = PipelineOrganizer.load_profile(profile_name)
            except FileNotFoundError as e:
                print(e)
                return

    # Show subjects related to this profile before creating a new one
    organizer.profile.show_subjects()

    use_existing = None
    if organizer.profile.subjects:
        use_existing = input("Use an existing subject? (y/n): ").strip().lower()

    if use_existing == "y":
        subject_name = input("Enter existing subject name: ").strip()
        if subject_name not in organizer.profile.subjects:
            print(f"Subject '{subject_name}' not registered under profile '{organizer.profile.name}'.")
            return

        dest_entry = organizer.profile.subjects[subject_name]

        if organizer.profile.allow_subsubjects and isinstance(dest_entry, dict):
            # sample_pass_path points to: <destination_root>/<subject_name>/<passNNN>
            sample_pass_path = list(dest_entry.values())[0]
            sample_pass_path = Path(sample_pass_path)
            # destination_root is parents[1] for this layout (fallback to parent)
            destination_root = sample_pass_path.parents[1] if len(sample_pass_path.parents) >= 2 else sample_pass_path.parent
            subject = organizer.create_subject(subject_name, destination_root, pass_name=None)
        else:
            # reuse the stored destination root for subjects without passes
            destination_root = dest_entry if isinstance(dest_entry, str) else input("Enter destination root folder (full path): ").strip()
            subject = Subject(subject_name, destination_root, organizer.profile, None)
            subject.create()
    else:
        subject_name = input("Enter subject/project name to create: ").strip()
        destination_root = input("Enter destination root folder for the subject (full path): ").strip()
        pass_name = None
        if organizer.profile.allow_subsubjects:
            pass_name = input("Optional pass/version name (leave empty to auto-increment): ").strip() or None
        subject = organizer.create_subject(subject_name, destination_root, pass_name)

    source_folder = input("Enter source folder containing files to organize (full path): ").strip()
    organizer.organize_to_subject(source_folder, subject)
    organizer.summarize_subject(subject)


if __name__ == "__main__":
    main()
