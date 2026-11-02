
def send_email_alert(device_id, recorded_at, leak_status, flame_detected):
    msg = EmailMessage()

    msg["Subject"] = "LPG SAFETY ALERT - Guardian 360"
    msg["From"] = st.secrets["GMAIL_ADDRESS"]
    msg["To"] = st.secrets["ALERT_EMAIL"]

    msg.set_content(f"""
GUARDIAN 360 - SAFETY ALERT

Device ID: {device_id}
Recorded At: {recorded_at}
Leak Status: {leak_status}
Flame Detected: {flame_detected}

This is an automated prototype notification.
""")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(
            st.secrets["GMAIL_ADDRESS"],
            st.secrets["GMAIL_APP_PASSWORD"]
        )
        smtp.send_message(msg)


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
        st.sidebar.success("Test email sent!")
    except Exception as e:
        st.sidebar.error("Email failed.")
        st.sidebar.caption(str(e))
