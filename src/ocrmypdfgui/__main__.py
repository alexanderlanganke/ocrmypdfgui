#!/usr/bin/env python3
import os
import sys
from PyQt5 import QtWidgets
from ocrmypdfgui import bootstrap

# On Windows, ensure Tesseract is in PATH for this process
if sys.platform.startswith("win"):
    possible_dirs = [
        r"C:\\Program Files\\Tesseract-OCR",
        r"C:\\Program Files (x86)\\Tesseract-OCR",
        os.path.expanduser(r"~\\AppData\\Local\\Programs\\Tesseract-OCR"),
    ]
    found = False
    for tess_dir in possible_dirs:
        tess_path = os.path.join(tess_dir, "tesseract.exe")
        if os.path.exists(tess_path):
            if tess_dir not in os.environ["PATH"]:
                os.environ["PATH"] = tess_dir + os.pathsep + os.environ["PATH"]
            print(f"[DEBUG] Added {tess_dir} to PATH.")
            found = True
            break
    if not found:
        print("[DEBUG] tesseract.exe not found in common locations. PATH may be incorrect.")
    print(f"[DEBUG] Current PATH: {os.environ['PATH']}")

    # Add Ghostscript to PATH if found
    gs_possible_dirs = [
        r"C:\Program Files\gs",
        r"C:\Program Files (x86)\gs"
    ]
    gs_found = False
    for base_dir in gs_possible_dirs:
        if os.path.exists(base_dir):
            for subdir in os.listdir(base_dir):
                bin_dir = os.path.join(base_dir, subdir, "bin")
                gs_exe = os.path.join(bin_dir, "gswin64c.exe")
                if os.path.exists(gs_exe):
                    if bin_dir not in os.environ["PATH"]:
                        os.environ["PATH"] = bin_dir + os.pathsep + os.environ["PATH"]
                    print(f"[DEBUG] Added {bin_dir} to PATH for Ghostscript.")
                    gs_found = True
                    break
            if gs_found:
                break
    if not gs_found:
        print("[DEBUG] Ghostscript not found in common locations. PATH may be incorrect.")

def main(args=None):
    if args is None:
        args = sys.argv[1:]

    app = QtWidgets.QApplication(sys.argv)
    window = bootstrap.BootstrapWindow()
    window.show()
    QtWidgets.QApplication.processEvents()

    bootstrap.check_and_install_python_packages(window)
    bootstrap.check_system_dependencies(window)
    window.set_progress(100)
    window.append_status("All dependencies checked. You can now run the application.")

    # Only close the window if there were no errors or warnings
    status_text = window.status.toPlainText().lower()
    if ("error" not in status_text and "fail" not in status_text and "manual" not in status_text):
        window.close()

    from ocrmypdfgui.gui import run
    run()

if __name__ == '__main__':
    sys.exit(main())
