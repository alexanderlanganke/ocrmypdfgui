from setuptools import setup, find_packages

setup(
    name="your_package_name",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        'cffi >= 1.9.1',
        'coloredlogs >= 14.0',
        'img2pdf >= 0.3.0, < 0.5',
        'pdfminer.six >= 20191110, != 20200720, <= 20201018',
        'Pillow >= 8.1.2',
        'pluggy >= 0.13.0, < 1.0',
        'reportlab >= 3.5.66',
        'setuptools',
        'tqdm >= 4',
        'ocrmypdf >= 13.0.0, < 14.0.0',
        'pikepdf >= 7.2.0, < 8.0.0',
        'pytesseract >= 0.3.8',
        'rarfile >= 3.0',
        'PyQt5 >= 5.15.0'
    ],
)