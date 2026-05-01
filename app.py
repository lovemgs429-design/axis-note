import streamlit as st
import pandas as pd
from database import init_db, get_db_connection
from logic import load_data, update_log_and_content
from style import apply_custom_style, render_header
from streamlit_gsheets import GSheetsConnection
import datetime

conn = st.connection("gsheets", type=GSheetsConnection)

# 1. 初期化：サイドバーを初期状態で非表示（collapsed）に設定
st.set_page_config(
    page_title="aXIs NOTE 🦋⛓", 
    page_icon="🦋",
    layout="wide", 
    initial_sidebar_state="collapsed"
)
apply_custom_style()
init_db()

def reset_all_filters():
    st.session_state.search_word = ""
    st.session_state.artist_select = "すべて"
    st.session_state.category_select = "Singing"
    st.session_state.sort_select = "最新順"

# サイドバーへのSNSリンク：指定のURLを反映
st.sidebar.markdown("### ◢ Links")
# Xのボタン
st.sidebar.link_button("𝕏 (Twitter)", "https://x.com/XIDEN_RKMusic")
st.sidebar.caption("XIDEN Official X Account")

# YouTubeのボタン
st.sidebar.link_button("YouTube", "https://www.youtube.com/@XIDEN_RKMusic")
# 2つの情報を1行に凝縮
st.sidebar.caption("XIDEN Official / 歌唱ログ・DB参照先アーカイブ")

# ナビゲーション
st.sidebar.divider()
menu = st.sidebar.radio("Navigation", ["🦋 Home"])

st.sidebar.write("")

# バージョン情報に擬態。🦋⛓ をクリックした時だけ Web Player へ
st.sidebar.markdown(
    '<div style="text-align: left; color: gray; font-size: 11px; opacity: 0.7;">'
    'v1.0.0-release | '
    '<a href="https://axis-web-player-v1.streamlit.app/" '
    'style="text-decoration: none; color: inherit;">🦋⛓</a>'
    '</div>', 
    unsafe_allow_html=True
)

with st.sidebar.expander("💬 感想・意見・バグ報告"):
    with st.form("feedback_form", clear_on_submit=True):
        name = st.text_input("お名前（任意）", placeholder="匿名希望")
        comment = st.text_area("改善案や不具合を教えてください", placeholder="ここに入力してください")
        submitted = st.form_submit_button("送信")

        if submitted:
            if not comment:
                st.error("メッセージを入力してください。")
            else:
                try:
                    ss_url = st.secrets["connections"]["gsheets"]["spreadsheet"]
                    df = conn.read(spreadsheet=ss_url, ttl=0)
                    
                    new_data = pd.DataFrame([{
                        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "name": name if name else "匿名",
                        "comment": comment
                    }])
                    
                    updated_df = pd.concat([df, new_data], ignore_index=True)
                    conn.update(spreadsheet=ss_url, data=updated_df)
                    
                    # --- 変更点：成功時はフォームの代わりにメッセージを表示 ---
                    st.balloons() # お祝いの風船（任意）
                    st.success("報告を受け付けました。ありがとうございます！🦋⛓")
                    # st.rerun() はあえて書かない
                    
                except Exception as e:
                    st.error(f"送信に失敗しました。詳細エラー: {e}")

st.sidebar.divider()
st.sidebar.markdown(
    """
    <div style="font-size: 10px; color: gray; opacity: 0.8;">
    <b>◢ Legal & Compliance</b><br>
    This app uses the YouTube API Services.<br>
    By using this app, users are agreeing to be bound by the 
    <a href="https://www.youtube.com/t/terms" target="_blank" style="color: gray;">YouTube Terms of Service</a>.<br>
    Please also refer to the <a href="https://policies.google.com/privacy" target="_blank" style="color: gray;">Google Privacy Policy</a>.
    </div>
    """, 
    unsafe_allow_html=True
)

try:
    df_all = load_data()
    if "search_word" not in st.session_state: st.session_state.search_word = ""
    if "artist_select" not in st.session_state: st.session_state.artist_select = "すべて"
    if "category_select" not in st.session_state: st.session_state.category_select = "Singing"
    if "sort_select" not in st.session_state: st.session_state.sort_select = "最新順"

    # 2. ナビゲーション：公開用として Home のみに限定
    render_header()

    if menu == "🦋 Home":
        f1, f2, f3, f4, f5 = st.columns([2, 1, 1, 1, 0.5])
        with f1: st.text_input("🔍 Search", key="search_word", placeholder="曲名や配信名...")
        with f2: 
            arts = ["すべて", "XIDEN"] + sorted([a for a in df_all["アーティスト"].unique() if a and a != "XIDEN"])
            st.selectbox("👤 Artist", arts, key="artist_select")
        with f3: st.selectbox("Category", ["すべて", "Singing", "Talk"], key="category_select")
        
        is_filtered = (st.session_state.search_word != "" or st.session_state.artist_select != "すべて" or st.session_state.category_select != "Singing" or st.session_state.sort_select != "最新順")
        with f4: 
            # ソート順の選択肢を追加
            sort_option = st.selectbox("Sort", ["最新順", "おすすめ順"],key="sort_select")
        with f5:
            st.markdown("<br>", unsafe_allow_html=True)
            if is_filtered: st.button("✕", on_click=reset_all_filters)

        # 1. コピーをせず参照から開始（メモリ節約）
        f_df = df_all

        # 2. 検索ワードによる絞り込み（高速な1カラム検索）
        if st.session_state.search_word:
            # 検索ワードも小文字にして比較
            sw = st.session_state.search_word.lower()
            f_df = f_df[f_df["search_index"].str.contains(sw, na=False)]

        # 3. プルダウンによる絞り込み（完全一致は非常に高速）
        if st.session_state.artist_select != "すべて":
            f_df = f_df[f_df["アーティスト"] == st.session_state.artist_select]
            
        if st.session_state.category_select != "すべて":
            f_df = f_df[f_df["カテゴリ"] == st.session_state.category_select]
        f_df["Play"] = f_df.apply(lambda r: f"https://youtu.be/{r['stream_id']}?t={r['start_time']}", axis=1)
        f_df["開始"] = f_df["start_time"].apply(lambda x: f"{int(x//60):02}:{int(x%60):02}")

        # 3. ソート処理
        if sort_option == "おすすめ順":
            f_df = f_df.sort_values("盛り上がり度", ascending=False)
        else:
            # これで '開始' 列が存在するのでエラーになりません
            f_df = f_df.sort_values(["配信日", "配信名", "start_time"], ascending=[False, False, True])

        # 4. 表示
        disp = ["Play", "曲名", "アーティスト", "開始", "配信日", "配信名"]
        if st.session_state.category_select == "すべて": disp.append("カテゴリ")
        
        st.dataframe(f_df[disp], width="stretch", hide_index=True, column_config={"Play": st.column_config.LinkColumn("▶️", display_text="📺")})

except Exception as e:
    st.error(f"Global Error: {e}")