import PyInstaller.__main__
import os
import sys
import shutil

def build_executable():
    # Get the absolute path of the current directory
    base_path = os.path.abspath(os.path.dirname(__file__))
    
    # Clean up previous builds
    if os.path.exists('build'):
        shutil.rmtree('build')
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    
    PyInstaller.__main__.run([
        'app.py',
        '--name=CareHospital',
        '--onefile',  # Create a single executable
        '--add-data=templates:templates',
        '--add-data=static:static',
        f'--workpath={os.path.join(base_path, "build")}',
        f'--distpath={os.path.join(base_path, "dist")}',
        '--hidden-import=flask_sqlalchemy',
        '--hidden-import=flask_login',
        '--hidden-import=flask_wtf',
        '--hidden-import=reportlab',
        '--hidden-import=email_validator',
        '--noconfirm',  # Skip confirmation prompts
    ])
    
    # Create a README file with instructions
    readme_content = """
Care Hospital Management System
=============================

This is a standalone executable for the Care Hospital Management System.

To run the application:
1. Double-click the CareHospital executable
2. Open your web browser and go to http://localhost:8080
3. Login with the following credentials:
   Email: frazakram19@gmail.com
   Password: (contact administrator for password)

Features:
- Patient records management
- Billing system with download capability
- Admin authentication
- CRUD operations for patient records

For any issues or support, please contact the system administrator.
"""
    
    with open(os.path.join('dist', 'README.txt'), 'w') as f:
        f.write(readme_content)

if __name__ == '__main__':
    build_executable()
