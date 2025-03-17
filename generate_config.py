import pickle
from werkzeug.security import generate_password_hash
import os

def generate_initial_config():
    # Initial configuration for Care Hospital
    config = {
        'hospital_name': 'Care Hospital',
        'admin_email': 'frazakram19@gmail.com',
        'admin_password_hash': generate_password_hash('admin123'),  # Default password, should be changed on first login
        'database_path': 'hospital.db',
        'settings': {
            'allow_pdf_download': True,
            'session_timeout': 3600,  # 1 hour
            'pagination_limit': 10,
            'currency': '₹'
        }
    }
    
    # Create the pickle file
    with open('config.pkl', 'wb') as f:
        pickle.dump(config, f)
    
    print("Configuration file 'config.pkl' has been generated successfully!")
    print(f"Admin email: {config['admin_email']}")
    print("Default password: admin123 (please change after first login)")

if __name__ == '__main__':
    generate_initial_config()
