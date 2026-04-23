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

def update_log_and_content(df_edited):
    conn = get_db_connection()
    cursor = conn.cursor()
    updated_count = 0
    
    # 1. 比較用に現在のマスタデータを一括取得
    current_masters = pd.read_sql("SELECT content_id, title, artist, category FROM m_contents", conn)
    current_masters = current_masters.set_index('content_id')

    for _, row in df_edited.iterrows():
        cid = row['content_id']
        
        # データベースに存在しないIDはスキップ
        if cid not in current_masters.index:
            continue
            
        old_master = current_masters.loc[cid]
        
        # 2. 画面上の値と、DB上の「現在の値」を比較
        # ※ df_old(アプリ上の古い値)ではなく、DBの値を正として比較します
        has_changed = (
            str(row['曲名']).strip() != str(old_master['title']).strip() or
            str(row['アーティスト']).strip() != str(old_master['artist']).strip() or
            str(row['カテゴリ']) != str(old_master['category'])
        )
        
        if has_changed:
            # ③ m_contents (マスタ) の更新
            cursor.execute("""
                UPDATE m_contents 
                SET title = ?, artist = ?, category = ? 
                WHERE content_id = ?
            """, (row['曲名'], row['アーティスト'], row['カテゴリ'], cid))

            # ④ 履歴への記録
            # ログには「DBに元々入っていた値」を old として記録します
            cursor.execute("""
                INSERT INTO t_edit_history 
                (content_id, old_title, new_title, old_artist, new_artist, old_category, new_category, edit_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (
                cid,
                old_master['title'], row['曲名'],
                old_master['artist'], row['アーティスト'],
                old_master['category'], row['カテゴリ']
            ))
            
            updated_count += 1
            
    conn.commit()
    conn.close()
    return updated_count


# logic.py

def get_edit_logs(limit=100):
    """履歴一覧を取得する"""
    conn = get_db_connection()
    try:
        query = """
            SELECT edit_id, 
                   datetime(edit_at, 'localtime') as edit_time, 
                   old_title, new_title, 
                   old_artist, new_artist,
                   old_category, new_category,
                   content_id
            FROM t_edit_history 
            ORDER BY edit_at DESC LIMIT ?
        """
        return pd.read_sql(query, conn, params=(limit,))
    finally:
        conn.close()

def restore_from_log(log_row):
    """特定のログデータからマスタテーブルを復元する"""
    conn = get_db_connection()
    # 1. まず cursor を作成する（これが無いとエラーになります）
    cursor = conn.cursor()
    
    try:
        # 【重要】もし「曲名」でエラーが出る場合は、ここを title, artist, category に書き換えてください
        cursor.execute("""
            UPDATE m_contents 
            SET title = ?, artist = ?, category = ?
            WHERE content_id = ?
        """, (
            log_row['old_title'], 
            log_row['old_artist'], 
            log_row['old_category'], 
            log_row['content_id']
        ))
        
        # 2. 履歴の保存
        from datetime import datetime
        cursor.execute("""
            INSERT INTO t_edit_history 
            (content_id, old_title, new_title, old_artist, new_artist, old_category, new_category, edit_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_row['content_id'], 
            log_row['new_title'], log_row['old_title'], 
            log_row['new_artist'], log_row['old_artist'], 
            log_row['new_category'], log_row['old_category'],
            datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        conn.commit()
        return True
    except Exception as e:
        # エラーが出た場合、原因をプリントします
        print(f"Error restoring log: {e}")
        return False
    finally:
        # 最後に必ず閉じる
        conn.close()