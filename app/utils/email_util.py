import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings


def _build_html_template(code: str, minutes: int, app_name: str) -> str:
    return f"""
    <html>
    <body style="margin:0;padding:0;background:#f4f6f8;font-family:Arial,sans-serif;">
        <table width="100%" cellpadding="0" cellspacing="0" style="padding:20px 0;">
            <tr>
                <td align="center">
                    <table width="600" style="background:#ffffff;border-radius:8px;padding:30px;">
                        
                        <tr>
                            <td style="font-size:20px;font-weight:bold;color:#333;">
                                {app_name} Verification Code
                            </td>
                        </tr>

                        <tr><td style="height:20px;"></td></tr>

                        <tr>
                            <td style="font-size:14px;color:#666;">
                                Your verification code is:
                            </td>
                        </tr>

                        <tr><td style="height:10px;"></td></tr>

                        <tr>
                            <td align="center">
                                <div style="
                                    font-size:32px;
                                    font-weight:bold;
                                    letter-spacing:6px;
                                    color:#111;
                                    padding:15px 0;
                                    border:1px dashed #ddd;
                                    border-radius:6px;
                                    width:200px;
                                ">
                                    {code}
                                </div>
                            </td>
                        </tr>

                        <tr><td style="height:20px;"></td></tr>

                        <tr>
                            <td style="font-size:12px;color:#999;">
                                This code is valid for {minutes} minutes. Please do not share it with anyone.
                            </td>
                        </tr>

                        <tr><td style="height:30px;"></td></tr>

                        <tr>
                            <td style="font-size:12px;color:#bbb;">
                                © {app_name}. All rights reserved.
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def send_verification_email(to_email: str, code: str, app_code: str):
    random_id = str(uuid.uuid4())[:8]

    app_name = app_code.capitalize()

    # ✅ subject 完全内部生成
    subject = f"[{app_code}] Verification Code (reqid={random_id})"

    minutes = settings.verification_code_ttl_seconds // 60

    html_content = _build_html_template(
        code=code,
        minutes=minutes,
        app_name=app_name
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.email_sender
    msg["To"] = to_email

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    server = smtplib.SMTP_SSL(settings.email_smtp_host, settings.email_smtp_port)
    server.login(settings.email_sender, settings.email_password)
    server.sendmail(settings.email_sender, [to_email], msg.as_string())
    server.quit()