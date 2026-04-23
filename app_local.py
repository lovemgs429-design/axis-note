import streamlit as st
import pandas as pd
import time
from database import init_db, get_db_connection
from logic import load_data, update_log_and_content, get_edit_logs, restore_from_log
from style import apply_custom_style, render_header

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
st.sidebar.link_button("𝕏 (Twitter)", "https://x.com/XIDEN_RKMusic")
st.sidebar.link_button("YouTube", "https://www.youtube.com/@XIDEN_RKMusic")
st.sidebar.markdown("---")

try:
    df_all = load_data()
    if "search_word" not in st.session_state: st.session_state.search_word = ""
    if "artist_select" not in st.session_state: st.session_state.artist_select = "すべて"
    if "category_select" not in st.session_state: st.session_state.category_select = "Singing"
    if "sort_select" not in st.session_state: st.session_state.sort_select = "最新順"

    # 2. ナビゲーション
    menu = st.sidebar.radio("Navigation", ["🦋 Home", "✒️ Write", "📜 Logs"])
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

        # 1. フィルタリング（既存の処理）
        f_df = df_all.copy()
        if st.session_state.search_word:
            f_df = f_df[f_df["曲名"].str.contains(st.session_state.search_word, case=False, na=False) | 
                        f_df["配信名"].str.contains(st.session_state.search_word, case=False, na=False)]
        if st.session_state.artist_select != "すべて": 
            f_df = f_df[f_df["アーティスト"] == st.session_state.artist_select]
        if st.session_state.category_select != "すべて": 
            f_df = f_df[f_df["カテゴリ"] == st.session_state.category_select]

        # 2. 列の作成（★ここをソートより前に移動！）
        f_df["Play"] = f_df.apply(lambda r: f"https://youtu.be/{r['stream_id']}?t={r['start_time']}", axis=1)
        f_df["開始"] = f_df["start_time"].apply(lambda x: f"{int(x//60):02}:{int(x%60):02}")

        # 3. ソート処理
        if sort_option == "おすすめ順":
            f_df = f_df.sort_values("盛り上がり度", ascending=False)
        else:
            # これで '開始' 列が存在するのでエラーになりません
            f_df = f_df.sort_values(["配信日", "開始"], ascending=[False, True])

        # 4. 表示
        disp = ["Play", "曲名", "アーティスト", "開始", "配信日", "配信名"]
        if st.session_state.category_select == "すべて": disp.append("カテゴリ")
        
        st.dataframe(
            f_df[disp], 
            use_container_width=True, 
            hide_index=True, 
            column_config={"Play": st.column_config.LinkColumn("▶️", display_text="📺")}
        )

    elif menu == "✒️ Write":
        st.subheader("✒️ Archive Edit")
        
        # 表示用のデータを準備
        edit_df = df_all[["content_id", "曲名", "アーティスト", "カテゴリ", "元の文字列", "stream_id", "start_time"]].copy()
        # YouTubeリンク列を動的に生成
        # ?t=秒数 を末尾に付けることで、その時間から再生されるようになります
        edit_df["再生リンク"] = (
            "https://www.youtube.com/watch?v=" + 
            edit_df["stream_id"] + 
            "&t=" + 
            edit_df["start_time"].astype(str)
        )
        
        # 画面に表示する列だけを絞り込む
        display_columns = ["content_id", "再生リンク", "曲名", "アーティスト", "カテゴリ", "元の文字列"]
        edited_df = st.data_editor(
            edit_df,
            hide_index=True,
            use_container_width=True,
            key="editor_grid",
            column_config={
                # ID列を見えるようにし、編集不可(disabled)に設定
                "content_id": st.column_config.Column(
                    "ID", 
                    help="データベース上の管理番号（編集不可）",
                    disabled=True,
                    width="small"
                ),
                # 再生リンクを「クリック可能なリンク」として設定
                "再生リンク": st.column_config.LinkColumn(
                    "🔗 再生",
                    help="YouTubeの歌い出し位置を開きます",
                    validate="^https://.*",
                    display_text="開く" # リンクを「開く」という文字で表示してスッキリさせる
                ),
                "カテゴリ": st.column_config.SelectboxColumn(options=["Singing", "Talk"]),
                "元の文字列": st.column_config.Column("未加工データ", disabled=True)
            }
        )
        
        if st.button("💾 Save All Changes"):
            # 編集後の DataFrame (edited_df) を渡すだけ
            count = update_log_and_content(edited_df)
            if count > 0:
                st.cache_data.clear()
                st.success(f"IDに基づき {count} 件のマスタを更新しました。")
                st.rerun()
        
    elif menu == "📜 Logs":
        st.subheader("📜 Modification Logs")

        # ロジック層からデータを取得
        h_df = get_edit_logs()

        if h_df.empty:
            st.info("履歴はありません。")
        else:
            # セッション状態の初期化
            if "restoring_ids" not in st.session_state:
                st.session_state["restoring_ids"] = set()

            for index, row in h_df.iterrows():
                # 復元済みかどうかの判定
                is_restored = row['edit_id'] in st.session_state["restoring_ids"]
                
                # タイトルの頭に状態アイコンを動的に付与
                status_icon = "✅ [復元済]" if is_restored else "🕒"
                expander_title = f"{status_icon} {row['edit_time']} | {row['old_title']}"

                # ログのヘッダー：判定済みのタイトルを使用
                with st.expander(expander_title, expanded=False):
                    
                    st.markdown("#### 🔄 変更の対比（ 現在 ← :blue[復元される値] ）")
                    
                    # 3カラム構成で新旧をわかりやすく並べる
                    col1, col2, col3 = st.columns([0.4, 0.1, 0.4])
                    
                    with col1:
                        st.write("**[ 現在（変更後） ]**")
                        st.code(f"Title: {row['new_title']}\nArtist: {row['new_artist']}\nCategory: {row['new_category']}")
                    
                    with col2:
                        st.markdown("<br><br>←", unsafe_allow_html=True)
                    
                    with col3:
                        st.write("**[ 過去（修正前） ]**")
                        st.code(f"Title: {row['old_title']}\nArtist: {row['old_artist']}\nCategory: {row['old_category']}")

                    st.divider()

                    # 復元ボタンの制御
                    if is_restored:
                        # 復元済みの場合はメッセージと無効化ボタンを表示
                        st.success("✅ この状態に復元済みです")
                        st.button("復元完了", key=f"btn_{row['edit_id']}", disabled=True, use_container_width=True)
                    else:
                        # 未復元の場合はアクティブなボタンを表示
                        if st.button("⏪ この状態に復元する", key=f"btn_{row['edit_id']}", type="primary", use_container_width=True):
                            # 押された瞬間にセッション状態へIDを保存
                            st.session_state["restoring_ids"].add(row['edit_id'])
                            
                            # ロジック層の関数を呼び出してDBを更新
                            if restore_from_log(row):
                                # 成功通知
                                st.toast(f"✅ 「{row['old_title']}」を復元しました。リストを更新します...", icon="🔄")
                                st.cache_data.clear()
                                
                                # ユーザーが状況を確認できるよう、1秒待機
                                import time
                                time.sleep(1.0)
                                
                                # 画面を再読み込みして、タイトルとボタンの状態を確定させる
                                st.rerun()
                            else:
                                st.error("復元に失敗しました。")
                                # 失敗した場合は再度押せるようにIDを削除
                                st.session_state["restoring_ids"].remove(row['edit_id'])

except Exception as e:
    st.error(f"Global Error: {e}")