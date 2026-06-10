import os
import sys

# Ensure src modules can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.auth.auth_manager import auth_manager

def seed_admin():
    print("Seeding default admin user...")
    
    # We will try to register the user
    success, msg = auth_manager.register_user(
        username="admin",
        email="admin@disasterconnect.org",
        password="Admin@1234",
        role="admin"
    )
    
    if success:
        print(f"Success! Admin user created with ID: {msg}")
    else:
        print(f"Failed to create admin user: {msg}")
        
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    seed_admin()
