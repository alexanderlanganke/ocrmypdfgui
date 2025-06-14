# Cross-platform PyQt5 GUI for OCRmyPDFGui
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QProgressBar, QFileDialog, QMessageBox, QDialog, QCheckBox, QComboBox, QDialogButtonBox, QFormLayout, QGroupBox, QGridLayout, QLineEdit, QListWidget, QListWidgetItem, QAbstractItemView, QToolTip, QToolBar, QAction, QStyle, QSizePolicy, QTabWidget, QStyledItemDelegate, QCompleter, QFrame, QScrollArea, QSpacerItem
)
from PyQt5.QtGui import QIcon, QColor, QBrush, QMovie, QPalette
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
import json
import pytesseract
import collections

SETTINGS_PATH = os.path.join(os.path.expanduser('~'), '.ocrmypdfgui', 'settings.ini')
DEFAULT_SETTINGS = {
    "rotate_pages": False,
    "remove_background": False,
    "deskew": False,
    "clean": False,
    "force_ocr": False,
    "skip_text": False,
    "output_mode": "pdf",
    "new_archive_on_sidecar": True,
    "language": []
}

class SettingsDialog(QDialog):
    def __init__(self, parent=None, settings=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = settings or DEFAULT_SETTINGS.copy()
        layout = QVBoxLayout()
        form = QFormLayout()

        self.cb_rotate = QCheckBox()
        self.cb_rotate.setChecked(self.settings.get("rotate_pages", False))
        self.cb_rotate.setToolTip("Rotate pages automatically if orientation is detected.")
        form.addRow("Rotate Pages", self.cb_rotate)

        self.cb_remove_bg = QCheckBox()
        self.cb_remove_bg.setChecked(self.settings.get("remove_background", False))
        self.cb_remove_bg.setToolTip("Remove background from scanned pages to improve OCR accuracy.")
        form.addRow("Remove Background", self.cb_remove_bg)

        self.cb_deskew = QCheckBox()
        self.cb_deskew.setChecked(self.settings.get("deskew", False))
        self.cb_deskew.setToolTip("Automatically straighten (deskew) pages.")
        form.addRow("Deskew", self.cb_deskew)

        self.cb_clean = QCheckBox()
        self.cb_clean.setChecked(self.settings.get("clean", False))
        self.cb_clean.setToolTip("Remove speckles and noise from scanned images.")
        form.addRow("Clean", self.cb_clean)

        self.cb_force_ocr = QCheckBox()
        self.cb_force_ocr.setChecked(self.settings.get("force_ocr", False))
        self.cb_force_ocr.setToolTip("Force OCR on all pages, even if text is already present.")
        form.addRow("Force OCR", self.cb_force_ocr)

        self.cb_skip_text = QCheckBox()
        self.cb_skip_text.setChecked(self.settings.get("skip_text", False))
        self.cb_skip_text.setToolTip("Skip OCR on pages that already contain text.")
        form.addRow("Skip Text", self.cb_skip_text)

        self.output_mode_combo = QComboBox()
        self.output_mode_combo.addItems(["pdf", "sidecar_txt"])
        self.output_mode_combo.setCurrentText(self.settings.get("output_mode", "pdf"))
        self.output_mode_combo.setToolTip("Choose output format: PDF (searchable) or sidecar TXT (text file alongside images).")
        form.addRow("Output Mode", self.output_mode_combo)

        self.cb_new_archive = QCheckBox()
        self.cb_new_archive.setChecked(self.settings.get("new_archive_on_sidecar", True))
        self.cb_new_archive.setToolTip("Create a new archive when adding a sidecar TXT to comic book archives.")
        form.addRow("New Archive on Sidecar", self.cb_new_archive)

        # Language selection (multi-select list)
        self.language_list = QListWidget()
        self.language_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.language_list.setToolTip("Select one or more OCR languages. Hold Ctrl or Shift to multi-select.")
        try:
            langs = pytesseract.get_languages(config='')
        except Exception:
            langs = ["eng"]
        # Always load selected languages from self.settings['language'] (from settings.ini)
        selected_langs = set(self.settings.get("language", []))
        for lang in langs:
            item = QListWidgetItem(lang)
            self.language_list.addItem(item)
            if lang in selected_langs:
                item.setSelected(True)
        form.addRow("Languages", self.language_list)

        layout.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def get_settings(self):
        return {
            "rotate_pages": self.cb_rotate.isChecked(),
            "remove_background": self.cb_remove_bg.isChecked(),
            "deskew": self.cb_deskew.isChecked(),
            "clean": self.cb_clean.isChecked(),
            "force_ocr": self.cb_force_ocr.isChecked(),
            "skip_text": self.cb_skip_text.isChecked(),
            "output_mode": self.output_mode_combo.currentText(),
            "new_archive_on_sidecar": self.cb_new_archive.isChecked(),
            "language": [item.text() for item in self.language_list.selectedItems()]
        }

class OCRWorker(QThread):
    progress = pyqtSignal(int)  # Change to int for QProgressBar
    message = pyqtSignal(str, str)
    finished = pyqtSignal()

    def __init__(self, file_path, settings):
        super().__init__()
        self.file_path = file_path
        self.settings = settings

    def run(self):
        # Import here to avoid import errors if dependencies are missing
        try:
            from ocrmypdfgui.ocr import batch_ocr
            batch_ocr(self.file_path, self.emit_progress, self.emit_message, self.settings, self.emit_finished)
        except Exception as e:
            self.emit_message(f"Error: {e}", "error")
            self.emit_finished()

    def emit_progress(self, value):
        # Accepts float 0.0-1.0, emits int 0-100
        self.progress.emit(int(value * 100))

    def emit_message(self, text, type):
        self.message.emit(text, type)

    def emit_finished(self):
        self.finished.emit()

class FileCard(QFrame):
    def __init__(self, file_path, compact=True):
        super().__init__()
        self.file_path = file_path
        self.messages = []
        self.expanded = False
        self.status = 'working'  # working, success, error, skip
        self.compact = compact
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        self.layout.setSpacing(2)
        self.header = QHBoxLayout()
        self.file_label = QLabel(os.path.basename(self.file_path))
        self.file_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        self.header.addWidget(self.file_label)
        self.status_icon = QLabel()
        self.spinner = QLabel()
        # Use a modern spinner icon (fallback to a static icon if QMovie fails)
        try:
            self.spinner_movie = QMovie(":/qt-project.org/styles/commonstyle/images/qtspinner.mng")
            if not self.spinner_movie.isValid():
                raise Exception()
        except Exception:
            self.spinner_movie = QMovie()
            self.spinner.setPixmap(self.style().standardIcon(QStyle.SP_BrowserReload).pixmap(18, 18))
        self.spinner.setMovie(self.spinner_movie)
        self.spinner_movie.start()
        self.header.addWidget(self.spinner)
        self.header.addWidget(self.status_icon)
        self.header.addStretch()
        self.toggle_btn = QPushButton("Show")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False)
        self.toggle_btn.setFixedWidth(60)
        self.toggle_btn.clicked.connect(self.toggle_expand)
        self.header.addWidget(self.toggle_btn)
        self.layout.addLayout(self.header)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border-radius: 4px; font-size: 10px; }")
        self.layout.addWidget(self.progress_bar)
        self.details = QLabel()
        self.details.setWordWrap(True)
        self.details.setVisible(False)
        self.details.setStyleSheet("font-size: 10px; color: #444;")
        self.layout.addWidget(self.details)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setStyleSheet("QWidget { background: #f9f9f9; border-radius: 6px; border: 1px solid #ddd; }")
        self.update_details(initial=True)

    def add_message(self, text, type):
        self.messages.append((text, type))
        self.update_details()

    def update_details(self, initial=False):
        details = ""
        # Show file path and type at the top
        if initial or not self.messages:
            details += f'<div style="color:#1976d2;"><b>Path:</b> {self.file_path}</div>'
            ext = os.path.splitext(self.file_path)[1].lower()
            if ext:
                details += f'<div style="color:#1976d2;"><b>Type:</b> {ext[1:].upper()}</div>'
        # Show all messages (with color)
        for msg, t in self.messages:
            color = {"success": "#388e3c", "error": "#d32f2f", "skip": "#1976d2"}.get(t, "#222")
            details += f'<div style="color:{color};margin-bottom:2px;">{msg}</div>'
        self.details.setText(details)

    def toggle_expand(self):
        self.expanded = not self.expanded
        self.details.setVisible(self.expanded)
        self.toggle_btn.setText("Hide" if self.expanded else "Show")
        # Switch between compact and expanded style
        if self.expanded:
            self.file_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            self.progress_bar.setFixedHeight(16)
            self.progress_bar.setTextVisible(True)
            self.details.setStyleSheet("font-size: 12px; color: #444;")
            self.layout.setContentsMargins(8, 8, 8, 8)
            self.layout.setSpacing(4)
        else:
            self.file_label.setStyleSheet("font-weight: bold; font-size: 12px;")
            self.progress_bar.setFixedHeight(10)
            self.progress_bar.setTextVisible(False)
            self.details.setStyleSheet("font-size: 10px; color: #444;")
            self.layout.setContentsMargins(4, 4, 4, 4)
            self.layout.setSpacing(2)

    def set_status(self, status):
        self.status = status
        self.spinner.setVisible(status == 'working')
        self.status_icon.setVisible(status != 'working')
        # Use modern icons for status
        if status == 'success':
            self.status_icon.setPixmap(self.style().standardIcon(QStyle.SP_DialogApplyButton).pixmap(20, 20))
        elif status == 'error':
            self.status_icon.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxCritical).pixmap(20, 20))
        elif status == 'skip':
            self.status_icon.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(20, 20))
        else:
            self.status_icon.clear()

    def set_progress(self, value):
        self.progress_bar.setValue(value)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCRmyPDFGui")
        self.resize(1000, 650)
        self.file_path = ""
        self.ocrmypdfsettings = {}
        self.file_cards = {}
        self.workers = {}
        self.selected_files = []
        self.files_queue = []
        self.current_file_index = 0
        self.selected_path_card = None  # Card for selected path
        self.init_ui()
        self.apply_modern_palette()

    def init_ui(self):
        # Toolbar
        toolbar = QToolBar()
        toolbar.setIconSize(QSize(28, 28))
        self.addToolBar(toolbar)

        open_file_action = QAction(QIcon.fromTheme("document-open"), "Open File", self)
        open_file_action.triggered.connect(self.select_file)
        toolbar.addAction(open_file_action)

        open_folder_action = QAction(QIcon.fromTheme("folder-open"), "Open Folder", self)
        open_folder_action.triggered.connect(self.select_folder)
        toolbar.addAction(open_folder_action)

        settings_action = QAction(QIcon.fromTheme("preferences-system"), "Settings", self)
        settings_action.triggered.connect(self.open_settings)
        toolbar.addAction(settings_action)

        toolbar.addSeparator()

        start_action = QAction(QIcon.fromTheme("media-playback-start"), "Start OCR", self)
        start_action.triggered.connect(self.start_ocr)
        toolbar.addAction(start_action)
        self.start_ocr_action = start_action

        stop_action = QAction(QIcon.fromTheme("media-playback-stop"), "Stop OCR", self)
        stop_action.triggered.connect(self.stop_ocr)
        toolbar.addAction(stop_action)
        self.stop_ocr_action = stop_action
        self.stop_ocr_action.setEnabled(False)

        # Central widget
        central = QWidget()
        vlayout = QVBoxLayout()
        vlayout.setContentsMargins(16, 16, 16, 16)
        vlayout.setSpacing(12)

        # Cards area (for file processing messages)
        self.cards_area = QScrollArea()
        self.cards_area.setWidgetResizable(True)
        self.cards_area.setFrameShape(QFrame.NoFrame)
        self.cards_area.setStyleSheet("QScrollArea { background: #f5f5f5; border: none; }")
        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(8, 8, 8, 8)
        self.cards_layout.setSpacing(12)
        self.cards_area.setWidget(self.cards_widget)
        vlayout.addWidget(self.cards_area, stretch=2)

        # Status bar area: replace status_label with a FileCard for the selected path
        self.status_layout = QVBoxLayout()
        self.status_layout.setContentsMargins(0, 0, 0, 0)
        self.status_layout.setSpacing(0)
        self.status_widget = QWidget()
        self.status_widget.setLayout(self.status_layout)
        self.selected_path_card = DirectoryCard("No file or folder selected")
        self.status_layout.addWidget(self.selected_path_card)
        vlayout.addWidget(self.status_widget)

        central.setLayout(vlayout)
        self.setCentralWidget(central)

    def apply_modern_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#f7f7f7"))
        palette.setColor(QPalette.Base, QColor("#fff"))
        palette.setColor(QPalette.Text, QColor("#222"))
        palette.setColor(QPalette.Button, QColor("#f7f7f7"))
        palette.setColor(QPalette.ButtonText, QColor("#222"))
        palette.setColor(QPalette.Highlight, QColor("#1976d2"))
        palette.setColor(QPalette.HighlightedText, QColor("#fff"))
        self.setPalette(palette)

    def update_selected_path_card(self, path):
        if self.selected_path_card:
            self.selected_path_card.setParent(None)
        if os.path.isdir(path):
            label = path
        elif os.path.isfile(path):
            label = os.path.basename(path)
        else:
            label = "No file or folder selected"
        self.selected_path_card = DirectoryCard(label)
        self.status_layout.addWidget(self.selected_path_card)

    def select_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select File", "", "PDF/CBZ/CBR Files (*.pdf *.cbz *.cbr)")
        if fname:
            self.file_path = fname
            self.selected_files = [fname]
            self.update_selected_path_card(fname)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.file_path = folder
            self.update_selected_path_card(folder)
            # Recursively list all supported files in the directory and subdirectories
            self.selected_files = []
            for root, _, files in os.walk(folder):
                for fname in files:
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in ['.pdf', '.cbz', '.cbr']:
                        self.selected_files.append(os.path.join(root, fname))
        else:
            self.selected_files = []
            self.update_selected_path_card("")

    def open_settings(self):
        # Load settings from file if exists
        settings = DEFAULT_SETTINGS.copy()
        try:
            if os.path.exists(SETTINGS_PATH):
                with open(SETTINGS_PATH, 'r') as f:
                    settings.update(json.load(f))
        except Exception as e:
            pass
        dlg = SettingsDialog(self, settings)
        if dlg.exec_() == QDialog.Accepted:
            new_settings = dlg.get_settings()
            # Save to file
            try:
                os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
                with open(SETTINGS_PATH, 'w') as f:
                    json.dump(new_settings, f, indent=2)
            except Exception as e:
                pass
            self.ocrmypdfsettings = new_settings

    def start_ocr(self):
        for card in self.file_cards.values():
            card.setParent(None)
        self.file_cards.clear()
        self.workers.clear()
        # Only process files, not the selected directory itself
        files_to_process = []
        if hasattr(self, 'selected_files') and self.selected_files:
            files_to_process = self.selected_files.copy()
        elif self.file_path and os.path.isfile(self.file_path):
            files_to_process = [self.file_path]
        elif self.file_path and os.path.isdir(self.file_path):
            files_to_process = [os.path.join(self.file_path, f) for f in os.listdir(self.file_path)
                                if os.path.splitext(f)[1].lower() in ['.pdf', '.cbz', '.cbr']]
        else:
            QMessageBox.warning(self, "No file/folder selected", "Please select a file or folder first.")
            return
        if not files_to_process:
            QMessageBox.warning(self, "No supported files", "No PDF, CBZ, or CBR files found in the selected folder.")
            return
        self.ocrmypdfsettings = DEFAULT_SETTINGS.copy()
        try:
            if os.path.exists(SETTINGS_PATH):
                with open(SETTINGS_PATH, 'r') as f:
                    self.ocrmypdfsettings.update(json.load(f))
        except Exception:
            pass
        # Ensure language is passed as a string for ocrmypdf
        if self.ocrmypdfsettings.get('language'):
            langs = self.ocrmypdfsettings['language']
            if isinstance(langs, list):
                self.ocrmypdfsettings['language'] = '+'.join(langs)
        self.start_ocr_action.setEnabled(False)
        self.stop_ocr_action.setEnabled(True)
        self.files_queue = files_to_process
        self.current_file_index = 0
        self.total_files = len(files_to_process)
        self.completed_files = 0
        if hasattr(self, 'selected_path_card') and self.selected_path_card:
            self.selected_path_card.set_total(self.total_files)
            self.selected_path_card.set_completed(0)
        self.process_next_file()

    def process_next_file(self):
        if self.current_file_index >= len(self.files_queue):
            self.start_ocr_action.setEnabled(True)
            self.stop_ocr_action.setEnabled(False)
            # Wait for all workers to finish before clearing
            self.cleanup_workers()
            return
        file_path = self.files_queue[self.current_file_index]
        if os.path.isdir(file_path):
            self.current_file_index += 1
            self.process_next_file()
            return
        card = FileCard(file_path, compact=True)
        self.cards_layout.addWidget(card)
        self.file_cards[file_path] = card
        worker = OCRWorker(file_path, self.ocrmypdfsettings)
        self.workers[file_path] = worker
        worker.progress.connect(card.set_progress)
        worker.message.connect(lambda text, type, fp=file_path: self.print_to_textview(text, type, fp))
        worker.finished.connect(lambda fp=file_path: self.ocr_finished(fp))
        worker.finished.connect(lambda w=worker, fp=file_path: self.cleanup_worker(fp, w))
        worker.start()

    def cleanup_worker(self, file_path, worker):
        # Properly wait for thread to finish and delete reference
        if file_path in self.workers and self.workers[file_path] is worker:
            worker.wait()
            del self.workers[file_path]

    def cleanup_workers(self):
        # Wait for all workers to finish before clearing references
        for fp, worker in list(self.workers.items()):
            worker.wait()
            del self.workers[fp]

    def stop_ocr(self):
        # Set the stop_event in ocr.py to interrupt the OCR process
        try:
            from ocrmypdfgui import ocr
            ocr.stop_event.set()
        except Exception:
            pass
        self.start_ocr_action.setEnabled(True)
        self.stop_ocr_action.setEnabled(False)

    def ocr_finished(self, file_path=None):
        if file_path and file_path in self.file_cards:
            self.file_cards[file_path].set_status('success')
        if file_path and file_path in self.workers:
            del self.workers[file_path]
        self.completed_files += 1
        if hasattr(self, 'selected_path_card') and self.selected_path_card:
            percent = int((self.completed_files / self.total_files) * 100) if self.total_files else 100
            self.selected_path_card.set_progress(percent, self.completed_files, self.total_files)
        self.current_file_index += 1
        self.process_next_file()

    def print_to_textview(self, text, type, file_path=None):
        # Always show all print_to_textview() content in the card details
        if not file_path:
            file_path = self.file_path or "(unknown)"
        if file_path not in self.file_cards:
            # Only add cards for files, not for the selected directory
            if os.path.isdir(file_path):
                return
            card = FileCard(file_path, compact=True)
            self.cards_layout.addWidget(card)
            self.file_cards[file_path] = card
        card = self.file_cards[file_path]
        card.add_message(text, type)
        if type in ("success", "error", "skip"):
            card.set_status(type)
            card.set_progress(100)
        else:
            card.set_status('working')
        self.cards_area.verticalScrollBar().setValue(self.cards_area.verticalScrollBar().maximum())

class DirectoryCard(QFrame):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setFixedHeight(16)
        self.progress.setTextVisible(True)
        self.total_files = 0
        self.completed_files = 0
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)
        label = QLabel(f"Selected: {self.path}")
        label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(label)
        layout.addWidget(self.progress)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("font-size: 11px; color: #1976d2;")
        layout.addWidget(self.status_label)
        self.setFrameStyle(QFrame.Panel | QFrame.Raised)
        self.setStyleSheet("QWidget { background: #f9f9f9; border-radius: 8px; border: 1px solid #ddd; }")

    def set_progress(self, percent, completed=None, total=None):
        self.progress.setValue(percent)
        if completed is not None:
            self.completed_files = completed
        if total is not None:
            self.total_files = total
        if self.total_files:
            self.status_label.setText(f"Progress: {percent}% ({self.completed_files} of {self.total_files} files)")
        else:
            self.status_label.setText(f"Progress: {percent}%")

    def set_total(self, total):
        self.total_files = total
        self.set_progress(self.progress.value(), self.completed_files, self.total_files)

    def set_completed(self, completed):
        self.completed_files = completed
        percent = int((self.completed_files / self.total_files) * 100) if self.total_files else 100
        self.set_progress(percent, self.completed_files, self.total_files)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
