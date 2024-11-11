# Create a QGIS plugin .zip file

import os
import zipfile

BUILD_DIR = "dist"
ZIP_FILE = "gwat.zip"
IGNORE = [
    ".git",
    ".gitignore",
    ".gitattributes",
    ".vscode",
    ".DS_Store",
    ".idea",
    "__pycache__",
    "scripts",
    "dist",
    "build",
    "README.md",
    "requirements.txt",
    ".pylintrc",
    "*.zip",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.pyi",
    "test",
    "__pycache__",
    "logo",
]


def zipdir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):

        dirs[:] = [d for d in dirs if d not in IGNORE]
        for file in files:
            if not any([file.endswith(i) for i in IGNORE]):
                ziph.write(
                    os.path.join(root, file),
                    os.path.relpath(os.path.join(root, file), os.path.join(path, "..")),
                )


def main():
    plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    print(f"Creating {ZIP_FILE} from {plugin_dir}")

    # Create output directory
    if not os.path.exists(os.path.join(plugin_dir, BUILD_DIR)):
        os.makedirs(os.path.join(plugin_dir, BUILD_DIR))

    zipf = zipfile.ZipFile(
        os.path.join(plugin_dir, BUILD_DIR, ZIP_FILE), "w", zipfile.ZIP_DEFLATED
    )
    zipdir(plugin_dir, zipf)
    zipf.close()


if __name__ == "__main__":
    main()
