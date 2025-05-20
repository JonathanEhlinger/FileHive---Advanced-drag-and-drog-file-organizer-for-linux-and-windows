import os
import shutil
import logging
import webbrowser
from datetime import datetime
from typing import Optional, List, Set
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QFileDialog, QPushButton,
    QTextEdit, QProgressBar, QHBoxLayout, QScrollArea, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject

import filetype  # Ensure this is installed: pip install filetype

OUTPUT_FOLDER = "organized_output"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OrganizerWorker(QThread):
    progress_update = pyqtSignal(int, int)  # processed, total
    log_update = pyqtSignal(str)
    finished = pyqtSignal(list)  # List of output folders

    def __init__(self, paths: List[str], output_folder: str):
        super().__init__()
        self.paths = paths
        self.output_folder = output_folder
        self.saved_folders: Set[str] = set()

    def run(self):
        all_files = []
        for path in self.paths:
            if os.path.isfile(path):
                all_files.append(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        src_file = os.path.join(root, file)
                        # Avoid organizing files already in the output folder
                        if os.path.commonpath([os.path.abspath(src_file), os.path.abspath(self.output_folder)]) == os.path.abspath(self.output_folder):
                            continue
                        all_files.append(src_file)
        total = len(all_files)
        for idx, file_path in enumerate(all_files, 1):
            try:
                mime = self.get_mime_type(file_path)
                ext = os.path.splitext(file_path)[1].lower().replace('.', '') or "NOEXT"
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                date_folder = mod_time.strftime("%Y-%m")
                folder_path = os.path.join(self.output_folder, ext.upper(), date_folder)
                os.makedirs(folder_path, exist_ok=True)
                # Change file name to append 'xh' before extension
                base_name, ext_dot = os.path.splitext(os.path.basename(file_path))
                new_name = f"{base_name}xh{ext_dot}"
                dest_file = os.path.join(folder_path, new_name)
                dest_file = self.get_unique_path(dest_file)
                shutil.copy2(file_path, dest_file)
                self.log_note(folder_path, file_path, mime, new_name)
                self.saved_folders.add(folder_path)
                self.log_update.emit(f"✔️ {os.path.basename(file_path)} → {folder_path} as {os.path.basename(dest_file)} [{mime}]")
            except Exception as e:
                self.log_update.emit(f"❌ Error organizing {file_path}: {e}")
            self.progress_update.emit(idx, total)
        self.finished.emit(list(self.saved_folders))

    def get_mime_type(self, path: str) -> str:
        try:
            kind = filetype.guess(path)
            if kind is not None:
                return kind.mime
            else:
                return "unknown/unknown"
        except Exception as e:
            return "unknown/unknown"

    def get_unique_path(self, path: str) -> str:
        base, ext = os.path.splitext(path)
        counter = 1
        unique_path = path
        while os.path.exists(unique_path):
            unique_path = f"{base}_{counter}{ext}"
            counter += 1
        return unique_path

    def log_note(self, folder: str, path: str, mime_type: str, new_name: str) -> None:
        note_file = os.path.join(folder, "organization_note.txt")
        with open(note_file, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()} - Moved {os.path.basename(path)} as {new_name} [{mime_type}]\n")

class FileHive(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FileHive - Smart File Organizer")
        self.resize(700, 500)
        self.setAcceptDrops(True)

        self.label = QLabel("👉 Drag files or folders here to organize\n\n🎯 They’ll be auto-sorted into folders and renamed with 'xh'.", self)
        self.label.setAlignment(Qt.AlignCenter)

        self.button = QPushButton("📁 Choose a folder manually")
        self.button.clicked.connect(self.select_folder)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setVisible(False)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMinimumHeight(120)

        self.summary_label = QLabel("📂 Output folders will be shown here after organization.")
        self.summary_label.setWordWrap(True)
        self.summary_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.summary_label.setOpenExternalLinks(True)
        self.summary_label.setStyleSheet("QLabel { background: #f0f0f0; border: 1px solid #ccc; padding: 8px; }")

        # Add credits/footer label
        self.credits_label = QLabel("GUI made by Jonathan Ehlinger, free to use")
        self.credits_label.setAlignment(Qt.AlignRight)
        self.credits_label.setStyleSheet("color: #888; font-size: 10pt; padding: 4px;")

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        layout.addWidget(self.progress)
        layout.addWidget(QLabel("📝 Actions & Log:"))
        layout.addWidget(self.log_view)
        layout.addWidget(QLabel("📂 Output Folders:"))
        layout.addWidget(self.summary_label)
        layout.addWidget(self.credits_label)  # Add credits at the bottom
        self.setLayout(layout)

        self.worker = None

    def select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.check_and_start_organizing([folder])

    def dragEnterEvent(self, event) -> None:
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:
        paths = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path) or os.path.isdir(path):
                paths.append(path)
        if paths:
            self.check_and_start_organizing(paths)

    def check_and_start_organizing(self, paths: List[str]) -> None:
        """Check for files already ending with 'xh' and prompt user if needed."""
        files_with_xh = self.find_files_with_xh(paths)
        if files_with_xh:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Question)
            msg.setWindowTitle("Files Already Modified")
            msg.setText(
                f"{len(files_with_xh)} file(s) already have 'xh' at the end of their name.\n"
                "Do you want to reorganize them again?"
            )
            msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            ret = msg.exec_()
            if ret == QMessageBox.No:
                self.show_last_locations(files_with_xh)
                return
        self.start_organizing(paths)

    def find_files_with_xh(self, paths: List[str]) -> List[str]:
        """Recursively find files with 'xh' at the end of their base name."""
        result = []
        for path in paths:
            if os.path.isfile(path):
                base, ext = os.path.splitext(os.path.basename(path))
                if base.endswith("xh"):
                    result.append(path)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        base, ext = os.path.splitext(file)
                        if base.endswith("xh"):
                            result.append(os.path.join(root, file))
        return result

    def show_last_locations(self, files: List[str]) -> None:
        """Show the last known locations and logs for the given files."""
        log_messages = []
        for file_path in files:
            base_name = os.path.basename(file_path)
            found_logs = self.search_logs_for_file(base_name)
            if found_logs:
                log_messages.append(f"<b>{base_name}</b>:<br>" + "<br>".join(found_logs))
            else:
                log_messages.append(f"<b>{base_name}</b>: No previous log found.")
        self.summary_label.setText(
            "🕑 <b>Last known locations and logs for selected files:</b><br><br>" +
            "<br><br>".join(log_messages)
        )
        self.log_view.append("ℹ️ Skipped reorganization for files already ending with 'xh'.")

    def search_logs_for_file(self, filename: str) -> List[str]:
        """Search all organization_note.txt files for entries about the given filename."""
        found_logs = []
        for root, dirs, files in os.walk(OUTPUT_FOLDER):
            if "organization_note.txt" in files:
                note_path = os.path.join(root, "organization_note.txt")
                try:
                    with open(note_path, "r", encoding="utf-8") as f:
                        for line in f:
                            if filename in line:
                                found_logs.append(f"{root}: {line.strip()}")
                except Exception:
                    continue
        return found_logs

    def start_organizing(self, paths: List[str]) -> None:
        self.log_view.append(f"🔄 Starting organization of {len(paths)} item(s)...")
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.button.setEnabled(False)
        self.setAcceptDrops(False)
        self.summary_label.setText("📂 Organizing... Please wait.")
        self.worker = OrganizerWorker(paths, OUTPUT_FOLDER)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.log_update.connect(self.append_log)
        self.worker.finished.connect(self.finish_organizing)
        self.worker.start()

    def update_progress(self, processed: int, total: int) -> None:
        self.progress.setMaximum(total)
        self.progress.setValue(processed)

    def append_log(self, message: str) -> None:
        self.log_view.append(message)

    def finish_organizing(self, folders: List[str]) -> None:
        self.log_view.append("✅ Organization complete.")
        self.progress.setVisible(False)
        self.button.setEnabled(True)
        self.setAcceptDrops(True)
        if folders:
            folder_links = []
            for folder in sorted(folders):
                url = f"file:///{os.path.abspath(folder).replace(os.sep, '/')}"
                folder_links.append(f'<a href="{url}">{folder}</a>')
            self.summary_label.setText(
                "📂 <b>Files were saved in the following folders (click to open):</b><br>" +
                "<br>".join(folder_links)
            )
        else:
            self.summary_label.setText("No files were organized.")

if __name__ == "__main__":
    app = QApplication([])
    window = FileHive()
    window.show()
    app.exec_()
