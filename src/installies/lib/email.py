import smtplib, ssl

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from installies.config import noreply_email, noreply_email_password, smtp_server, smtp_server_port

def send_email(to: str, body: str, subject: str):
    """Sends and email."""

    message = MIMEMultipart('alternative')
    message['Subject'] = subject
    message['From'] = noreply_email
    message['To'] = to

    message.attach(MIMEText(body, 'html'))
    
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, smtp_server_port, context=context) as server:
        server.login(noreply_email, noreply_email_password)
        server.sendmail(
            noreply_email,
            to,
            message.as_string(),
        )
