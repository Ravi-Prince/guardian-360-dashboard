
import streamlit as st
import pandas as pd
from datetime import datetime, date

st.set_page_config(
    page_title="Guardian 360 | LPG Safety",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #07111f, #0b1930);
    color: #f3f6fc;
}
.block-container { padding-top: 2rem; }
h1, h2, h3 { color: #f3f6fc; }
[data-testid="stMetric"] {
    background: #12233b;
    border: 1px solid #263d5b;
    padding: 18px;
    border-radius: 14px;
}
.status {
    background: #182b43;
    border: 1px solid #36506f;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 14px;
}
.small { color: #9fb3cc; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ GUARDIAN 360")
st.caption("INTELLIGENT LPG MONITORING · LEAK PREVENTION · SAFETY STATUS")

st.markdown("""
<div class="status">
    <strong>● DEVICE CONNECTION: WAITING FOR DEVICE DATA</strong><br>
    <span class="small">No live sensor readings received yet. Connect the ESP32 before relying on readings.</span>
</div>
""", unsafe_allow_html=True)

st.subheader("Live Safety Overview")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Cylinder Level", "Waiting", "No live data")
c2.metric("Gas Status", "UNKNOWN", "Sensor data pending")
c3.metric("Temperature", "Waiting", "No live data")
c4.metric("Power Demo", "UNKNOWN", "Output state unconfirmed")

st.divider()

left, right = st.columns(2)

with left:
    st.subheader("⚖️ Cylinder & Refill")
    st.info("Cylinder weight and LPG percentage will appear after the load cell is calibrated and connected.")
    refill_date = st.date_input(
        "Date of latest cylinder refill",
        value=date.today(),
        help="Update this when you replace or refill the cylinder."
    )
    if st.button("Save refill date", use_container_width=True):
        st.session_state["refill_date"] = refill_date
        st.success(f"Refill date saved: {refill_date.strftime('%d %b %Y')}")
    if "refill_date" in st.session_state:
        st.caption(
            "Latest refill: " +
            st.session_state["refill_date"].strftime("%d %b %Y")
        )
    st.warning("Refill prediction unavailable until real weight history is collected.")

with right:
    st.subheader("🚨 Safety & Isolation")
    st.markdown("""
    <div class="status">
        <strong>Gas leak detection</strong><br>
        <span class="small">UNKNOWN — waiting for sensor data</span>
    </div>
    <div class="status">
        <strong>Servo valve isolation</strong><br>
        <span class="small">UNCONFIRMED — hardware feedback not received</span>
    </div>
    <div class="status">
        <strong>Power isolation demonstration</strong><br>
        <span class="small">UNCONFIRMED — ESP32 output feedback pending</span>
    </div>
    """, unsafe_allow_html=True)

st.divider()

st.subheader("📡 Sensor Health")
s1, s2, s3, s4 = st.columns(4)
s1.metric("MQ Gas Sensors", "Pending")
s2.metric("Load Cell / HX711", "Pending")
s3.metric("DHT11", "Pending")
s4.metric("Vibration Sensor", "Pending")

st.divider()

st.subheader("📋 Event History")
st.caption("Leak alerts, device disconnections, isolation events and weight history will appear here after the cloud connection is configured.")

events = pd.DataFrame(columns=[
    "Timestamp", "Event", "Status", "Details"
])
st.dataframe(events, use_container_width=True, hide_index=True)

st.download_button(
    "⬇️ Download event history (CSV)",
    data=events.to_csv(index=False).encode("utf-8"),
    file_name="guardian360_events.csv",
    mime="text/csv",
    use_container_width=True
)

st.divider()
st.caption(
    "GUARDIAN 360 · Prototype monitoring dashboard. "
    "This interface does not certify that gas or electrical power has been isolated. "
    "Keep independent, certified safety devices in service."
)
