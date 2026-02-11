import sqlite3
import os

# Pastikan folder database ada
os.makedirs('scripts', exist_ok=True)

def init_db():
    conn = sqlite3.connect('scripts/database.db')
    cursor = conn.cursor()
    # Tabel untuk history download
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            title TEXT,
            filename TEXT,
            downloaded_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()
    print("✅ Database 'database.db' berhasil dibuat di folder scripts/!")

if __name__ == "__main__":
    init_db()
