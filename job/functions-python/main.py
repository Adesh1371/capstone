import os
import json
import httpx
from firebase_functions.firestore_fn import (
    on_document_created,
    Event,
    DocumentSnapshot,
)
import firebase_admin
firebase_admin.initialize_app()

@on_document_created(document="orders/{orderId}", secrets=["BREVO_API_KEY", "FROM_EMAIL"])
def on_order_created(event: Event[DocumentSnapshot]) -> None:
    snap = event.data
    if not snap:
        return

    order = snap.to_dict()
    if not order:
        return

    order_id = event.params["orderId"]
    user_email = order.get("user_email", "")
    user_name = order.get("user_name", "")
    total = order.get("total", 0)
    items = order.get("items", [])

    if not user_email:
        print(f"No email found for order {order_id}")
        return

    items_html = "".join(
        f"<tr>"
        f"<td style='padding:8px;border-bottom:1px solid #eee'>{i.get('name','')}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:center'>{i.get('quantity',0)}</td>"
        f"<td style='padding:8px;border-bottom:1px solid #eee;text-align:right'>${float(i.get('price',0)):.2f}</td>"
        f"</tr>"
        for i in items
    )

    html = f"""
    <div style="font-family:Georgia,serif;max-width:600px;margin:0 auto;background:#fff">
      <div style="background:#0a0a0a;padding:32px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:28px;letter-spacing:4px">SHOPFLOW</h1>
      </div>
      <div style="padding:40px">
        <h2 style="color:#0a0a0a">Order Confirmed</h2>
        <p style="color:#555">Hi {user_name}, your order
        <strong>#{order_id[:8].upper()}</strong>
        has been placed successfully.</p>
        <table style="width:100%;border-collapse:collapse;margin:24px 0">
          <thead>
            <tr style="background:#f5f5f5">
              <th style="padding:10px;text-align:left">Item</th>
              <th style="padding:10px;text-align:center">Qty</th>
              <th style="padding:10px;text-align:right">Price</th>
            </tr>
          </thead>
          <tbody>{items_html}</tbody>
        </table>
        <div style="text-align:right;font-size:20px;font-weight:bold;color:#0a0a0a">
          Total: ${float(total):.2f}
        </div>
        <p style="color:#555;margin-top:24px">
          We will send another email when your order ships.
        </p>
      </div>
      <div style="background:#f5f5f5;padding:20px;text-align:center;
                  color:#999;font-size:12px">
        ShopFlow · All rights reserved
      </div>
    </div>"""

    brevo_api_key = os.environ.get("BREVO_API_KEY", "")
    from_email = os.environ.get("FROM_EMAIL", "adeshgore1371@gmail.com")

    if not brevo_api_key:
        print("BREVO_API_KEY not set")
        return

    with httpx.Client() as client:
        response = client.post(
            "https://api.brevo.com/v3/smtp/email",
            headers={
                "api-key": brevo_api_key,
                "Content-Type": "application/json"
            },
            json={
                "sender": {"name": "ShopFlow", "email": from_email},
                "to": [{"email": user_email}],
                "subject": f"Order Confirmed — #{order_id[:8].upper()}",
                "htmlContent": html
            }
        )
        print(f"Email sent to {user_email}: {response.status_code} {response.text}")