import smtplib
from email.mime.text import MIMEText

smtp_host = "smtp.gmail.com"
smtp_port = 587
smtp_user = "testermoolya3@gmail.com"
smtp_pass = "jhsm rsle tfjk pxoc"

msg = MIMEText("Test message body")
msg["Subject"] = "Test Email"
msg["From"] = smtp_user
msg["To"] = "testermoolya3@gmail.com"

with smtplib.SMTP(smtp_host, smtp_port) as server:
    server.starttls()
    server.login(smtp_user, smtp_pass)
    server.sendmail(smtp_user, "testermoolya3@gmail.com", msg.as_string())

print("✅ Manual test email sent!")
