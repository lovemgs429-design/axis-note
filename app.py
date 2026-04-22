import streamlit as st
import pandas as pd
from database import init_db, get_db_connection
from logic import load_data, update_log_and_content
from style import apply_custom_style, render_header

# 1. 初期化：サイドバーを初期状態で非表示（collapsed）に設定
st.set_page_config(
    page_title="aXIs NOTE 🦋⛓", 
    layout="wide", 
    initial_sidebar_state="collapsed"
)
apply_custom_style()
init_db()

def reset_all_filters():
    st.session_state.search_word = ""
    st.session_state.artist_select = "すべて"
    st.session_state.category_select = "Singing"

# サイドバーへのSNSリンク：指定のURLを反映
st.sidebar.markdown("### ◢ Links")
st.sidebar.link_button("𝕏 (Twitter)", "https://x.com/XIDEN_RKMusic")
st.sidebar.link_button("YouTube", "https://www.youtube.com/@XIDEN_RKMusic")
st.sidebar.markdown("---")

try:
    df_all = load_data()
    if "search_word" not in st.session_state: st.session_state.search_word = ""
    if "artist_select" not in st.session_state: st.session_state.artist_select = "すべて"
    if "category_select" not in st.session_state: st.session_state.category_select = "Singing"

    # 2. ナビゲーション：公開用として Home のみに限定
    menu = st.sidebar.radio("Navigation", ["🦋 Home"])
    render_header()

    if menu == "🦋 Home":
        # フィルターエリア：元の仕様を完全維持
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

        # データの絞り込み・表示ロジック：元の仕様を完全維持
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

except Exception as e:
    st.error(f"Global Error: {e}")