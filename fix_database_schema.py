import sqlite3

def fix_db():
    print("🔧 Checking database schema...")
    try:
        conn = sqlite3.connect('roadkill.db')
        cursor = conn.cursor()
        
        # Check if column exists
        try:
            cursor.execute("SELECT animal_type FROM carcass LIMIT 1")
            print("ℹ️  Column 'animal_type' already exists in database.")
        except sqlite3.OperationalError:
            print("⚠️  Column 'animal_type' missing in database. Adding it now...")
            # Add the missing column
            cursor.execute("ALTER TABLE carcass ADD COLUMN animal_type VARCHAR(50)")
            # Set a default value for existing records
            cursor.execute("UPDATE carcass SET animal_type = 'Unknown' WHERE animal_type IS NULL")
            conn.commit()
            print("✅ Success: Column 'animal_type' added to database.")
        
        conn.close()
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fix_db()
