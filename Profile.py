from pathlib import Path
import json

# -------------------- PROFILE CLASS --------------------
class Profile:
    def __init__(self, name, rules=None, notes="", subjects=None, allow_subsubjects=False):
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
        # subjects: { subject_name: destination_path OR { pass_name: pass_path, ... } }
        self.subjects = subjects or {}
        self.allow_subsubjects = allow_subsubjects

    # ------------------ SAVE / LOAD ------------------
    def save(self, folder="profiles"):
        script_folder = Path(__file__).parent
        folder_path = script_folder / folder
        folder_path.mkdir(parents=True, exist_ok=True)

        profile_path = folder_path / f"{self.name}.json"
        data = {
            "name": self.name,
            "rules": self.rules,
            "notes": self.notes,
            "subjects": self.subjects,
            "allow_subsubjects": self.allow_subsubjects
        }
        with open(profile_path, "w") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Profile '{self.name}' saved to {profile_path}")

    @classmethod
    def load(cls, name, folder="profiles"):
        script_folder = Path(__file__).parent
        folder_path = script_folder / folder
        profile_path = folder_path / f"{name}.json"
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile '{name}' not found in {folder_path}")
        with open(profile_path, "r") as f:
            data = json.load(f)
        return cls(
            name=data.get("name"),
            rules=data.get("rules"),
            notes=data.get("notes", ""),
            subjects=data.get("subjects", {}),
            allow_subsubjects=data.get("allow_subsubjects", False)
        )

    # ------------------ LIST / CREATE / DELETE ------------------
    @staticmethod
    def list_profiles(folder="profiles"):
        script_folder = Path(__file__).parent
        folder_path = script_folder / folder
        if not folder_path.exists():
            return []
        return [p.stem for p in folder_path.glob("*.json")]

    @staticmethod
    def create_profile_interactively():
        # minimal interactive creation to avoid breaking callers
        name = input("Enter profile name: ").strip()
        use_default = input("Use default rules? (y/n): ").strip().lower() == "y"
        notes = input("Notes (optional): ").strip()
        allow_subs = input("Allow subsubjects/passes? (y/n): ").strip().lower() == "y"
        rules = None
        if not use_default:
            rules = {}
            print("Enter category and extensions (type 'done' to finish):")
            while True:
                cat = input("Category (or 'done'): ").strip()
                if cat.lower() == "done":
                    break
                exts = input("Extensions (comma separated, include dot): ").strip()
                rules[cat] = [e.strip() for e in exts.split(",") if e.strip()]
        profile = Profile(name=name, rules=rules, notes=notes, allow_subsubjects=allow_subs)
        profile.save()
        return profile

    @staticmethod
    def delete_profile(name, folder="profiles"):
        script_folder = Path(__file__).parent
        folder_path = script_folder / folder
        profile_path = folder_path / f"{name}.json"
        if profile_path.exists():
            profile_path.unlink()
            print(f"✅ Profile '{name}' deleted.")
            return True
        print(f"Profile '{name}' not found.")
        return False

    # ------------------ SUBJECT MANAGEMENT ------------------
    def add_subject(self, subject_name, destination_path, pass_name=None):
        """Register a subject under this profile.
        destination_path should be the full path to the subject (or pass) folder.
        If allow_subsubjects is True, stored value is a dict of passes.
        """
        dest_str = str(destination_path)
        if self.allow_subsubjects:
            entry = self.subjects.get(subject_name)
            if not isinstance(entry, dict):
                entry = {}
            if not pass_name:
                # if no pass name provided, try to derive one (caller should normally provide)
                # fallback: use pass001 if none present
                pass_name = "pass001"
                if entry:
                    nums = [int(k[4:]) for k in entry.keys() if k.lower().startswith("pass") and k[4:].isdigit()]
                    if nums:
                        pass_name = f"pass{max(nums)+1:03d}"
            entry[pass_name] = dest_str
            self.subjects[subject_name] = entry
        else:
            # single destination stored as string
            self.subjects[subject_name] = dest_str
        self.save()

    def remove_subject(self, subject_name, pass_name=None):
        if self.allow_subsubjects and pass_name:
            entry = self.subjects.get(subject_name)
            if isinstance(entry, dict) and pass_name in entry:
                del entry[pass_name]
                if not entry:
                    del self.subjects[subject_name]
                else:
                    self.subjects[subject_name] = entry
        elif subject_name in self.subjects:
            del self.subjects[subject_name]
        self.save()

    def list_subjects(self):
        return dict(self.subjects)

    def show_subjects(self):
        """Display all subjects and passes related to this profile."""
        if not self.subjects:
            print(f"No subjects registered for profile '{self.name}'.")
            return
        print(f"\n=== Subjects for Profile: {self.name} ===")
        for subj, entry in self.subjects.items():
            if self.allow_subsubjects and isinstance(entry, dict):
                print(f" - {subj}:")
                for p, path in entry.items():
                    print(f"    • {p} -> {path}")
            else:
                print(f" - {subj} -> {entry}")
        print("=========================================\n")

