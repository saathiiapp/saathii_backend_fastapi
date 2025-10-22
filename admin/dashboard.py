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
    .mini-stats { font-size: 12px; color: #666; margin-top: 6px; }
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

            st.markdown("### 🧾 Verify Listeners")

            for listener in unverified_listeners:
                col1, col2, col3, col4 = st.columns([2, 2, 4, 2])
                with col1:
                    st.markdown(f"**👤 {listener['username']}**")
                with col2:
                    st.markdown(f"🌍 {listener['country']}")
                with col3:
                    st.markdown(f"[🎧 Listen Audio]({listener['audio_file_url']})")
                with col4:
                    if st.button(
                        "✅ Verify Listener", key=f"verify_{listener['user_id']}"
                    ):
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
