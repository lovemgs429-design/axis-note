import pandas as pd
import streamlit as st
from database import get_db_connection, init_db

@st.cache_data(ttl=600)
def load_data():
    init_db()
    conn = get_db_connection()
    try:
        df = pd.read_sql("""
            SELECT 
                l.rowid as log_id, l.content_id, c.title as 曲名, c.artist as アーティスト, c.category as カテゴリ,
                a.alias_name as 元の文字列, s.published_at as 配信日, s.stream_title as 配信名, 
                l.stream_id, l.start_time, l.density as 盛り上がり度
            FROM t_singing_logs l
            JOIN m_contents c ON l.content_id = c.content_id
            LEFT JOIN m_aliases a ON c.content_id = a.content_id
            LEFT JOIN t_streams s ON l.stream_id = s.stream_id
            GROUP BY l.stream_id, l.start_time
            ORDER BY s.published_at DESC, l.start_time ASC
        """, conn)
    except:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

def update_log_and_content(df_old, df_new):
    conn = get_db_connection()
    cursor = conn.cursor()
    updated_count = 0
    for i in range(len(df_new)):
        new_row = df_new.iloc[i]; old_row = df_old.iloc[i]
        if (str(new_row['曲名']).strip() != str(old_row['曲名']).strip() or 
            str(new_row['アーティスト']).strip() != str(old_row['アーティスト']).strip() or 
            str(new_row['カテゴリ']) != str(old_row['カテゴリ'])):
            
            cursor.execute("SELECT content_id FROM m_contents WHERE title = ? AND artist = ? AND category = ?", 
                           (new_row['曲名'], new_row['アーティスト'], new_row['カテゴリ']))
            res = cursor.fetchone()
            tid = res[0] if res else None
            if not tid:
                cursor.execute("INSERT INTO m_contents (title, artist, category) VALUES (?, ?, ?)", 
                               (new_row['曲名'], new_row['アーティスト'], new_row['カテゴリ']))
                tid = cursor.lastrowid
            
            cursor.execute("UPDATE t_singing_logs SET content_id = ? WHERE rowid = ?", (tid, new_row['log_id']))
            old_t = old_row['曲名'] if old_row['曲名'] else "(EMPTY)"
            cursor.execute("INSERT INTO t_edit_history (log_id, old_title, new_title, category) VALUES (?, ?, ?, ?)", 
                           (new_row['log_id'], old_t, new_row['曲名'], new_row['カテゴリ']))
            updated_count += 1
    conn.commit(); conn.close()
    return updated_count