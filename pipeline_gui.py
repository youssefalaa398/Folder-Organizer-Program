

import sys
import traceback
from pathlib import Path
from PySide6 import QtWidgets, QtCore
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit, QTextEdit, QComboBox, QCheckBox, QSpinBox
)

# Attempt to import your backend modules. Adjust if packaged differently.
try:
    from Profile import Profile
    from Subject import Subject
    from PipelineOrganizer import PipelineOrganizer
except Exception:
    # Allow running the GUI while backend module is named differently.
    # The user should ensure these modules are on PYTHONPATH.
    PipelineOrganizer = None
    Profile = None
    Subject = None


class WorkerSignals(QtCore.QObject):
    finished = QtCore.Signal()
    error = QtCore.Signal(str)
    progress = QtCore.Signal(str)
    result = QtCore.Signal(object)


class OrganizeWorker(QtCore.QRunnable):
    def __init__(self, organizer, source, subject, move_files=False):
        super().__init__()
        self.organizer = organizer
        self.source = source
        self.subject = subject
        self.move_files = move_files
        self.signals = WorkerSignals()

    @QtCore.Slot()
    def run(self):
        try:
            copy_func = None
            import shutil
            copy_func = shutil.move if self.move_files else shutil.copy2
            self.signals.progress.emit(f"Starting organization from {self.source} to {self.subject.destination_path}")
            ok = self.organizer.organize_to_subject(self.source, self.subject, copy_function=copy_func)
            if not ok:
                self.signals.error.emit("Organization failed. See console for details.")
                return
            self.signals.progress.emit("Organization finished. Generating summary...")
            self.signals.result.emit(True)
        except Exception as e:
            tb = traceback.format_exc()
            self.signals.error.emit(f"Exception: {e}\n{tb}")
        finally:
            self.signals.finished.emit()


class PipelineGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pipeline Organizer — GUI")
        self.setMinimumSize(800, 600)

        self.threadpool = QtCore.QThreadPool()

        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.layout = QVBoxLayout(self.central)

        # Top row: Profile controls
        row = QHBoxLayout()
        self.layout.addLayout(row)

        row.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        row.addWidget(self.profile_combo)
        self.refresh_profiles_btn = QPushButton("Refresh")
        row.addWidget(self.refresh_profiles_btn)
        self.new_profile_btn = QPushButton("Create New Profile")
        row.addWidget(self.new_profile_btn)

        # Profile notes
        self.profile_notes = QLineEdit()
        self.profile_notes.setPlaceholderText("Profile notes (read only until saved)")
        self.layout.addWidget(self.profile_notes)

        # Middle: source, destination
        mid = QHBoxLayout()
        self.layout.addLayout(mid)

        # Source
        src_layout = QVBoxLayout()
        mid.addLayout(src_layout)
        src_layout.addWidget(QLabel("Source folder"))
        srow = QHBoxLayout()
        self.src_input = QLineEdit()
        srow.addWidget(self.src_input)
        self.src_browse = QPushButton("Browse")
        srow.addWidget(self.src_browse)
        src_layout.addLayout(srow)

        # Destination root
        dst_layout = QVBoxLayout()
        mid.addLayout(dst_layout)
        dst_layout.addWidget(QLabel("Destination root"))
        drow = QHBoxLayout()
        self.dst_input = QLineEdit()
        drow.addWidget(self.dst_input)
        self.dst_browse = QPushButton("Browse")
        drow.addWidget(self.dst_browse)
        dst_layout.addLayout(drow)

        # Subject name and pass
        subj_row = QHBoxLayout()
        self.layout.addLayout(subj_row)
        subj_row.addWidget(QLabel("Subject / Project name:"))
        self.subj_input = QLineEdit()
        subj_row.addWidget(self.subj_input)
        subj_row.addWidget(QLabel("Pass (optional):"))
        self.pass_input = QLineEdit()
        subj_row.addWidget(self.pass_input)

        # Options row
        opt_row = QHBoxLayout()
        self.layout.addLayout(opt_row)
        self.move_checkbox = QCheckBox("Move files instead of copying")
        opt_row.addWidget(self.move_checkbox)
        opt_row.addStretch()

        # Actions
        actions = QHBoxLayout()
        self.layout.addLayout(actions)
        self.start_btn = QPushButton("Start Organizing")
        actions.addWidget(self.start_btn)
        self.open_dest_btn = QPushButton("Open Destination")
        actions.addWidget(self.open_dest_btn)

        # Log area
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.layout.addWidget(self.log)

        # Summary button
        sumrow = QHBoxLayout()
        self.layout.addLayout(sumrow)
        self.summary_btn = QPushButton("Show Summary")
        sumrow.addWidget(self.summary_btn)
        sumrow.addStretch()

        # Wire events
        self.refresh_profiles_btn.clicked.connect(self.refresh_profiles)
        self.new_profile_btn.clicked.connect(self.create_profile_dialog)
        self.src_browse.clicked.connect(self.browse_source)
        self.dst_browse.clicked.connect(self.browse_destination)
        self.start_btn.clicked.connect(self.start_organize)
        self.open_dest_btn.clicked.connect(self.open_destination)
        self.summary_btn.clicked.connect(self.show_summary)

        # initial load
        self.refresh_profiles()

    # ---------- helpers ----------
    def log_msg(self, text):
        self.log.append(text)

    def refresh_profiles(self):
        self.profile_combo.clear()
        try:
            profiles = Profile.list_profiles()
        except Exception:
            profiles = []
        self.profile_combo.addItems(profiles)
        if profiles:
            self.load_profile(profiles[0])

    def load_profile(self, name):
        try:
            prof = Profile.load(name)
            self.current_profile = prof
            self.profile_notes.setText(prof.notes or "")
            self.log_msg(f"Loaded profile: {name}")
        except Exception as e:
            self.log_msg(f"Failed to load profile {name}: {e}")

    def create_profile_dialog(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Create Profile", "Profile name:")
        if not ok or not name.strip():
            return
        use_default = QMessageBox.question(self, "Use default rules?", "Use default rules? (Yes=yes)")
        # keep it simple: use defaults always for now
        prof = Profile(name.strip())
        prof.save()
        self.log_msg(f"Created profile: {prof.name}")
        self.refresh_profiles()

    def browse_source(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if folder:
            self.src_input.setText(folder)

    def browse_destination(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Destination Root")
        if folder:
            self.dst_input.setText(folder)

    def start_organize(self):
        # validate
        try:
            prof_name = self.profile_combo.currentText()
            if not prof_name:
                QMessageBox.warning(self, "Profile missing", "Please select or create a profile first.")
                return
            profile = Profile.load(prof_name)
            organizer = PipelineOrganizer(profile)

            source = Path(self.src_input.text().strip())
            if not source.exists():
                QMessageBox.warning(self, "Source missing", "Source folder does not exist.")
                return

            destination_root = Path(self.dst_input.text().strip())
            if not destination_root.exists():
                create = QMessageBox.question(self, "Create destination?", "Destination does not exist. Create it? (Yes)")
                destination_root.mkdir(parents=True, exist_ok=True)

            subj_name = self.subj_input.text().strip()
            if not subj_name:
                QMessageBox.warning(self, "Subject missing", "Please enter a subject/project name.")
                return

            pass_name = self.pass_input.text().strip() or None
            subject = organizer.create_subject(subj_name, str(destination_root), pass_name)

            move_files = self.move_checkbox.isChecked()

            worker = OrganizeWorker(organizer, str(source), subject, move_files=move_files)
            worker.signals.progress.connect(lambda t: self.log_msg(t))
            worker.signals.error.connect(lambda t: self.log_msg(f"❌ {t}"))
            worker.signals.result.connect(lambda r: self.log_msg("✅ Done"))
            worker.signals.finished.connect(lambda: self.log_msg("Worker finished."))

            self.threadpool.start(worker)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.log_msg(traceback.format_exc())

    def open_destination(self):
        # open the destination folder in file manager
        try:
            prof_name = self.profile_combo.currentText()
            profile = Profile.load(prof_name)
            # open profile folder
            folder = Path.cwd() / "profiles"
            QtGui = None
            from PySide6 import QtGui
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(str(folder)))
        except Exception as e:
            self.log_msg(f"Could not open destination: {e}")

    def show_summary(self):
        try:
            prof_name = self.profile_combo.currentText()
            profile = Profile.load(prof_name)
            organizer = PipelineOrganizer(profile)
            # attempt to show subjects
            profile.show_subjects()
            self.log_msg("(Also printed profile subjects to console)")
        except Exception as e:
            self.log_msg(f"Error showing summary: {e}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    gui = PipelineGUI()
    gui.show()
    sys.exit(app.exec())
