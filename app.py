import streamlit as st
import pandas as pd
from database import init_db, get_db_connection
from logic import load_data, update_log_and_content
from style import apply_custom_style, render_header

# 1. 初期化
st.set_page_config(page_title="aXIs NOTE 🦋⛓", layout="wide")
apply_custom_style()
init_db()

def reset_all_filters():
    st.session_state.search_word = ""
    st.session_state.artist_select = "すべて"
    st.session_state.category_select = "Singing"

try:
    df_all = load_data()
    if "search_word" not in st.session_state: st.session_state.search_word = ""
    if "artist_select" not in st.session_state: st.session_state.artist_select = "すべて"
    if "category_select" not in st.session_state: st.session_state.category_select = "Singing"

    # 2. ナビゲーション
    menu = st.sidebar.radio("Navigation", ["🦋 Home", "✒️ Write", "📜 Logs"])
    render_header()

    if menu == "🦋 Home":
        f1, f2, f3, f4 = st.columns([2, 1, 1, 0.5])
        with f1: st.text_input("🔍 Search", key="search_word", placeholder="曲名や配信名...")
        with f2: 
            arts = ["すべて", "XIDEN"] + sorted([a for a in df_all["アーティスト"].unique() if a and a != "XIDEN"])
            st.selectbox("👤 Artist", arts, key="artist_select")
        with f3: st.selectbox("Category", ["すべて", "Singing", "Talk"], key="category_select")
        
        is_filtered = (st.session_state.search_word != "" or st.session_state.artist_select != "すべて" or st.session_state.category_select != "Singing")
        with f4:
            st.markdown("<br>", unsafe_allow_html=True)
            if is_filtered: st.button("✕", on_click=reset_all_filters)

        f_df = df_all.copy()
        if st.session_state.search_word:
            f_df = f_df[f_df["曲名"].str.contains(st.session_state.search_word, case=False, na=False) | f_df["配信名"].str.contains(st.session_state.search_word, case=False, na=False)]
        if st.session_state.artist_select != "すべて": f_df = f_df[f_df["アーティスト"] == st.session_state.artist_select]
        if st.session_state.category_select != "すべて": f_df = f_df[f_df["カテゴリ"] == st.session_state.category_select]

        f_df["Play"] = f_df.apply(lambda r: f"https://youtu.be/{r['stream_id']}?t={r['start_time']}", axis=1)
        f_df["開始"] = f_df["start_time"].apply(lambda x: f"{int(x//60):02}:{int(x%60):02}")
        disp = ["Play", "曲名", "アーティスト", "開始", "配信日", "配信名"]
        if st.session_state.category_select == "すべて": disp.append("カテゴリ")
        st.dataframe(f_df[disp], use_container_width=True, hide_index=True, column_config={"Play": st.column_config.LinkColumn("▶️", display_text="📺")})

    elif menu == "✒️ Write":
        st.subheader("✒️ Archive Edit")
        w_df = df_all.copy()
        w_df["Play"] = w_df.apply(lambda r: f"https://youtu.be/{r['stream_id']}?t={r['start_time']}", axis=1)
        w_df["開始"] = w_df["start_time"].apply(lambda x: f"{int(x//60):02}:{int(x%60):02}")
        edit_target = w_df[["Play", "log_id", "曲名", "アーティスト", "カテゴリ", "元の文字列", "開始", "配信名"]].copy()
        edited = st.data_editor(edit_target, hide_index=True, use_container_width=True, key="editor",
                               column_config={"log_id": None, "Play": st.column_config.LinkColumn("▶️", display_text="📺"), "カテゴリ": st.column_config.SelectboxColumn(options=["Singing", "Talk"])})
        if st.button("💾 Save All Changes", use_container_width=True):
            count = update_log_and_content(edit_target, edited)
            if count > 0:
                st.success(f"{count} 件記録しました。"); st.cache_data.clear(); st.rerun()
            else: st.warning("変更がありません。")

    elif menu == "📜 Logs":
        st.subheader("📜 Modification Logs")
        conn = get_db_connection()
        h_df = pd.read_sql("""
            SELECT datetime(edit_at, 'localtime') as 日時, 
            CASE WHEN old_title = '(SYSTEM AUTO)' THEN '✨ 自動登録'
                 WHEN old_title = '(NEW RECORD)' OR old_title = '(NEW)' THEN '🆕 新規作成'
                 ELSE '✏️ 修正: ' || old_title END as 区分,
            new_title as 変更後, category as カテゴリ 
            FROM t_edit_history ORDER BY edit_at DESC LIMIT 150
        """, conn)
        if h_df.empty: st.info("履歴はありません。")
        else: st.dataframe(h_df, use_container_width=True, hide_index=True)
        conn.close()

except Exception as e:
    st.error(f"Global Error: {e}")