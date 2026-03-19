import os
import asyncio
from typing import Optional

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@shopflow.com")
FROM_NAME = os.getenv("FROM_NAME", "ShopFlow")

async def send_email(to: str, subject: str, html: str):
    """Send email via SMTP. Logs to console if SMTP not configured."""
    if not SMTP_HOST or not SMTP_PASSWORD:
        print(f"\n📧 EMAIL (not sent — SMTP not configured)\nTo: {to}\nSubject: {subject}\n")
        return True
    try:
        import aiosmtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{FROM_NAME} <{FROM_EMAIL}>"
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))
        await aiosmtplib.send(msg, hostname=SMTP_HOST, port=SMTP_PORT,
                              username=SMTP_USER, password=SMTP_PASSWORD, start_tls=True)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

async def send_order_confirmation(to: str, name: str, order: dict):
    items_html = "".join(
        f"<tr><td style='padding:8px;border-bottom:1px solid #eee'>{i['name']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:center'>{i['quantity']}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:right'>${i['price']:.2f}</td></tr>"
        for i in order.get("items", [])
    )
    html = f"""
    <div style="font-family:Georgia,serif;max-width:600px;margin:0 auto;background:#fff">
      <div style="background:#0a0a0a;padding:32px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:28px;letter-spacing:4px">SHOPFLOW</h1>
      </div>
      <div style="padding:40px">
        <h2 style="color:#0a0a0a;font-size:22px">Order Confirmed</h2>
        <p style="color:#555">Hi {name}, your order <strong>#{order['_id'][:8].upper()}</strong> has been placed successfully.</p>
        <table style="width:100%;border-collapse:collapse;margin:24px 0">
          <thead><tr style="background:#f5f5f5">
            <th style="padding:10px;text-align:left">Item</th>
            <th style="padding:10px;text-align:center">Qty</th>
            <th style="padding:10px;text-align:right">Price</th>
          </tr></thead>
          <tbody>{items_html}</tbody>
        </table>
        <div style="text-align:right;font-size:20px;font-weight:bold;color:#0a0a0a">
          Total: ${order['total']:.2f}
        </div>
        <p style="color:#555;margin-top:24px">We'll send another email when your order ships.</p>
      </div>
      <div style="background:#f5f5f5;padding:20px;text-align:center;color:#999;font-size:12px">
        ShopFlow · All rights reserved
      </div>
    </div>"""
    await send_email(to, f"Order Confirmed — #{order['_id'][:8].upper()}", html)

async def send_welcome_email(to: str, name: str):
    html = f"""
    <div style="font-family:Georgia,serif;max-width:600px;margin:0 auto">
      <div style="background:#0a0a0a;padding:32px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:28px;letter-spacing:4px">SHOPFLOW</h1>
      </div>
      <div style="padding:40px">
        <h2>Welcome, {name}!</h2>
        <p style="color:#555">Your account has been created. Start exploring our curated collection.</p>
        <a href="#" style="display:inline-block;background:#0a0a0a;color:#fff;padding:14px 32px;text-decoration:none;margin-top:16px">Shop Now</a>
      </div>
    </div>"""
    await send_email(to, "Welcome to ShopFlow", html)
