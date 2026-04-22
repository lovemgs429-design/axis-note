import sqlite3

def get_db_connection():
    return sqlite3.connect("utawaku.db")

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 履歴テーブル作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS t_edit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            log_id INTEGER, 
            old_title TEXT, 
            new_title TEXT, 
            edit_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # カラム修復（Migration）
    cursor.execute("PRAGMA table_info(t_edit_history)")
    cols = [c[1] for c in cursor.fetchall()]
    if "category" not in cols:
        cursor.execute("ALTER TABLE t_edit_history ADD COLUMN category TEXT")
    conn.commit()
    conn.close()