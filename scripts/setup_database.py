#!/usr/bin/env python3
"""
Script to set up the database with initial migration
"""
import os
import sys
import subprocess
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.db.database import engine, Base
from app.db.models import Incentive, Company, IncentiveCompanyMatch


def run_alembic_command(command):
    """Run an alembic command"""
    backend_path = Path(__file__).parent.parent / "backend"
    os.chdir(backend_path)
    
    try:
        result = subprocess.run(
            ["alembic"] + command.split(),
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✓ {command}: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {command} failed: {e.stderr}")
        return False


def create_tables():
    """Create all tables directly"""
    try:
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Error creating tables: {e}")
        return False


def main():
    print("Setting up Public Incentives database...")
    
    # Create data directory
    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    print(f"✓ Created data directory: {data_dir}")
    
    # Try to run alembic migration first
    print("\n1. Running Alembic migration...")
    if run_alembic_command("revision --autogenerate -m 'Initial migration'"):
        if run_alembic_command("upgrade head"):
            print("✓ Database migration completed successfully")
        else:
            print("⚠ Migration failed, creating tables directly...")
            create_tables()
    else:
        print("⚠ Alembic failed, creating tables directly...")
        create_tables()
    
    print("\n✓ Database setup completed!")
    print("\nNext steps:")
    print("1. Place your CSV files in the 'data/' directory:")
    print("   - data/companies.csv")
    print("   - data/incentives.csv")
    print("2. Start the API: docker-compose up")
    print("3. Check file status: GET /data/files/status")
    print("4. Import data: POST /data/import")
    print("5. Process matches: POST /data/process-all-matches")


if __name__ == "__main__":
    main()
