import sys
import shutil
import traceback
from pathlib import Path
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit,
    QComboBox, QCheckBox, QListWidget, QListWidgetItem
)

# --- Backend imports (must exist in same folder) ---
from Profile import Profile
from Subject import Subject
from PipelineOrganizer import PipelineOrganizer


# -------------------- CREATE PROFILE DIALOG --------------------
class CreateProfileDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Create New Profile")
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)

        layout.addWidget(QLabel("Profile Name:"))
        self.name_input = QLineEdit()
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Notes (optional):"))
        self.notes_input = QTextEdit()
        self.notes_input.setFixedHeight(80)
        layout.addWidget(self.notes_input)

        self.allow_subs = QCheckBox("Allow sub-subjects (passes)")
        layout.addWidget(self.allow_subs)

        # --- Radio buttons ---
        radio_row = QHBoxLayout()
        radio_row.addWidget(QLabel("Use default rules?"))
        self.use_default_yes = QtWidgets.QRadioButton("Yes")
        self.use_default_no = QtWidgets.QRadioButton("No")
        self.use_default_yes.setChecked(True)
        radio_row.addWidget(self.use_default_yes)
        radio_row.addWidget(self.use_default_no)
        radio_row.addStretch()
        layout.addLayout(radio_row)

        # --- Default Rules ---
        self.default_rules_view = QTextEdit()
        self.default_rules_view.setReadOnly(True)
        self.default_rules_view.setFixedHeight(140)
        self.default_rules_view.setPlainText(self._format_rules(Profile.DEFAULT_RULES))
        layout.addWidget(QLabel("Default rules (read-only):"))
        layout.addWidget(self.default_rules_view)

        # --- Custom rules area ---
        self.custom_rules_widget = QWidget()
        self.custom_rules_layout = QVBoxLayout(self.custom_rules_widget)
        self.custom_rules_list = QListWidget()
        self.custom_rules_layout.addWidget(self.custom_rules_list)

        add_row = QHBoxLayout()
        self.cat_input = QLineEdit()
        self.cat_input.setPlaceholderText("Category (e.g. Videos)")
        self.ext_input = QLineEdit()
        self.ext_input.setPlaceholderText("Extensions (e.g. .mp4,.mov)")
        self.add_rule_btn = QPushButton("Add Rule")
        add_row.addWidget(self.cat_input)
        add_row.addWidget(self.ext_input)
        add_row.addWidget(self.add_rule_btn)
        self.custom_rules_layout.addLayout(add_row)

        self.remove_rule_btn = QPushButton("Remove Selected Rule")
        self.custom_rules_layout.addWidget(self.remove_rule_btn)
        layout.addWidget(self.custom_rules_widget)
        self.custom_rules_widget.setVisible(False)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        self.create_btn = QPushButton("Create Profile")
        self.cancel_btn = QPushButton("Cancel")
        btn_row.addStretch()
        btn_row.addWidget(self.create_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        # --- Connections ---
        self.use_default_yes.toggled.connect(self._toggle_custom_form)
        self.add_rule_btn.clicked.connect(self._add_custom_rule)
        self.remove_rule_btn.clicked.connect(self._remove_custom_rule)
        self.create_btn.clicked.connect(self._on_create)
        self.cancel_btn.clicked.connect(self.reject)

    def _format_rules(self, rules):
        return "\n".join(f"{k}: {', '.join(v)}" for k, v in rules.items())

    def _toggle_custom_form(self, checked):
        self.custom_rules_widget.setVisible(not checked)
        self.default_rules_view.setVisible(checked)

    def _add_custom_rule(self):
        cat = self.cat_input.text().strip()
        exts = self.ext_input.text().strip()
        if not cat or not exts:
            QMessageBox.warning(self, "Invalid", "Please enter category and extensions.")
            return
        self.custom_rules_list.addItem(f"{cat} -> {exts}")
        self.cat_input.clear()
        self.ext_input.clear()

    def _remove_custom_rule(self):
        for it in self.custom_rules_list.selectedItems():
            self.custom_rules_list.takeItem(self.custom_rules_list.row(it))

    def _on_create(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Missing name", "Please enter a profile name.")
            return

        notes = self.notes_input.toPlainText().strip()
        allow_subs = self.allow_subs.isChecked()

        if self.use_default_yes.isChecked():
            rules = Profile.DEFAULT_RULES
        else:
            rules = {}
            for i in range(self.custom_rules_list.count()):
                txt = self.custom_rules_list.item(i).text()
                if "->" in txt:
                    cat, exts = txt.split("->", 1)
                    cat = cat.strip()
                    exts = [e.strip() if e.startswith('.') else f".{e.strip()}"
                            for e in exts.split(",") if e.strip()]
                    rules[cat] = exts
            if not rules:
                QMessageBox.warning(self, "No rules", "Add at least one custom rule.")
                return

        prof = Profile(name, rules=rules, notes=notes, subjects={}, allow_subsubjects=allow_subs)
        prof.save()
        self.created_profile = prof
        self.accept()


# -------------------- MAIN GUI --------------------
class PipelineGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Organizer Tool")
        self.setMinimumSize(900, 750)
        self.current_profile = None

        # Layout
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # --- Profile Row ---
        row = QHBoxLayout()
        layout.addLayout(row)
        row.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        row.addWidget(self.profile_combo)
        self.new_profile_btn = QPushButton("Create New Profile")
        self.delete_profile_btn = QPushButton("Delete Profile")
        row.addWidget(self.new_profile_btn)
        row.addWidget(self.delete_profile_btn)
        row.addStretch()

        # --- Notes ---
        self.profile_notes = QTextEdit()
        self.profile_notes.setReadOnly(True)
        self.profile_notes.setFixedHeight(20)
        layout.addWidget(QLabel("Profile Notes:"))
        layout.addWidget(self.profile_notes)

        # --- Subjects List ---
        layout.addWidget(QLabel("Subjects in this Profile:"))
        self.subjects_list = QListWidget()
        self.subjects_list.setFixedHeight(120)
        layout.addWidget(self.subjects_list)
        
        subj_btn_row = QHBoxLayout()
        self.delete_subject_btn = QPushButton("Delete Selected Subject")
        subj_btn_row.addWidget(self.delete_subject_btn)
        subj_btn_row.addStretch()
        layout.addLayout(subj_btn_row)

        # --- Source / Destination ---
        mid = QHBoxLayout()
        layout.addLayout(mid)

        src_layout = QVBoxLayout()
        mid.addLayout(src_layout)
        src_layout.addWidget(QLabel("Source Folder"))
        srow = QHBoxLayout()
        self.src_input = QLineEdit()
        self.src_browse = QPushButton("Browse")
        srow.addWidget(self.src_input)
        srow.addWidget(self.src_browse)
        src_layout.addLayout(srow)

        dst_layout = QVBoxLayout()
        mid.addLayout(dst_layout)
        dst_layout.addWidget(QLabel("Destination Root"))
        drow = QHBoxLayout()
        self.dst_input = QLineEdit()
        self.dst_browse = QPushButton("Browse")
        drow.addWidget(self.dst_input)
        drow.addWidget(self.dst_browse)
        dst_layout.addLayout(drow)

        # --- Subject Name ---
        subj_row = QHBoxLayout()
        layout.addLayout(subj_row)
        subj_row.addWidget(QLabel("Subject / Project Name:"))
        self.subj_input = QLineEdit()
        subj_row.addWidget(self.subj_input)
        subj_row.addStretch()

        # --- Options ---
        opt_row = QHBoxLayout()
        layout.addLayout(opt_row)
        self.move_checkbox = QCheckBox("Move files instead of copying")
        opt_row.addWidget(self.move_checkbox)
        opt_row.addStretch()

        # --- Actions ---
        actions = QHBoxLayout()
        layout.addLayout(actions)
        self.start_btn = QPushButton("Start Organizing")
        actions.addWidget(self.start_btn)

        # --- Log ---
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        # --- Summary ---
        sum_row = QHBoxLayout()
        layout.addLayout(sum_row)
        self.summary_btn = QPushButton("Show Summary")
        sum_row.addWidget(self.summary_btn)
        sum_row.addStretch()

        # Connections
        self.new_profile_btn.clicked.connect(self.create_profile)
        self.delete_profile_btn.clicked.connect(self.delete_profile)
        self.delete_subject_btn.clicked.connect(self.delete_subject)
        self.src_browse.clicked.connect(self.browse_source)
        self.dst_browse.clicked.connect(self.browse_destination)
        self.start_btn.clicked.connect(self.start_organize)
        self.summary_btn.clicked.connect(self.show_summary)
        self.profile_combo.currentTextChanged.connect(self.on_profile_selected)

        self.refresh_profiles()

    # --- Helpers ---
    def log_msg(self, text):
        self.log.append(text)

    def refresh_profiles(self):
        self.profile_combo.clear()
        profiles = Profile.list_profiles()
        if profiles:
            self.profile_combo.addItems(profiles)
            self.load_profile(profiles[0])
        else:
            self.profile_notes.setPlainText("No profiles found. Create one!")

    def load_profile(self, name):
        try:
            prof = Profile.load(name)
            self.current_profile = prof
            self.profile_notes.setPlainText(prof.notes or "")
            self.refresh_subjects_list()
            self.log_msg(f"Loaded profile: {name}")
        except Exception as e:
            self.log_msg(f"Failed to load profile {name}: {e}")

    def refresh_subjects_list(self):
        """Refresh the subjects list widget based on current profile."""
        self.subjects_list.clear()
        if not self.current_profile:
            return
        
        subjects = self.current_profile.list_subjects()
        for subj_name, entry in subjects.items():
            if self.current_profile.allow_subsubjects and isinstance(entry, dict):
                # Show subject with passes
                for pass_name, path in entry.items():
                    item_text = f"{subj_name} / {pass_name}"
                    item = QListWidgetItem(item_text)
                    item.setData(QtCore.Qt.UserRole, (subj_name, pass_name))
                    self.subjects_list.addItem(item)
            else:
                # Show subject without passes
                item = QListWidgetItem(subj_name)
                item.setData(QtCore.Qt.UserRole, (subj_name, None))
                self.subjects_list.addItem(item)

    def on_profile_selected(self, name):
        if name:
            self.load_profile(name)

    def create_profile(self):
        dlg = CreateProfileDialog(self)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            self.refresh_profiles()
            prof = dlg.created_profile
            idx = self.profile_combo.findText(prof.name)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)
            self.log_msg(f"Profile '{prof.name}' created.")

    def delete_profile(self):
        name = self.profile_combo.currentText()
        if not name:
            QMessageBox.warning(self, "No profile", "No profile selected.")
            return
        reply = QMessageBox.question(self, "Confirm Delete", f"Delete profile '{name}'?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            Profile.delete_profile(name)
            self.refresh_profiles()
            self.log_msg(f"Profile '{name}' deleted.")

    def delete_subject(self):
        """Delete the selected subject (or pass) from disk and from the profile."""
        selected = self.subjects_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "No selection", "Please select a subject to delete.")
            return

        item = selected[0]
        subj_name, pass_name = item.data(QtCore.Qt.UserRole)

        item_text = item.text()
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Delete '{item_text}'? This will remove the folder from disk.",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Determine destination_root based on stored path format
                subjects_map = self.current_profile.subjects
                if self.current_profile.allow_subsubjects and isinstance(subjects_map.get(subj_name), dict) and pass_name:
                    # stored pass path is the full pass folder: <destination_root>/<subject>/<passNNN>
                    pass_path = Path(subjects_map[subj_name].get(pass_name))
                    destination_root = pass_path.parents[1] if len(pass_path.parents) >= 2 else pass_path.parent
                else:
                    # stored entry is full subject folder: <destination_root>/<subject>
                    entry = subjects_map.get(subj_name)
                    subj_path = Path(entry)
                    destination_root = subj_path.parent

                # Use Subject.delete() to remove folder from disk
                subject = Subject(subj_name, str(destination_root), self.current_profile, pass_name)
                subject.delete()

                # Remove metadata from profile
                self.current_profile.remove_subject(subj_name, pass_name)
                self.refresh_subjects_list()
                self.log_msg(f"Subject '{item_text}' deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete subject: {str(e)}")
                self.log_msg(f"Error deleting subject: {e}")

    def browse_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.src_input.setText(folder)

    def browse_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Root")
        if folder:
            self.dst_input.setText(folder)

    def start_organize(self):
        try:
            if not self.current_profile:
                QMessageBox.warning(self, "No Profile", "Please select or create a profile first.")
                return

            source = Path(self.src_input.text().strip())
            dest_root = Path(self.dst_input.text().strip())
            subj_name = self.subj_input.text().strip()
            if not source.exists():
                QMessageBox.warning(self, "Error", "Source folder not found.")
                return
            if not dest_root.exists():
                dest_root.mkdir(parents=True, exist_ok=True)
            if not subj_name:
                QMessageBox.warning(self, "Missing name", "Enter subject/project name.")
                return

            organizer = PipelineOrganizer(self.current_profile)
            subject = organizer.create_subject(subj_name, str(dest_root), pass_name=None)
            move_files = self.move_checkbox.isChecked()

            ok = organizer.organize_to_subject(
                str(source),
                subject,
                copy_function=(shutil.move if move_files else shutil.copy2)
            )

            if ok:
                self.refresh_subjects_list()
                self.log_msg("✅ Organization complete.")
            else:
                self.log_msg("⚠️ Organization finished with issues.")

        except Exception as e:
            self.log_msg(traceback.format_exc())
            QMessageBox.critical(self, "Error", str(e))

    def show_summary(self):
        try:
            if not self.current_profile:
                QMessageBox.warning(self, "No profile", "Please select a profile first.")
                return
            subjects = self.current_profile.list_subjects()
            summary_text = f"Profile: {self.current_profile.name}\n\nSubjects:\n"
            for subj, entry in subjects.items():
                if self.current_profile.allow_subsubjects and isinstance(entry, dict):
                    summary_text += f"\n{subj}:\n"
                    for pass_name, path in entry.items():
                        summary_text += f"  • {pass_name}: {path}\n"
                else:
                    summary_text += f"\n{subj}: {entry}\n"
            self.log_msg(summary_text)
        except Exception as e:
            self.log_msg(f"Error: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = PipelineGUI()
    gui.show()
    sys.exit(app.exec())
