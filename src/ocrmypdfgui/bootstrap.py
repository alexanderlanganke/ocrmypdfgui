import sys
import subprocess
import os
import platform
import shutil
from PyQt5 import QtWidgets, QtGui, QtCore
import webbrowser

REQUIRED_PYTHON_PACKAGES = [
    'ocrmypdf', 'pikepdf', 'pytesseract', 'Pillow', 'PyQt5', 'rarfile', 'coloredlogs', 'img2pdf', 'pdfminer.six', 'pluggy', 'reportlab', 'tqdm'
]

WINDOWS_DEPENDENCIES = {
    'tesseract': 'https://github.com/tesseract-ocr/tesseract',
    'ghostscript': 'https://www.ghostscript.com/download/gsdnld.html'
}

LINUX_DEPENDENCIES = [
    'tesseract-ocr', 'ghostscript', 'libqpdf-dev', 'unrar', 'python3-pyqt5'
]

class BootstrapWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OCRmyPDF-GUI Bootstrapping")
        self.setFixedSize(400, 300)
        layout = QtWidgets.QVBoxLayout(self)

        # Logo
        logo_path = os.path.join(os.path.dirname(__file__), "resources", "ocrmypdfgui.png")
        if os.path.exists(logo_path):
            pixmap = QtGui.QPixmap(logo_path).scaled(128, 128, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            logo = QtWidgets.QLabel()
            logo.setPixmap(pixmap)
            logo.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(logo)
        else:
            layout.addSpacing(140)

        # Status text
        self.status = QtWidgets.QTextEdit()
        self.status.setReadOnly(True)
        self.status.setFixedHeight(100)
        layout.addWidget(self.status)

        # Progress bar
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        self.setLayout(layout)

    def append_status(self, text):
        self.status.append(text)
        QtWidgets.QApplication.processEvents()

    def set_progress(self, value):
        self.progress.setValue(value)
        QtWidgets.QApplication.processEvents()

def check_and_install_python_packages(window):
    import importlib
    total = len(REQUIRED_PYTHON_PACKAGES)
    for i, pkg in enumerate(REQUIRED_PYTHON_PACKAGES, 1):
        try:
            importlib.import_module(pkg.split('.')[0])
            window.append_status(f"✔ {pkg} already installed")
        except ImportError:
            window.append_status(f"Installing missing Python package: {pkg}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', pkg])
            window.append_status(f"✔ {pkg} installed")
        window.set_progress(int(i / total * 50))  # 0-50% for Python packages

def install_tesseract_windows(window):
    import shutil
    import subprocess
    window.append_status("Attempting to install Tesseract (all languages) using winget...")
    if not shutil.which("winget"):
        window.append_status("winget is not available on this system. Please install Tesseract manually from: https://github.com/UB-Mannheim/tesseract/wiki/Downloads")
        return
    try:
        # Install Tesseract with all language packs
        subprocess.check_call([
            "winget", "install", "--id", "UB-Mannheim.TesseractOCR", "-e",
            "--accept-package-agreements", "--accept-source-agreements",
            "--override", "/alllanguages=1"
        ])
        window.append_status("Tesseract (all languages) installed successfully via winget.")
    except Exception as e:
        window.append_status(f"Error installing Tesseract with winget: {e}")
        window.append_status("Please install Tesseract with all languages manually from: https://github.com/UB-Mannheim/tesseract/wiki/Downloads")

def install_ghostscript_windows(window):
    import webbrowser
    # Only prompt if not already installed
    if shutil.which('gswin64c') or shutil.which('gswin32c'):
        window.append_status("✔ Ghostscript already installed and found in PATH.")
        return
    window.append_status("Automatic Ghostscript installation is not available.")
    window.append_status("Please install Ghostscript manually from: https://www.ghostscript.com/download/gsdnld.html")
    webbrowser.open("https://www.ghostscript.com/download/gsdnld.html")

def check_system_dependencies(window):
    if platform.system() == 'Windows':
        for i, (dep, url) in enumerate(WINDOWS_DEPENDENCIES.items(), 1):
            if not shutil.which(dep):
                if dep == 'tesseract':
                    window.append_status(f"Tesseract not found. Attempting automatic installation...")
                    install_tesseract_windows(window)
                    if shutil.which('tesseract'):
                        window.append_status("✔ Tesseract installed and found in PATH")
                    else:
                        window.append_status(f"⚠ Automatic installation failed. Please install Tesseract manually from: {url}")
                elif dep == 'ghostscript':
                    window.append_status(f"Ghostscript not found. Please install manually.")
                    install_ghostscript_windows(window)
                    if shutil.which('gswin64c') or shutil.which('gswin32c'):
                        window.append_status("✔ Ghostscript installed and found in PATH")
                    else:
                        window.append_status(f"⚠ Manual installation required. Please install Ghostscript from: {url}")
                else:
                    window.append_status(f"⚠ Missing {dep}. Please install from: {url}")
            else:
                window.append_status(f"✔ {dep} found in PATH")
            window.set_progress(50 + int(i / len(WINDOWS_DEPENDENCIES) * 50))  # 50-100%
    else:
        for i, dep in enumerate(LINUX_DEPENDENCIES, 1):
            if not shutil.which(dep.split('-')[0]):
                window.append_status(f"⚠ Missing system package: {dep}. Please install using your package manager.")
            else:
                window.append_status(f"✔ {dep} found")
            window.set_progress(50 + int(i / len(LINUX_DEPENDENCIES) * 50))  # 50-100%

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = BootstrapWindow()
    window.show()
    QtWidgets.QApplication.processEvents()

    check_and_install_python_packages(window)
    check_system_dependencies(window)
    window.set_progress(100)
    window.append_status("All dependencies checked. You can now run the application.")
    QtWidgets.QMessageBox.information(window, "Bootstrap Complete", "All dependencies checked. You can now run the application.")
    window.close()

if __name__ == '__main__':
    main()
