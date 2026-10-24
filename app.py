
import streamlit as st
import pandas as pd
from datetime import date
from supabase import create_client

st.set_page_config(
    page_title="Guardian 360 | LPG Safety",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {background:linear-gradient(135deg,#07111f,#0b1930);color:#f3f6fc}
.block-container {padding-top:2rem}
h1,h2,h3 {color:#f3f6fc}
[data-testid="stMetric"] {
 background:#12233b;border:1px solid #263d5b;
 padding:16px;border-radius:14px
}
</style>
""", unsafe_allow_html=True)

st.title("🛡️ GUARDIAN 360")
st.caption("INTELLIGENT LPG MONITORING · LEAK PREVENTION")

@st.cache_resource
def get_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

st.sidebar.header("Dashboard")
refresh = st.sidebar.button("🔄 Refresh readings")

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
    st.error("Could not load database readings. Check Streamlit Secrets and Supabase access.")
    st.caption(str(e))

if readings:
    latest = readings[0]
    device_id = latest.get("device_id", "Unknown")
    recorded_at = latest.get("recorded_at", "Unknown")
    status = latest.get("device_status", "UNKNOWN")
    leak = latest.get("leak_status", "UNKNOWN")

    st.info(
        f"Latest database record: {recorded_at} · Device: {device_id}. "
        "A database record alone does not prove the device is currently online."
    )

    if device_id == "guardian-360-esp32":
        st.warning(
            "Database records found. Until real ESP32 readings are verified, "
            "treat the values as unverified/test data."
        )

    st.subheader("Latest Recorded Readings")
    a, b, c, d = st.columns(4)

    temp = latest.get("temperature_c")
    humidity = latest.get("humidity_pct")
    weight = latest.get("cylinder_weight_kg")
    pct = latest.get("lpg_remaining_pct")

    a.metric("Temperature", f"{temp} °C" if temp is not None else "Waiting")
    b.metric("Humidity", f"{humidity} %" if humidity is not None else "Waiting")
    c.metric("Cylinder Weight", f"{weight} kg" if weight is not None else "Waiting")
    d.metric("LPG Remaining", f"{pct} %" if pct is not None else "Waiting")

    st.subheader("Safety Status")
    s1, s2, s3 = st.columns(3)
    s1.metric("Leak Status", leak)
    s2.metric("Valve Confirmed", str(latest.get("valve_confirmed", "Unknown")))
    s3.metric("Power Demo Output", str(latest.get("power_demo_on", "Unknown")))

    st.subheader("Sensor History")
    df = pd.DataFrame(readings)
    if "recorded_at" in df.columns:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download readings CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="guardian360_readings.csv",
            mime="text/csv"
        )
else:
    st.warning("WAITING FOR DEVICE DATA")
    st.write(
        "No readings are available, or the dashboard cannot access the table. "
        "Connect the ESP32 and configure secure read access."
    )

st.divider()
st.subheader("Cylinder Refill")
refill_date = st.date_input("Latest refill date", value=date.today())
st.caption(f"Selected refill date: {refill_date.strftime('%d %b %Y')}")

st.caption(
    "Prototype only. Database values may be test data. "
    "Never rely on this dashboard as a certified LPG safety system. "
    "Gas isolation must be independently verified by appropriate hardware."
)
