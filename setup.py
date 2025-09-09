"""
Setup script for DST Reader.
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="dst-reader",
    version="1.0.0",
    author="DST Reader Team",
    author_email="dstreader@example.com",
    description="A PyQt-based GUI application for viewing and analyzing DST embroidery files",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/dst-reader",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
        "Topic :: Text Processing :: Markup",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=6.0.0",
            "black>=21.0.0",
            "flake8>=3.9.0",
            "mypy>=0.910",
        ],
    },
    entry_points={
        "console_scripts": [
            "dstreader=dstreader.gui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "dstreader": ["*.md", "*.txt"],
    },
    keywords="dst embroidery visualization pyqt gui",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/dst-reader/issues",
        "Source": "https://github.com/yourusername/dst-reader",
        "Documentation": "https://github.com/yourusername/dst-reader/wiki",
    },
)
