
import streamlit as st
import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import date

from supabase import create_client

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
.block-container {padding-top:2rem}
h1,h2,h3 {color:#f3f6fc}
[data-testid="stMetric"] {
    background:#12233b;
    border:1px solid #263d5b;
    padding:16px;
    border-radius:14px;
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ GUARDIAN 360")
st.caption("INTELLIGENT LPG MONITORING · LEAK PREVENTION")


# ---------------- SUPABASE ----------------

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_SERVICE_ROLE_KEY"]
    )


# ---------------- EMAIL ALERT ----------------

def send_email_alert(device_id, recorded_at, leak_status, flame_detected):
    
# ---------------- TEST EMAIL ----------------

st.sidebar.subheader("Email Testing")

if st.sidebar.button("📧 Send Test Email"):
    try:
        send_email_alert(
            "Guardian-360-Test",
            "Manual Test",
            "TEST ALERT",
            False
        )
        st.sidebar.success("Test email sent! Check your inbox.")
    except Exception as e:
        st.sidebar.error("Email failed.")
        st.sidebar.caption(str(e))

    msg = EmailMessage()

    msg["Subject"] = "🚨 LPG SAFETY ALERT - Guardian 360"
    msg["From"] = st.secrets["GMAIL_ADDRESS"]
    msg["To"] = st.secrets["ALERT_EMAIL"]

    msg.set_content(f"""
GUARDIAN 360 - SAFETY ALERT

An abnormal safety condition has been reported.

Device ID: {device_id}
Recorded At: {recorded_at}
Leak Status: {leak_status}
Flame Detected: {flame_detected}

Please check the LPG system immediately.

This is an automated prototype notification.
Do not rely on this email as the only safety mechanism.
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            st.secrets["GMAIL_ADDRESS"],
            st.secrets["GMAIL_APP_PASSWORD"]
        )
        smtp.send_message(msg)


def is_true(value):
    return str(value).strip().lower() in (
        "true", "1", "yes", "on", "detected"
    )


def is_leak(value):
    return str(value).strip().lower() in (
        "leak", "detected", "warning", "danger",
        "alert", "unsafe", "gas leak"
    )


# ---------------- SIDEBAR ----------------

st.sidebar.header("Dashboard")
st.sidebar.button("🔄 Refresh readings")


# ---------------- LOAD DATABASE ----------------

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
    st.error("Could not load database readings.")
    st.caption(str(e))


# ---------------- DISPLAY READINGS ----------------

if readings:

    latest = readings[0]

    device_id = latest.get("device_id", "Unknown")
    recorded_at = latest.get("recorded_at", "Unknown")
    status = latest.get("device_status", "UNKNOWN")
    leak = latest.get("leak_status", "UNKNOWN")
    flame = latest.get("flame_detected", False)

    st.info(
        f"Latest database record: {recorded_at} · "
        f"Device: {device_id}"
    )

    if device_id == "guardian-360-esp32":
        st.warning(
            "Verify that these readings are coming from your real ESP32."
        )

    # ---------------- EMAIL TRIGGER ----------------

    alert_detected = is_leak(leak) or is_true(flame)

    alert_id = (
        f"{device_id}_{recorded_at}_{leak}_{flame}"
    )

    if "last_email_alert_id" not in st.session_state:
        st.session_state.last_email_alert_id = None

    if alert_detected:

        st.error("🚨 SAFETY ALERT DETECTED")

        if st.session_state.last_email_alert_id != alert_id:

            try:
                send_email_alert(
                    device_id,
                    recorded_at,
                    leak,
                    flame
                )

                st.session_state.last_email_alert_id = alert_id
                st.success("Safety alert email sent successfully.")

            except Exception as e:
                st.error("Email could not be sent.")
                st.caption(str(e))

        else:
            st.info("Email already sent for this reading.")

    else:
        st.success("✅ No leak or flame alert in the latest reading.")

    # ---------------- METRICS ----------------

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

    # ---------------- SAFETY STATUS ----------------

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

    # ---------------- HISTORY ----------------

    st.subheader("Sensor History")

    df = pd.DataFrame(readings)

    if "recorded_at" in df.columns:

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "⬇️ Download readings CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="guardian360_readings.csv",
            mime="text/csv"
        )

else:

    st.warning("WAITING FOR DEVICE DATA")

    st.write(
        "No readings are available, or the dashboard cannot access the table."
    )


# ---------------- REFILL DATE ----------------

st.divider()

st.subheader("Cylinder Refill")

refill_date = st.date_input(
    "Latest refill date",
    value=date.today()
)

st.caption(
    f"Selected refill date: {refill_date.strftime('%d %b %Y')}"
)


# ---------------- FOOTER ----------------

st.caption(
    "Prototype only. Database values may be test data. "
    "Never rely on this dashboard as a certified LPG safety system. "
    "Gas isolation must be independently verified by appropriate hardware."
)
