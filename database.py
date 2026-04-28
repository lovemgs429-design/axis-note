import sqlite3

def get_db_connection():
    return sqlite3.connect("utawaku.db")

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # 1. 履歴テーブル作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS t_edit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            content_id INTEGER, 
            old_title TEXT, 
            new_title TEXT, 
            old_artist TEXT,
            new_artist TEXT,
            old_category TEXT,
            new_category TEXT,
            edit_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. カラム修復（Migration）- 必要なカラムがなければ追加
    cursor.execute("PRAGMA table_info(t_edit_history)")
    cols = [c[1] for c in cursor.fetchall()]
    for col_name in ["old_artist", "new_artist", "old_category", "new_category"]:
        if col_name not in cols:
            cursor.execute(f"ALTER TABLE t_edit_history ADD COLUMN {col_name} TEXT")

    # 3. インデックスの追加（高速化の肝）
    # 歌唱ログの取得（曲ID、配信ID、開始時間）をカバーするインデックス
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_log_main ON t_singing_logs(content_id, stream_id, start_time)")
    
    # 配信情報の取得（配信ID、日付順）を高速化
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_streams_date ON t_streams(published_at DESC)")
    
    # 曲名・アーティスト名の検索とソートを高速化
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_search ON m_contents(title, artist, category)")
    
    # エイリアス検索の高速化
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alias_lookup ON m_aliases(alias_name, content_id)")

    # 4. 統計情報の更新（SQLiteのクエリプランナを最適化）
    cursor.execute("ANALYZE")

    conn.commit()
    conn.close()