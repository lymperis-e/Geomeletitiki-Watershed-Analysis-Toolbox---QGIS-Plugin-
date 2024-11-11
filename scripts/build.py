import os
import zipfile

BUILD_DIR = 'dist'
ZIP_FILE = 'gwat.zip'
IGNORE = [
    '.git',
    '.gitignore',
    '.gitattributes',
    '.vscode',
    '.DS_Store',
    '.idea',
    '__pycache__',
    'scripts',
    'dist',
    'build',
    'README.md',
    'LICENSE',
    'requirements.txt',
    'Pipfile',
    'Pipfile.lock',
    '*.log',
    '.pylintrc',
    '*.zip',
    '*.pyc',
    '*.pyo',
    '*.pyd',
    '*.pyi',
    'test',
    '__pycache__',
]

def zipdir(path, ziph):
    # ziph is the zipfile handle
    for root, dirs, files in os.walk(path):
        # Remove ignored directories from the search path
        dirs[:] = [d for d in dirs if d not in IGNORE]
        for file in files:
            if not any([file.endswith(i) for i in IGNORE]):
                # Calculate the relative path but ensure all files are in root of the zip
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, path)
                ziph.write(abs_path, rel_path)
            
def main():
    plugin_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print(f'Creating {ZIP_FILE} from {plugin_dir}')
    
    # Create output directory if it doesn't exist
    if not os.path.exists(os.path.join(plugin_dir, BUILD_DIR)):
        os.makedirs(os.path.join(plugin_dir, BUILD_DIR))
    
    zipf = zipfile.ZipFile(os.path.join(plugin_dir, BUILD_DIR, ZIP_FILE), 'w', zipfile.ZIP_DEFLATED)
    zipdir(plugin_dir, zipf)
    zipf.close()
    
if __name__ == '__main__':
    main()
