import os
from sqlalchemy import text
from app import app, db

def migrate_schema():
    uri = app.config['SQLALCHEMY_DATABASE_URI']
    print(f"🔧 Connecting to database...")
    
    with app.app_context():
        with db.engine.connect() as conn:
            # We use a transaction so we can rollback if the check fails
            # (Postgres requires rollback after any error)
            trans = conn.begin()
            try:
                # 1. Try selecting the column to see if it exists
                conn.execute(text("SELECT animal_type FROM carcass LIMIT 1"))
                print("ℹ️  Column 'animal_type' already exists. No changes needed.")
                trans.rollback() # Nothing to do
                
            except Exception:
                # If select fails, the column is likely missing.
                # We must rollback the failed check before doing anything else.
                trans.rollback()
                
                # Start a new transaction for the update
                trans = conn.begin()
                print("⚠️  Column 'animal_type' missing. Adding it now...")
                
                # Add the column
                conn.execute(text("ALTER TABLE carcass ADD COLUMN animal_type VARCHAR(50)"))
                
                # Set default value for existing rows
                conn.execute(text("UPDATE carcass SET animal_type = 'Unknown' WHERE animal_type IS NULL"))
                
                trans.commit()
                print("✅ Success! Column 'animal_type' added to production database.")

if __name__ == "__main__":
    migrate_schema()
