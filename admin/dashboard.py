import streamlit as st
import requests
import pandas as pd

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Saathii Admin Dashboard", layout="wide")

VERIFY_API_URL = "https://saathiiapp.com/admin/verification/pending"
WEBHOOK_URL = "https://saathiiapp.com/admin/verification/webhook"
STATS_API_URL = "https://saathiiapp.com/both/feed/stats"

# ---------------- SIDEBAR NAV ----------------
st.sidebar.title("📊 Saathii Admin")
page = st.sidebar.radio(
    "Navigate", ["🏠 Home (Dashboard)", "🎧 Listeners Table"], index=0
)
st.sidebar.markdown("---")
st.sidebar.info(
    "Manage verifications, monitor listeners, and track live platform stats."
)


# ---------------- FETCH DATA ----------------
st.markdown(
    """
    <style>
    /* ========== Neon Theme ========== */
    :root {
        --bg: #0a0f1e;
        --panel: #0f172a;
        --text: #e6f0ff;
        --muted: #9db0d0;
        --accent: #00e5ff; /* neon cyan */
        --accent-2: #ff00ff; /* neon magenta */
        --accent-3: #39ff14; /* neon green */
        --glow: 0 0 10px rgba(0,229,255,0.6), 0 0 20px rgba(0,229,255,0.4), 0 0 34px rgba(0,229,255,0.25);
        --soft-glow: 0 0 6px rgba(0,229,255,0.4), 0 0 16px rgba(0,229,255,0.25);
        --ring: 0 0 0 1px rgba(0,229,255,0.45) inset;
    }

    .stApp, .stApp header { background: radial-gradient(1000px 600px at 10% 0%, rgba(255,0,255,0.06), transparent), radial-gradient(1000px 800px at 100% 0%, rgba(0,229,255,0.07), transparent), var(--bg) !important; }
    .stApp, .stMarkdown, .stText, .stSelectbox, .stRadio, .stSubheader, .stHeader, .stCaption { color: var(--text) !important; }
    .block-container { padding-top: 1.5rem; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(20,27,55,0.95), rgba(13,19,41,0.95));
        border-right: 1px solid rgba(0,229,255,0.2);
        box-shadow: 6px 0 24px rgba(0,0,0,0.35);
    }
    section[data-testid="stSidebar"] * { color: var(--text) !important; }
    section[data-testid="stSidebar"] .stMarkdown h1, h2, h3 { text-shadow: var(--soft-glow); }

    /* Headings */
    h1, h2, h3, .stHeader, .stSubheader { color: var(--text) !important; text-shadow: var(--soft-glow); }
    hr { border-color: rgba(0,229,255,0.2) !important; }

    /* Links */
    a { color: var(--accent) !important; text-decoration: none; }
    a:hover { text-shadow: var(--soft-glow); }

    /* Buttons */
    .stButton > button {
        background: rgba(0,229,255,0.08);
        color: var(--text);
        border: 1px solid rgba(0,229,255,0.5);
        border-radius: 10px;
        box-shadow: var(--ring), var(--soft-glow);
        transition: all .15s ease-out;
    }
    .stButton > button:hover { box-shadow: var(--glow); transform: translateY(-1px); }
    .stButton > button:active { transform: translateY(0); }

    /* Metrics */
    [data-testid="stMetric"] { background: rgba(7,12,30,0.7); padding: 12px; border-radius: 12px; border: 1px solid rgba(0,229,255,0.18); box-shadow: var(--soft-glow); }
    [data-testid="stMetricLabel"] { color: var(--muted) !important; }
    [data-testid="stMetricValue"] { color: var(--accent) !important; text-shadow: var(--glow); }

    /* Tabs */
    div[role="tablist"] > div { gap: 6px; }
    div[role="tab"] { background: rgba(0,229,255,0.06); color: var(--text); border: 1px solid rgba(0,229,255,0.25); border-radius: 10px; }
    div[role="tab"][aria-selected="true"] { box-shadow: var(--glow); border-color: rgba(0,229,255,0.55); }

    /* DataFrame container */
    [data-testid="stDataFrame"] { background: rgba(12,18,40,0.7); border-radius: 12px; border: 1px solid rgba(0,229,255,0.15); box-shadow: 0 0 0 1px rgba(255,255,255,0.04) inset; }

    /* Mini stats */
    .mini-stats { font-size: 12px; color: var(--muted); margin-top: 6px; }

    /* Mini list styles for listeners */
    .mini-card { border: 1px solid rgba(0,229,255,0.25); border-radius: 12px; padding: 12px 14px; margin-bottom: 10px; background: linear-gradient(180deg, rgba(8,14,36,0.85), rgba(10,16,38,0.85)); box-shadow: var(--soft-glow); }
    .mini-card:hover { box-shadow: var(--glow); }
    .mini-title { font-weight: 700; font-size: 15px; margin: 0 0 6px 0; color: var(--text); text-shadow: 0 0 8px rgba(255,255,255,0.05); }
    .mini-sub { color: var(--muted); font-size: 12px; margin: 0; }
    .tag { display: inline-block; padding: 2px 10px; border-radius: 999px; font-size: 11px; margin-right: 8px; border: 1px solid rgba(0,229,255,0.35); color: var(--text); background: rgba(0,229,255,0.08); box-shadow: var(--soft-glow); }
    .tag-verified { border-color: rgba(57,255,20,0.45); background: rgba(57,255,20,0.12); box-shadow: 0 0 10px rgba(57,255,20,0.35); }
    .tag-unverified { border-color: rgba(255,0,255,0.45); background: rgba(255,0,255,0.10); box-shadow: 0 0 10px rgba(255,0,255,0.35); }
    .muted { color: var(--muted); font-size: 12px; }
    .truncate { display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

def fetch_data():
    try:
        verification_data = requests.get(VERIFY_API_URL).json()
    except Exception as e:
        st.error(f"Failed to fetch verification data: {e}")
        verification_data = {}

    try:
        stats_data = requests.get(STATS_API_URL).json()
    except Exception as e:
        st.error(f"Failed to fetch stats data: {e}")
        stats_data = {}

    return verification_data, stats_data


verification_data, stats_data = fetch_data()

# Extract verification info
unverified_listeners = verification_data.get("unverified_listeners", [])
verified_listeners = verification_data.get("verified_listeners", [])
total_unverified = verification_data.get("total_unverified_count", 0)
total_verified = verification_data.get("total_verified_count", 0)
total_all_listeners = total_unverified + total_verified

# Extract stats info
listeners_stats = stats_data.get("listeners", {})
users_stats = stats_data.get("users", {})


# ---------------- VERIFY DIALOG ----------------
@st.dialog("🔒 Verify Listener")
def verify_listener_dialog(listener):
    st.write(f"Are you sure you want to verify **{listener['username']}**?")
    st.markdown(
        f"🌍 **Country:** {listener['country']}  |  🗣️ **Language:** {listener['preferred_language']}"
    )
    st.markdown(f"[🎧 Listen to Audio]({listener['audio_file_url']})")

    if st.button("✅ Confirm Verification"):
        try:
            webhook_response = requests.post(
                WEBHOOK_URL, json={"user_id": listener["user_id"]}
            )
            if webhook_response.status_code == 200:
                st.success(
                    f"Listener **{listener['username']}** verified successfully!"
                )
            else:
                st.error(
                    f"❌ Failed ({webhook_response.status_code}) for {listener['username']}"
                )
        except Exception as e:
            st.error(f"Error: {e}")


# ---------------- PAGE 1: DASHBOARD ----------------
if page == "🏠 Home (Dashboard)":
    st.title("🏠 Saathii Admin Dashboard")
    st.markdown(
        "Welcome to **Saathii.com Admin Panel** — monitor your live platform stats here."
    )
    st.markdown("---")

    # ----------- SUMMARY COUNTS -----------
    st.subheader("📈 Platform Overview")

    col1, col2 = st.columns(2)

    # CUSTOMER STATS
    with col1:
        st.markdown("### 👤 Customers")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total", users_stats.get("total", 0))
        st.markdown(
            f"<div class='mini-stats'>Online: {users_stats.get('online', 0)} | Available: {users_stats.get('available', 0)} | Busy: {users_stats.get('busy', 0)}</div>",
            unsafe_allow_html=True,
        )

    # LISTENER STATS
    with col2:
        st.markdown("### 🎧 Listeners")
        l1, l2, l3, l4 = st.columns(4)
        l1.metric("Total", total_all_listeners)
        l2.metric("Verified", total_verified)
        l3.metric("Unverified", total_unverified)
        st.markdown(
            f"<div class='mini-stats'>Online: {listeners_stats.get('online', 0)} | Available: {listeners_stats.get('available', 0)} | Busy: {listeners_stats.get('busy', 0)}</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.subheader("🧠 Insights (Coming Soon)")
    st.info(
        """
        - Daily signup & verification trends  
        - Listener activity heatmap  
        - User engagement analytics  
        - AI-based listener verification suggestions  
        """
    )

# ---------------- PAGE 2: LISTENERS TABLE ----------------
elif page == "🎧 Listeners Table":
    st.title("🎧 Listener Verification Table")

    tab1, tab2 = st.tabs(
        [f"🔴 Unverified ({total_unverified})", f"🟢 Verified ({total_verified})"]
    )

    # ---------- UNVERIFIED ----------
    with tab1:
        st.subheader("Unverified Listeners")

        if not unverified_listeners:
            st.info("✅ No unverified listeners found.")
        else:
            df_unverified = pd.DataFrame(unverified_listeners)
            df_unverified = df_unverified[
                [
                    "user_id",
                    "username",
                    "sex",
                    "country",
                    "preferred_language",
                    "bio",
                    "audio_file_url",
                    "created_at",
                ]
            ]
            st.dataframe(df_unverified, use_container_width=True)

            st.markdown("### 🧾 Verify Listeners (Mini List)")

            # Pagination for unverified mini list
            page_size_unv = 10
            total_unv = len(unverified_listeners)
            total_pages_unv = (total_unv + page_size_unv - 1) // page_size_unv if total_unv else 1
            col_pu1, col_pu2 = st.columns([3, 1])
            with col_pu1:
                current_page_unv = st.number_input(
                    "Page",
                    min_value=1,
                    max_value=max(1, total_pages_unv),
                    value=1,
                    step=1,
                    key="unv_page_input",
                )
            with col_pu2:
                st.caption(f"{total_unv} items • {total_pages_unv} pages")

            start_unv = (int(current_page_unv) - 1) * page_size_unv
            end_unv = min(start_unv + page_size_unv, total_unv)
            for listener in unverified_listeners[start_unv:end_unv]:
                cc1, cc2 = st.columns([6, 2])
                with cc1:
                    st.markdown(
                        f"""
                        <div class='mini-card'>
                          <div class='mini-title'>👤 {listener.get('username','')}</div>
                          <p class='mini-sub'>
                            <span class='tag tag-unverified'>Unverified</span>
                            🌍 {listener.get('country','')} &nbsp; • &nbsp; 🗣️ {listener.get('preferred_language','')}
                          </p>
                          <p class='mini-sub truncate'>""" + (listener.get('bio','') or '') + """</p>
                          <p class='mini-sub'>🎧 <a href='""" + (listener.get('audio_file_url','') or '#') + """' target='_blank'>Listen audio</a></p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with cc2:
                    if st.button("✅ Verify", key=f"verify_{listener['user_id']}"):
                        verify_listener_dialog(listener)

    # ---------- VERIFIED ----------
    with tab2:
        st.subheader("Verified Listeners")
        if not verified_listeners:
            st.info("No verified listeners found.")
        else:
            df_verified = pd.DataFrame(verified_listeners)
            df_verified = df_verified[
                [
                    "user_id",
                    "username",
                    "sex",
                    "country",
                    "preferred_language",
                    "bio",
                    "audio_file_url",
                    "created_at",
                ]
            ]
            st.dataframe(df_verified, use_container_width=True)

            st.markdown("### 🗂️ Verified Listeners (Mini List)")

            # Pagination for verified mini list
            page_size_v = 10
            total_v = len(verified_listeners)
            total_pages_v = (total_v + page_size_v - 1) // page_size_v if total_v else 1
            col_pv1, col_pv2 = st.columns([3, 1])
            with col_pv1:
                current_page_v = st.number_input(
                    "Page ",
                    min_value=1,
                    max_value=max(1, total_pages_v),
                    value=1,
                    step=1,
                    key="v_page_input",
                )
            with col_pv2:
                st.caption(f"{total_v} items • {total_pages_v} pages")

            start_v = (int(current_page_v) - 1) * page_size_v
            end_v = min(start_v + page_size_v, total_v)
            for listener in verified_listeners[start_v:end_v]:
                cc1, cc2 = st.columns([6, 2])
                with cc1:
                    st.markdown(
                        f"""
                        <div class='mini-card'>
                          <div class='mini-title'>👤 {listener.get('username','')}</div>
                          <p class='mini-sub'>
                            <span class='tag tag-verified'>Verified</span>
                            🌍 {listener.get('country','')} &nbsp; • &nbsp; 🗣️ {listener.get('preferred_language','')}
                          </p>
                          <p class='mini-sub truncate'>""" + (listener.get('bio','') or '') + """</p>
                          <p class='mini-sub'>🎧 <a href='""" + (listener.get('audio_file_url','') or '#') + """' target='_blank'>Listen audio</a></p>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                with cc2:
                    st.markdown("<span class='muted'>No actions</span>", unsafe_allow_html=True)

# ---------------- FOOTER ----------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script&display=swap');
    .footer {
        text-align: center;
        font-family: 'Dancing Script', cursive;
        font-size: 26px;
        color: #999;
        margin-top: 30px;
    }
    </style>
    <div class='footer'>© 2025 saathii.com — Admin Dashboard</div>
    """,
    unsafe_allow_html=True,
)
