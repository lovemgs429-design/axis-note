import streamlit as st

def apply_custom_style():
    st.markdown("""
        <style>
        /* 全体背景とテキスト */
        .stApp { 
            background-color: #050505 !important; 
            color: #D1C4E9 !important; 
        }
        
        /* サイドバー */
        [data-testid="stSidebar"] { 
            background-color: #0D0512 !important; 
            border-right: 2px solid #4A148C !important; 
        }
        
        /* 入力フォーム・セレクトボックスの枠線と背景 */
        div[data-baseweb="input"], div[data-baseweb="select"] {
            border: 1px solid #7B1FA2 !important;
            background-color: #1A0A23 !important;
        }
        
        /* ボタンのデザイン */
        .stButton>button { 
            background-color: #1A0A23 !important; 
            color: #B287FD !important; 
            border: 1px solid #7B1FA2 !important;
            transition: 0.3s;
        }
        .stButton>button:hover {
            border: 1px solid #B287FD !important;
            box-shadow: 0 0 10px #7B1FA2;
            color: #FFFFFF !important;
        }

        /* データフレーム（表）のカスタマイズ */
        .stDataFrame {
            border: 1px solid #4A148C !important;
        }
        
        /* ロゴ周りのタイポグラフィ */
        .note-header { 
            color: #B287FD !important; 
            font-size: 42px !important; 
            font-weight: 800; 
            letter-spacing: 0.15em; 
            text-shadow: 0 0 12px #7B1FA2; 
            margin-bottom: 5px; 
        }
        .sub-title-archive { 
            color: #9575CD !important; 
            font-size: 13px !important; 
            font-family: 'Courier New', Courier, monospace; 
            letter-spacing: 0.2em; 
            margin-bottom: 10px; 
            font-weight: 600;
            opacity: 0.8;
        }
        .fan-mark-neon { 
            font-size: 24px; 
            color: #B287FD !important; 
            text-shadow: 0 0 15px #7B1FA2; 
            margin-bottom: 35px; 
        }

        /* スクロールバーのカスタマイズ（紫のアクセント） */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #050505; }
        ::-webkit-scrollbar-thumb { background: #4A148C; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: #7B1FA2; }
        </style>
        """, unsafe_allow_html=True)

def render_header():
    """aXIs NOTE のこだわり配置をレンダリング"""
    st.markdown('<p class="note-header">◢ aXIs NOTE</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title-archive">UNOFFICIAL FAN-MADE DATABASE</p>', unsafe_allow_html=True)
    st.markdown('<p class="fan-mark-neon">🦋⛓</p>', unsafe_allow_html=True)