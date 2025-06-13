# Cross-platform PyQt5 GUI for OCRmyPDFGui
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QProgressBar, QFileDialog, QMessageBox, QDialog, QCheckBox, QComboBox, QDialogButtonBox, QFormLayout, QGroupBox, QGridLayout, QLineEdit, QListWidget, QListWidgetItem, QAbstractItemView, QToolTip
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import json
import pytesseract

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
        selected_langs = set(self.settings.get("language", []))
        for lang in langs:
            item = QListWidgetItem(lang)
            if lang in selected_langs:
                item.setSelected(True)
            self.language_list.addItem(item)
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

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCRmyPDFGui (PyQt5)")
        self.resize(1000, 600)
        self.file_path = ""
        self.ocrmypdfsettings = {}
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        layout = QVBoxLayout()
        btn_layout = QHBoxLayout()

        self.select_file_btn = QPushButton("Select File")
        self.select_file_btn.clicked.connect(self.select_file)
        btn_layout.addWidget(self.select_file_btn)

        self.select_folder_btn = QPushButton("Select Folder")
        self.select_folder_btn.clicked.connect(self.select_folder)
        btn_layout.addWidget(self.select_folder_btn)

        self.start_ocr_btn = QPushButton("Start OCR")
        self.start_ocr_btn.clicked.connect(self.start_ocr)
        btn_layout.addWidget(self.start_ocr_btn)

        self.stop_ocr_btn = QPushButton("Stop OCR")
        self.stop_ocr_btn.clicked.connect(self.stop_ocr)
        btn_layout.addWidget(self.stop_ocr_btn)
        self.stop_ocr_btn.setEnabled(False)

        layout.addLayout(btn_layout)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        self.status_label = QLabel("Idle")
        layout.addWidget(self.status_label)

        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        layout.addWidget(self.text_output)

        # Add Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_btn)

        central.setLayout(layout)
        self.setCentralWidget(central)

    def select_file(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Select File", "", "PDF/CBZ/CBR Files (*.pdf *.cbz *.cbr)")
        if fname:
            self.file_path = fname
            self.status_label.setText(f"Selected: {fname}")

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.file_path = folder
            self.status_label.setText(f"Selected: {folder}")

    def open_settings(self):
        # Load settings from file if exists
        settings = DEFAULT_SETTINGS.copy()
        try:
            if os.path.exists(SETTINGS_PATH):
                with open(SETTINGS_PATH, 'r') as f:
                    settings.update(json.load(f))
        except Exception as e:
            self.text_output.append(f"<span style='color:red'>Error loading settings: {e}</span>")
        dlg = SettingsDialog(self, settings)
        if dlg.exec_() == QDialog.Accepted:
            new_settings = dlg.get_settings()
            # Save to file
            try:
                os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
                with open(SETTINGS_PATH, 'w') as f:
                    json.dump(new_settings, f, indent=2)
                self.text_output.append("<span style='color:green'>Settings saved.</span>")
            except Exception as e:
                self.text_output.append(f"<span style='color:red'>Error saving settings: {e}</span>")
            self.ocrmypdfsettings = new_settings

    def start_ocr(self):
        if not self.file_path:
            QMessageBox.warning(self, "No file/folder selected", "Please select a file or folder first.")
            return
        # Load settings before starting OCR
        settings = DEFAULT_SETTINGS.copy()
        try:
            if os.path.exists(SETTINGS_PATH):
                with open(SETTINGS_PATH, 'r') as f:
                    settings.update(json.load(f))
        except Exception as e:
            self.text_output.append(f"<span style='color:red'>Error loading settings: {e}</span>")
        self.ocrmypdfsettings = settings
        self.start_ocr_btn.setEnabled(False)
        self.stop_ocr_btn.setEnabled(True)
        self.text_output.append("Starting OCR...")
        self.worker = OCRWorker(self.file_path, self.ocrmypdfsettings)
        self.worker.progress.connect(self.progress.setValue)
        self.worker.message.connect(self.print_to_textview)
        self.worker.finished.connect(self.ocr_finished)
        self.worker.start()

    def stop_ocr(self):
        # TODO: Implement stop logic (set stop_event in ocr.py)
        self.text_output.append("Stop requested (not yet implemented)")
        self.start_ocr_btn.setEnabled(True)
        self.stop_ocr_btn.setEnabled(False)

    def ocr_finished(self):
        self.text_output.append("OCR finished.")
        self.start_ocr_btn.setEnabled(True)
        self.stop_ocr_btn.setEnabled(False)

    def print_to_textview(self, text, type):
        if type == "success":
            self.text_output.append(f'<span style="color:green">{text}</span>')
        elif type == "error":
            self.text_output.append(f'<span style="color:red">{text}</span>')
        elif type == "skip":
            self.text_output.append(f'<span style="color:blue">{text}</span>')
        else:
            self.text_output.append(text)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
