# Folder Organizer / Pipeline Organizer

A small tool to organize files into project "subjects" using configurable profiles.  
Profiles define categories (file extensions → folders) and track projects (subjects) and their storage locations. The app supports an optional per-subject pass/version folder (auto-incremented pass001, pass002, ...). Use via a simple GUI (PySide6) or a minimal CLI.

## Key features
- Create / delete Profiles (rules, notes, allow passes)
- Create / delete Subjects (projects) for a Profile
- Auto-incremented "pass" folders per subject (when enabled)
- Copy or move files from a source folder into categorized destination subfolders
- Persist profiles and subject metadata as JSON in the `profiles` folder

