import shutil
from pathlib import Path
from Profile import Profile  # import your Profile class
from Subject import Subject

class PipelineOrganizer:
    def __init__(self, profile, source_folder, destination_folder):
        """
        profile: Profile object containing name, rules, notes
        source_folder: folder to organize
        destination_folder: folder to copy organized files into
        """
        self.profile = profile
        self.rules = profile.rules
        self.source_folder = Path(source_folder)
        self.destination_folder = Path(destination_folder)

    def get_category(self, file_extension):
        """Return the category for a file extension based on the profile rules."""
        for category, extensions in self.rules.items():
            if file_extension in extensions:
                return category
        return "Others"

    def organize_files(self):
        """Organize files from source to destination based on profile rules."""
        print(f"🧩 Organizing files using profile '{self.profile.name}'...")
        if not self.source_folder.exists():
            print(f"⚠️ Source folder '{self.source_folder}' does not exist.")
            return

        self.destination_folder.mkdir(parents=True, exist_ok=True)

        for file in self.source_folder.iterdir():
            if file.is_file():
                category = self.get_category(file.suffix)
                dest_dir = self.destination_folder / category
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy(file, dest_dir / file.name)

        print("✅ Organization complete.")

    def summarize(self):
        """Print a summary of how many files are in each category folder."""
        print("\n📦 Summary:")
        if not self.destination_folder.exists():
            print("No files organized yet.")
            return

        for folder in self.destination_folder.iterdir():
            if folder.is_dir():
                count = len(list(folder.glob("*")))
                print(f"  • {folder.name}: {count} files")




def main():
    print("=== Pipeline Organizer Tool ===")
    #new_profile = Profile.create_profile_interactively()
    Profile.delete_profile("3d pipeline")  
    #print("📁 Found profiles:", profiles)
 

if __name__ == "__main__":
    main()
