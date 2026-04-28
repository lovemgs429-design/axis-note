import pandas as pd
import streamlit as st
from database import get_db_connection, init_db

# --- [高速化1] JOIN済み全データのメモリ常駐化 ---
@st.cache_resource
def load_data():
    """
    サーバー起動時、またはデータ更新時に一度だけ実行される。
    DB(SSD/HDD)から全データをJOINしてRAMに展開。
    """
    init_db()
    conn = get_db_connection()
    try:
        # 重いJOIN処理をここで1回だけ実行する
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
            ORDER BY s.published_at DESC, s.stream_title DESC, l.start_time ASC
        """, conn)
    except:
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

# --- [高速化2] 更新処理とメモリの同期 ---
def update_log_and_content(df_edited):
    """
    マスタデータの更新を行い、メモリ上のキャッシュをリセットする。
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    updated_count = 0
    
    # 比較用に現在のマスタデータを一括取得
    current_masters = pd.read_sql("SELECT content_id, title, artist, category FROM m_contents", conn)
    current_masters = current_masters.set_index('content_id')

    try:
        for _, row in df_edited.iterrows():
            cid = row['content_id']
            if cid not in current_masters.index:
                continue
                
            old_master = current_masters.loc[cid]
            
            # DB上の値と画面上の値に差があるかチェック
            has_changed = (
                str(row['曲名']).strip() != str(old_master['title']).strip() or
                str(row['アーティスト']).strip() != str(old_master['artist']).strip() or
                str(row['カテゴリ']) != str(old_master['category'])
            )
            
            if has_changed:
                # マスタ更新
                cursor.execute("""
                    UPDATE m_contents 
                    SET title = ?, artist = ?, category = ? 
                    WHERE content_id = ?
                """, (row['曲名'], row['アーティスト'], row['カテゴリ'], cid))

                # 履歴保存
                cursor.execute("""
                    INSERT INTO t_edit_history 
                    (content_id, old_title, new_title, old_artist, new_artist, old_category, new_category, edit_at) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
                """, (
                    cid,
                    old_master['title'], row['曲名'],
                    old_master['artist'], row['アーティスト'],
                    old_master['category'], row['カテゴリ']
                ))
                updated_count += 1
                
        conn.commit()
        
        # 【重要】更新に成功したら、メモリ上のロード済みデータを破棄する
        if updated_count > 0:
            st.cache_resource.clear()
            
    except Exception as e:
        conn.rollback()
        st.error(f"更新に失敗しました: {e}")
        return 0
    finally:
        conn.close()
        
    return updated_count

def get_edit_logs(limit=100):
    """履歴取得（これは頻繁に変わるため cache しないか、短い ttl を推奨）"""
    conn = get_db_connection()
    try:
        query = "SELECT * FROM t_edit_history ORDER BY edit_at DESC LIMIT ?"
        return pd.read_sql(query, conn, params=(limit,))
    finally:
        conn.close()

def restore_from_log(log_row):
    """復元処理"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE m_contents 
            SET title = ?, artist = ?, category = ?
            WHERE content_id = ?
        """, (log_row['old_title'], log_row['old_artist'], log_row['old_category'], log_row['content_id']))
        
        # 履歴記録
        cursor.execute("""
            INSERT INTO t_edit_history 
            (content_id, old_title, new_title, old_artist, new_artist, old_category, new_category, edit_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """, (
            log_row['content_id'], 
            log_row['new_title'], log_row['old_title'], 
            log_row['new_artist'], log_row['old_artist'], 
            log_row['new_category'], log_row['old_category']
        ))
        conn.commit()
        
        # 【重要】復元に成功したらメモリキャッシュをクリア
        st.cache_resource.clear()
        return True
    except:
        conn.rollback()
        return False
    finally:
        conn.close()