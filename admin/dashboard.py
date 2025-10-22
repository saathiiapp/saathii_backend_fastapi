import streamlit as st
import requests
import pandas as pd
import asyncio
import websockets
import json

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Saathii Admin Dashboard", layout="wide")

VERIFY_API_URL = "http://api:8000/admin/verification/pending"
WEBHOOK_URL = "http://api:8000/admin/verification/webhook"
STATS_API_URL = "http://api:8000/both/feed/stats"
USERS_API_URL = "http://api:8000/admin/users"
USER_STATUS_API_URL = "http://api:8000/admin/users/status"
WS_VERIFICATION_URL = "ws://api:8000/ws/verification"

# ---------------- SIDEBAR NAV ----------------
st.sidebar.title("📊 Saathii Admin")
page = st.sidebar.radio(
    "Navigate", ["🏠 Home (Dashboard)", "🎧 Listeners Verification", "👥 User Management"], index=0
)
st.sidebar.markdown("---")
st.sidebar.info(
    "Clean admin interface for user management, verifications, and platform monitoring."
)


# ---------------- FETCH DATA ----------------
st.markdown(
    """
    <style>
    /* ========== MINIMALIST THEME UI ========== */
    :root {
        --bg-primary: #ffffff;
        --bg-secondary: #f8f9fa;
        --bg-tertiary: #f1f3f4;
        --text-primary: #2d3748;
        --text-secondary: #718096;
        --text-accent: #3182ce;
        --accent-blue: #3182ce;
        --accent-green: #38a169;
        --accent-red: #e53e3e;
        --accent-orange: #dd6b20;
        --border-light: #e2e8f0;
        --border-medium: #cbd5e0;
        --shadow-sm: 0 1px 3px rgba(0,0,0,0.1);
        --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
        --shadow-lg: 0 10px 15px rgba(0,0,0,0.1);
    }

    /* Main App Styling */
    .stApp {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    .stApp > div {
        background: transparent !important;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background: var(--bg-primary) !important;
        border-right: 1px solid var(--border-light) !important;
        box-shadow: var(--shadow-md) !important;
    }

    section[data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    /* Headers and Text */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        margin-bottom: 0.5rem !important;
    }

    .stMarkdown, .stText, .stSubheader, .stHeader, .stCaption {
        color: var(--text-primary) !important;
    }

    /* Buttons */
    .stButton > button {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-medium) !important;
        border-radius: 6px !important;
        box-shadow: var(--shadow-sm) !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        padding: 8px 16px !important;
    }

    .stButton > button:hover {
        background: var(--bg-secondary) !important;
        border-color: var(--accent-blue) !important;
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-1px) !important;
    }

    .stButton > button:active {
        transform: translateY(0) !important;
    }

    /* Primary Buttons */
    .stButton > button[kind="primary"] {
        background: var(--accent-blue) !important;
        color: white !important;
        border-color: var(--accent-blue) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stButton > button[kind="primary"]:hover {
        background: #2c5aa0 !important;
        box-shadow: var(--shadow-md) !important;
    }

    /* Selectboxes and Inputs */
    .stSelectbox > div > div {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-medium) !important;
        border-radius: 6px !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stSelectbox > div > div > div {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    .stSelectbox label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    .stTextInput > div > div > input {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-medium) !important;
        border-radius: 6px !important;
        color: var(--text-primary) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stTextInput label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    /* Radio Buttons */
    .stRadio > div {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 6px !important;
        padding: 12px !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stRadio label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    /* Tabs */
    div[role="tablist"] > div {
        gap: 4px !important;
        background: var(--bg-secondary) !important;
        padding: 4px !important;
        border-radius: 8px !important;
        border: 1px solid var(--border-light) !important;
    }

    div[role="tab"] {
        background: transparent !important;
        color: var(--text-secondary) !important;
        border: 1px solid transparent !important;
        border-radius: 6px !important;
        font-weight: 500 !important;
        transition: all 0.2s ease !important;
        padding: 8px 16px !important;
    }

    div[role="tab"][aria-selected="true"] {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        box-shadow: var(--shadow-sm) !important;
        border-color: var(--border-medium) !important;
    }

    div[role="tab"]:hover {
        background: var(--bg-tertiary) !important;
        color: var(--text-primary) !important;
    }

    /* DataFrames */
    .stDataFrame {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 8px !important;
        box-shadow: var(--shadow-sm) !important;
        overflow: hidden !important;
    }

    .stDataFrame table {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    .stDataFrame th {
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-light) !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
    }

    .stDataFrame td {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-light) !important;
    }

    .stDataFrame tr:hover {
        background: var(--bg-secondary) !important;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 8px !important;
        padding: 16px !important;
        box-shadow: var(--shadow-sm) !important;
        text-align: center !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--text-primary) !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }

    /* Expanders */
    .stExpander {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 8px !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stExpander > div > div {
        background: var(--bg-primary) !important;
        color: var(--text-primary) !important;
    }

    /* Toggle Switches */
    .stToggle {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 8px !important;
        padding: 12px !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stToggle > label {
        color: var(--text-primary) !important;
        font-weight: 500 !important;
    }

    /* Success/Error Messages */
    .stSuccess {
        background: #f0fff4 !important;
        color: #22543d !important;
        border: 1px solid #9ae6b4 !important;
        border-radius: 6px !important;
        box-shadow: var(--shadow-sm) !important;
        font-weight: 500 !important;
    }

    .stError {
        background: #fed7d7 !important;
        color: #742a2a !important;
        border: 1px solid #feb2b2 !important;
        border-radius: 6px !important;
        box-shadow: var(--shadow-sm) !important;
        font-weight: 500 !important;
    }

    .stInfo {
        background: #ebf8ff !important;
        color: #2a4365 !important;
        border: 1px solid #90cdf4 !important;
        border-radius: 6px !important;
        box-shadow: var(--shadow-sm) !important;
        font-weight: 500 !important;
    }

    .stWarning {
        background: #fef5e7 !important;
        color: #744210 !important;
        border: 1px solid #fbd38d !important;
        border-radius: 6px !important;
        box-shadow: var(--shadow-sm) !important;
        font-weight: 500 !important;
    }

    /* Links */
    a {
        color: var(--accent-blue) !important;
        text-decoration: none !important;
        transition: all 0.2s ease !important;
    }

    a:hover {
        color: #2c5aa0 !important;
        text-decoration: underline !important;
    }

    /* Horizontal Rules */
    hr {
        border: 1px solid var(--border-light) !important;
        margin: 20px 0 !important;
    }

    /* Custom Cards */
    .mini-card {
        background: var(--bg-primary) !important;
        border: 1px solid var(--border-light) !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        box-shadow: var(--shadow-sm) !important;
        transition: all 0.2s ease !important;
    }

    .mini-card:hover {
        box-shadow: var(--shadow-md) !important;
        transform: translateY(-2px) !important;
    }

    .mini-title {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        margin-bottom: 8px !important;
    }

    .mini-sub {
        color: var(--text-secondary) !important;
        font-size: 14px !important;
        margin: 4px 0 !important;
    }

    /* Tags */
    .tag {
        display: inline-block !important;
        padding: 4px 12px !important;
        border-radius: 16px !important;
        font-size: 12px !important;
        margin-right: 8px !important;
        margin-bottom: 4px !important;
        border: 1px solid var(--border-medium) !important;
        color: var(--text-secondary) !important;
        background: var(--bg-secondary) !important;
        font-weight: 500 !important;
    }

    .tag-verified {
        border-color: var(--accent-green) !important;
        color: var(--accent-green) !important;
        background: #f0fff4 !important;
    }

    .tag-unverified {
        border-color: var(--accent-red) !important;
        color: var(--accent-red) !important;
        background: #fed7d7 !important;
    }

    /* Fade inactive user rows */
    .inactive-row {
        opacity: 0.4 !important;
        background: var(--bg-tertiary) !important;
    }
    .inactive-row td {
        background: var(--bg-tertiary) !important;
        color: var(--text-secondary) !important;
    }

    /* Footer */
    .footer {
        text-align: center !important;
        padding: 24px 0 !important;
        margin-top: 40px !important;
        border-top: 1px solid var(--border-light) !important;
        color: var(--text-secondary) !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }

    /* Scrollbar Styling */
    ::-webkit-scrollbar {
        width: 8px !important;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-secondary) !important;
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-medium) !important;
        border-radius: 4px !important;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent-blue) !important;
    }

    /* Responsive Design */
    @media (max-width: 768px) {
        .stButton > button {
            font-size: 14px !important;
            padding: 6px 12px !important;
        }
        
        [data-testid="stMetricValue"] {
            font-size: 1.25rem !important;
        }
    }
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


# ---------------- WEBSOCKET PRODUCER ----------------
async def send_verification_event(listener_id, verification_message="Approved by admin"):
    """Send verification event via websocket"""
    try:
        async with websockets.connect(WS_VERIFICATION_URL) as websocket:
            event = {
                "listener_id": listener_id,
                "verification_status": True,
                "verification_message": verification_message
            }
            await websocket.send(json.dumps(event))
            print(f"Sent verification event: {event}")
            return True
    except Exception as e:
        print(f"Websocket error: {e}")
        return False

def verify_listener_websocket(listener_id, verification_message="Approved by admin"):
    """Synchronous wrapper for websocket verification"""
    try:
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(send_verification_event(listener_id, verification_message))
        loop.close()
        return result
    except Exception as e:
        print(f"Error in websocket verification: {e}")
        return False

# ---------------- VERIFY DIALOG ----------------
def verify_listener_dialog(listener):
    st.write(f"Are you sure you want to verify **{listener['username']}**?")
    st.markdown(
        f"🌍 **Country:** {listener['country']}  |  🗣️ **Language:** {listener['preferred_language']}"
    )
    st.markdown(f"[🎧 Listen to Audio]({listener['audio_file_url']})")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm Verification", type="primary"):
            try:
                # Send verification event via websocket
                success = verify_listener_websocket(
                    listener["user_id"], 
                    f"Approved by admin - {listener['username']}"
                )
                
                if success:
                    st.success(
                        f"Listener **{listener['username']}** verified successfully via websocket!"
                    )
                    st.rerun()
                else:
                    st.error(
                        f"❌ Failed to send verification event for {listener['username']}"
                    )
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        if st.button("❌ Cancel"):
            st.rerun()


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
                        st.session_state[f"show_dialog_{listener['user_id']}"] = True
                        st.rerun()
                
                # Show dialog if triggered
                if st.session_state.get(f"show_dialog_{listener['user_id']}", False):
                    with st.expander(f"🔒 Verify {listener['username']}", expanded=True):
                        verify_listener_dialog(listener)
                        if st.button("❌ Close", key=f"close_{listener['user_id']}"):
                            st.session_state[f"show_dialog_{listener['user_id']}"] = False
                            st.rerun()

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

# ---------------- PAGE 3: USER MANAGEMENT ----------------
elif page == "👥 User Management":
    st.title("👥 User Management")
    st.markdown("Manage all users (customers and listeners) with active/inactive status controls.")
    st.markdown("---")

    # Filters
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        role_filter = st.selectbox("Role", ["All", "Customer", "Listener"], index=0)

    with col2:
        status_filter = st.selectbox("Status", ["All", "Active", "Inactive"], index=0)

    with col3:
        search_username = st.text_input("Search Username", placeholder="Enter username to search...")

    with col4:
        sort_by = st.selectbox("Sort By", ["created_at", "username", "user_id"], index=0)
    
    # Build API parameters
    params = {
        "page": 1,
        "per_page": 50,
        "sort_by": sort_by,
        "sort_order": "desc"
    }

    if role_filter != "All":
        params["role"] = role_filter.lower()

    if status_filter != "All":
        params["is_active"] = status_filter == "Active"

    if search_username and search_username.strip():
        params["search"] = search_username.strip()
    
    # Fetch users data
    try:
        response = requests.get(USERS_API_URL, params=params)
        if response.status_code == 200:
            users_data = response.json()
            users = users_data.get("users", [])
            total_count = users_data.get("total_count", 0)
            
            # Display search results info
            if search_username and search_username.strip():
                st.subheader(f"Search Results for '{search_username}' ({total_count} found)")
            else:
                st.subheader(f"Users ({total_count} total)")

            if users:
                # Create DataFrame for display
                df_data = []
                for user in users:
                    roles_str = ", ".join(user.get("roles", []))
                    status_text = "🟢 Active" if user.get("is_active") else "🔴 Inactive"
                    online_text = "🟢 Online" if user.get("is_online") else "⚪ Offline"
                    verified_text = "✅ Verified" if user.get("is_verified") else "⏳ Pending" if user.get("is_verified") is False else "N/A"
                    
                    df_data.append({
                        "User ID": user.get("user_id"),
                        "Username": user.get("username", "N/A"),
                        "Phone": user.get("phone"),
                        "Roles": roles_str,
                        "Status": status_text,
                        "Online": online_text,
                        "Verified": verified_text if "listener" in user.get("roles", []) else "N/A",
                        "Country": user.get("country", "N/A"),
                        "Created": user.get("created_at", "N/A")[:10] if user.get("created_at") else "N/A",
                        "is_active": user.get("is_active")  # Keep this for styling
                    })
                
                df = pd.DataFrame(df_data)
                
                # Display the table with custom styling for inactive rows
                st.dataframe(
                    df.drop(columns=['is_active']),  # Hide the is_active column from display
                    use_container_width=True,
                    hide_index=True
                )
                
                # Add custom styling for inactive rows using st.markdown
                if not df.empty:
                    st.markdown(
                        """
                        <script>
                        // Apply faded styling to inactive rows
                        setTimeout(function() {
                            const table = document.querySelector('[data-testid="stDataFrame"] table');
                            if (table) {
                                const rows = table.querySelectorAll('tbody tr');
                                rows.forEach((row, index) => {
                                    const isActive = """ + str(df['is_active'].tolist()).replace("'", '"') + """[index];
                                    if (!isActive) {
                                        row.style.opacity = '0.5';
                                        row.style.backgroundColor = '#f8f9fa';
                                        const cells = row.querySelectorAll('td');
                                        cells.forEach(cell => {
                                            cell.style.backgroundColor = '#f8f9fa';
                                            cell.style.color = '#6c757d';
                                        });
                                    }
                                });
                            }
                        }, 100);
                        </script>
                        """,
                        unsafe_allow_html=True
                    )
                
                # User management controls
                st.markdown("### 🔧 User Status Management")
                
                # Create columns for user selection and status toggle
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # User selection dropdown
                    user_options = {}
                    for user in users:
                        username = user.get('username') or f"User {user['user_id']}"
                        display_name = f"{username} (ID: {user['user_id']})"
                        user_options[display_name] = user['user_id']
                    selected_user = st.selectbox("Select User to Manage", list(user_options.keys()))
                    selected_user_id = user_options[selected_user]
                
                with col2:
                    # Find current status of selected user
                    current_user = next((u for u in users if u['user_id'] == selected_user_id), None)
                    if current_user:
                        current_status = current_user.get('is_active', False)
                        new_status = st.toggle(
                            "Active Status", 
                            value=current_status,
                            help="Toggle to activate/deactivate user account"
                        )
                        
                        if new_status != current_status:
                            if st.button("Update Status", type="primary"):
                                # Update user status
                                update_data = {
                                    "user_id": selected_user_id,
                                    "is_active": new_status
                                }
                                
                                try:
                                    update_response = requests.put(USER_STATUS_API_URL, json=update_data)
                                    if update_response.status_code == 200:
                                        result = update_response.json()
                                        st.success(f"✅ {result.get('message', 'Status updated successfully')}")
                                        st.rerun()  # Refresh the page to show updated data
                                    else:
                                        st.error(f"❌ Failed to update status: {update_response.text}")
                                except Exception as e:
                                    st.error(f"❌ Error updating status: {str(e)}")
                    else:
                        st.warning("User not found in current view")
                
                # Pagination info
                st.markdown(f"**Showing {len(users)} of {total_count} users**")
                
            else:
                if search_username and search_username.strip():
                    st.info(f"No users found matching username '{search_username}' with current filters.")
                else:
                    st.info("No users found matching the current filters.")
                
        else:
            st.error(f"Failed to fetch users data: {response.status_code} - {response.text}")
            
    except Exception as e:
        st.error(f"Error fetching users data: {str(e)}")

# ---------------- FOOTER ----------------
st.markdown("---")
st.markdown("© 2025 Saathii Admin Dashboard")
