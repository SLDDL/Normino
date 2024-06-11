from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="normino",
    version="6.0",
    url="https://github.com/SLDDL/Normino",
    py_modules=["normino"],
    install_requires=[
        "colorama",
        "beautifulsoup4",
        "requests",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": [
            "normino=normino:main",
        ],
    },
    project_urls={
        "Documentation": "https://github.com/SLDDL/Normino/blob/main/README.md",
        "Source": "https://github.com/SLDDL/Normino",
        "Tracker": "https://github.com/SLDDL/Normino/issues",
        "Icon": "https://raw.githubusercontent.com/SLDDL/Normino/main/icon.png",
    },
)
