
import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import date
from supabase import create_client

# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Guardian 360 | LPG Safety",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg,#07111f,#0b1930);
    color: #f3f6fc;
}
.block-container {
    padding-top: 2rem;
}
h1,h2,h3 {
    color: #f3f6fc;
}
[data-testid="stMetric"] {
    background: #12233b;
    border: 1px solid #263d5b;
    padding: 16px;
    border-radius: 14px;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ GUARDIAN 360")
st.caption("INTELLIGENT LPG MONITORING · LEAK PREVENTION")


# ==================================================
# SUPABASE CONNECTION
# ==================================================

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    )


# ==================================================
# EMAIL RECIPIENTS
# ==================================================

def get_email_recipients():
    return [
        email.strip()
        for email in st.secrets["ALERT_EMAIL"].split(",")
        if email.strip()
    ]


# ==================================================
# EMAIL NOTIFICATION
# ==================================================

def send_email_alert(device_id, recorded_at, leak_status, flame_detected):

    recipients = get_email_recipients()

    if not recipients:
        raise ValueError("No email recipients configured.")

    msg = EmailMessage()

    msg["Subject"] = "LPG SAFETY ALERT - Guardian 360"
    msg["From"] = st.secrets["GMAIL_ADDRESS"]
    msg["To"] = ", ".join(recipients)

    msg.set_content(f"""
GUARDIAN 360 - SAFETY NOTIFICATION

An abnormal safety condition has been reported.

Device ID: {device_id}
Recorded At: {recorded_at}
Leak Status: {leak_status}
Flame Detected: {flame_detected}

Please check the LPG system immediately.

This is an automated prototype notification.
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:

        smtp.login(
            st.secrets["GMAIL_ADDRESS"],
            st.secrets["GMAIL_APP_PASSWORD"]
        )

        smtp.send_message(
            msg,
            to_addrs=recipients
        )


# ==================================================
# SIDEBAR
# ==================================================

st.sidebar.header("Guardian 360 Controls")

if st.sidebar.button("🔄 Refresh Readings"):
    st.rerun()


# ==================================================
# TEST EMAIL
# ==================================================

st.sidebar.divider()
st.sidebar.subheader("📧 Email Testing")

if st.sidebar.button("Send Test Email"):

    try:

        send_email_alert(
            "Guardian-360-Test",
            "Manual Test",
            "TEST ALERT",
            False
        )

        st.sidebar.success(
            "Test email sent to both recipients!"
        )

    except Exception as e:

        st.sidebar.error("Email sending failed.")
        st.sidebar.caption(str(e))


# ==================================================
# DATABASE READINGS
# ==================================================

try:

    db = get_supabase()

    result = (
        db.table("sensor_readings")
        .select("*")
        .order("recorded_at", desc=True)
        .limit(100)
        .execute()
    )

    readings = result.data or []

except Exception as e:

    readings = []

    st.error("Could not load Supabase readings.")
    st.caption(str(e))


# ==================================================
# ALERT DETECTION
# ==================================================

if readings:

    latest = readings[0]

    device_id = latest.get("device_id", "Unknown")
    recorded_at = latest.get("recorded_at", "Unknown")

    leak = latest.get("leak_status", "UNKNOWN")
    flame = latest.get("flame_detected", False)

    st.info(
        f"Latest record: {recorded_at} | Device: {device_id}"
    )

    leak_detected = str(leak).strip().lower() in [
        "leak",
        "detected",
        "warning",
        "danger",
        "alert",
        "unsafe",
        "gas leak",
        "true",
        "1"
    ]

    flame_detected = str(flame).strip().lower() in [
        "true",
        "1",
        "yes",
        "on",
        "detected"
    ]

    if leak_detected or flame_detected:

        st.error("🚨 SAFETY ALERT DETECTED!")

        alert_id = (
            f"{device_id}_{recorded_at}_{leak}_{flame}"
        )

        if st.session_state.get("last_email_alert_id") != alert_id:

            try:

                send_email_alert(
                    device_id,
                    recorded_at,
                    leak,
                    flame
                )

                st.session_state.last_email_alert_id = alert_id

                st.success(
                    "Safety email sent to both recipients."
                )

            except Exception as e:

                st.error("Could not send safety email.")
                st.caption(str(e))

    else:

        st.success(
            "✅ No safety alert in the latest database reading."
        )


    # ==================================================
    # SENSOR VALUES
    # ==================================================

    st.subheader("Latest Recorded Readings")

    a, b, c, d = st.columns(4)

    temp = latest.get("temperature_c")
    humidity = latest.get("humidity_pct")
    weight = latest.get("cylinder_weight_kg")
    pct = latest.get("lpg_remaining_pct")

    a.metric(
        "Temperature",
        f"{temp} °C" if temp is not None else "Waiting"
    )

    b.metric(
        "Humidity",
        f"{humidity} %" if humidity is not None else "Waiting"
    )

    c.metric(
        "Cylinder Weight",
        f"{weight} kg" if weight is not None else "Waiting"
    )

    d.metric(
        "LPG Remaining",
        f"{pct} %" if pct is not None else "Waiting"
    )


    # ==================================================
    # SAFETY STATUS
    # ==================================================

    st.subheader("Safety Status")

    s1, s2, s3 = st.columns(3)

    s1.metric("Leak Status", str(leak))

    s2.metric(
        "Valve Confirmed",
        str(latest.get("valve_confirmed", "Unknown"))
    )

    s3.metric(
        "Power Demo Output",
        str(latest.get("power_demo_on", "Unknown"))
    )


    # ==================================================
    # SENSOR HISTORY
    # ==================================================

    st.subheader("Sensor History")

    df = pd.DataFrame(readings)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    st.download_button(
        "⬇️ Download Readings CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="guardian360_readings.csv",
        mime="text/csv"
    )

else:

    st.warning("WAITING FOR DEVICE DATA")

    st.write(
        "No sensor records are currently available from Supabase."
    )


# ==================================================
# CYLINDER REFILL
# ==================================================

st.divider()

st.subheader("Cylinder Refill")

refill_date = st.date_input(
    "Latest Refill Date",
    value=date.today()
)

st.caption(
    f"Selected refill date: {refill_date.strftime('%d %b %Y')}"
)


# ==================================================
# FOOTER
# ==================================================

st.divider()

st.caption("""
Guardian 360 | LPG Monitoring and Leak Prevention Prototype.

This dashboard is not a certified LPG safety system.
Never rely on email notifications or dashboard readings as
the sole means of detecting leaks or isolating gas.
""")
