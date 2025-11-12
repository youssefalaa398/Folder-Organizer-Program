import json
from pathlib import Path
from Subject import Subject
# -------------------- PROFILE CLASS --------------------
class Profile:
    def __init__(self, name, rules=None, notes="", subjects=None):
        self.name = name
        self.rules = rules or {
            "Maya": [".ma", ".mb"],
            "Models": [".fbx", ".obj"],
            "Textures": [".png", ".jpg", ".tiff"],
            "Renders": [".exr", ".tga"],
            "Substance": [".sbsar", ".spp"],
            "Zbrush Scenes": [".zpr", ".ztl"]
        }
        self.notes = notes
        # subjects stored as { "subject_name": "destination_root_path" }
        self.subjects = subjects or {}

    def save(self, folder="profiles"):
        # Get the folder where Profile.py resides
        script_folder = Path(__file__).parent
        folder_path = script_folder / folder
        folder_path.mkdir(parents=True, exist_ok=True)  # ensure folder exists

        profile_path = folder_path / f"{self.name}.json"
        
        data = {
            "name": self.name,
            "rules": self.rules,
            "notes": self.notes,
            "subjects": self.subjects
        }

        print(f"📝 Saving profile to: {profile_path}")  # debug
        try:
            with open(profile_path, "w") as f:
                json.dump(data, f, indent=4)
            print(f"✅ Profile '{self.name}' saved to {profile_path}")
        except Exception as e:
            print(f"Failed to save profile: {e}")

    @classmethod
    def load(cls, name, folder="profiles"):
        """Load a profile from JSON file."""
        script_folder = Path(__file__).parent
        folder_path = script_folder / folder
        profile_path = folder_path / f"{name}.json"
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile '{name}' not found in {folder}")
        with open(profile_path, "r") as f:
            data = json.load(f)
        return cls(
            name=data.get("name"),
            rules=data.get("rules"),
            notes=data.get("notes", ""),
            subjects=data.get("subjects", {})
        )


    @staticmethod
    def list_profiles(folder="profiles"):
        """List all saved profiles in the script's 'profiles' folder."""
        script_folder = Path(__file__).parent
        folder_path = script_folder / folder
        if not folder_path.exists():
            print("⚠️ No 'profiles' folder found.")
            return []
        profiles = [f.stem for f in folder_path.glob("*.json")]
        if not profiles:
            print("⚠️ No profiles found in the folder.")
        return profiles


    @staticmethod
    def create_profile_interactively():
        """Interactively create a new profile and save it as JSON."""
        print("Creating a new profile")
        existing_profiles = Profile.list_profiles()

        #  Profile name
        while True:
            name = input("Enter profile name: ").strip()
            if name:
                break
            print("⚠️ Profile name cannot be empty.")

        
        
        if name in existing_profiles:
            print("profile already exists!") 


        else:
            #  Optional notes
            notes = input("Add notes (optional): ").strip()

            # Choose default rules or custom rules
            use_default = input("Use default rules? (y/n): ").strip().lower()
            
            if use_default == 'y':
                profile = Profile(name=name, notes=notes)
            else:
                # Let user input categories and extensions
                rules = {}
                print("Enter your categories and extensions (type 'done' when finished):")
                while True:
                    category = input("Category name: ").strip()
                    if category.lower() == 'done':
                        break
                    exts = input("Extensions (comma separated, include the dot, e.g., .ma,.mb): ").strip()
                    rules[category] = [e.strip() for e in exts.split(',') if e.strip()]
                profile = Profile(name, rules, notes)

            # 4️⃣ Save the profile
            profile.save()
            print(f"Profile '{profile.name}' created successfully!\n")
            return profile
        
    @staticmethod   
    def delete_profile(name, folder="profiles"):
        """Delete a saved profile JSON file by name."""
        script_folder = Path(__file__).parent
        folder_path = script_folder / folder
        profile_path = folder_path / f"{name}.json"

        if not profile_path.exists():
            print(f"Profile '{name}' not found in {folder_path}")
            return False

        try:
            profile_path.unlink()
            print(f"Profile '{name}' deleted successfully.")
            return True
        except Exception as e:
            print(f"Failed to delete profile '{name}': {e}")
            return False

    # ---------------- subject helpers ----------------
    def add_subject(self, subject_name, destination_root):
        """Register a subject under this profile (destination_root can be any path)."""
        self.subjects[subject_name] = str(destination_root)
        self.save()

    def remove_subject(self, subject_name):
        """Remove a subject record from the profile (does not delete filesystem)."""
        if subject_name in self.subjects:
            del self.subjects[subject_name]
            self.save()

    def list_subjects(self):
        """Return the stored subjects dict (name -> destination_root)."""
        return dict(self.subjects)

