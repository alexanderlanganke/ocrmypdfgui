import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="ocrmypdfgui",
    version="0.1.1",
    author="Alexander Langanke",
    author_email="alexlanganke@gmail.com",
    description="Hobby Project GUI for the Python Program 'OCRmyPDF' by James R. Barlow",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/alexanderlanganke/ocrmypdfgui",
    project_urls={
        "Bug Tracker": "https://github.com/alexanderlanganke/ocrmypdfgui/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.6",
    install_requires=[
        'cffi >= 1.9.1',  # must be a setup and install requirement
        'coloredlogs >= 14.0',  # strictly optional
        'img2pdf >= 0.3.0, < 0.5',  # pure Python, so track HEAD closely
        'pdfminer.six >= 20191110, != 20200720, <= 20201018',
        "pikepdf >= 2.10.0",
        'Pillow >= 8.1.2',
        'pluggy >= 0.13.0, < 1.0',
        'reportlab >= 3.5.66',
        'setuptools',
        'tqdm >= 4',
        'ocrmypdf'
    ],
    entry_points={'console_scripts': ['ocrmypdfgui = ocrmypdfgui.__main__:main']},

)
