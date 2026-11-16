"""
Standalone Database Initialization Utility
Usage:
    python db_init.py
"""
import sys
from db import init_database

if __name__ == "__main__":
    print("==================================================================")
    print("  Smart Food Waste Reduction & Donation Management System")
    print("  Database Initialization & Seeding")
    print("==================================================================")
    try:
        init_database()
        print("\n[SUCCESS] Database schema created and seed data populated successfully!")
        print("You can now launch the Flask app with: python app.py")
    except Exception as e:
        print(f"\n[ERROR] Database initialization failed: {e}")
        print("\nPlease ensure MySQL/MariaDB server is running and credentials in .env are correct.")
        sys.exit(1)
