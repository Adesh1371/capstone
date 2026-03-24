const {onDocumentCreated} = require("firebase-functions/v2/firestore");
const admin = require("firebase-admin");
const nodemailer = require("nodemailer");

admin.initializeApp();

exports.onOrderCreated = onDocumentCreated(
  {
    document: "orders/{orderId}",
    secrets: ["BREVO_USER", "BREVO_SMTP_KEY", "FROM_EMAIL"]
  },
  async (event) => {
    const snap = event.data;
    if (!snap) return;

    const order = snap.data();
    const orderId = event.params.orderId;
    const userEmail = order.user_email || "";
    const userName = order.user_name || "";
    const total = order.total || 0;
    const items = order.items || [];

    if (!userEmail) {
      console.log("No email found for order", orderId);
      return;
    }

    const itemsHtml = items.map(i => `
      <tr>
        <td style="padding:8px;border-bottom:1px solid #eee">${i.name}</td>
        <td style="padding:8px;border-bottom:1px solid #eee;text-align:center">${i.quantity}</td>
        <td style="padding:8px;border-bottom:1px solid #eee;text-align:right">$${parseFloat(i.price).toFixed(2)}</td>
      </tr>`).join("");

    const html = `
    <div style="font-family:Georgia,serif;max-width:600px;margin:0 auto;background:#fff">
      <div style="background:#0a0a0a;padding:32px;text-align:center">
        <h1 style="color:#fff;margin:0;font-size:28px;letter-spacing:4px">SHOPFLOW</h1>
      </div>
      <div style="padding:40px">
        <h2 style="color:#0a0a0a">Order Confirmed</h2>
        <p style="color:#555">Hi ${userName}, your order
        <strong>#${orderId.slice(0,8).toUpperCase()}</strong>
        has been placed successfully.</p>
        <table style="width:100%;border-collapse:collapse;margin:24px 0">
          <thead>
            <tr style="background:#f5f5f5">
              <th style="padding:10px;text-align:left">Item</th>
              <th style="padding:10px;text-align:center">Qty</th>
              <th style="padding:10px;text-align:right">Price</th>
            </tr>
          </thead>
          <tbody>${itemsHtml}</tbody>
        </table>
        <div style="text-align:right;font-size:20px;font-weight:bold;color:#0a0a0a">
          Total: $${parseFloat(total).toFixed(2)}
        </div>
        <p style="color:#555;margin-top:24px">
          We will send another email when your order ships.
        </p>
      </div>
      <div style="background:#f5f5f5;padding:20px;text-align:center;
                  color:#999;font-size:12px">
        ShopFlow - All rights reserved
      </div>
    </div>`;

    const transporter = nodemailer.createTransport({
      host: "smtp-relay.brevo.com",
      port: 587,
      auth: {
        user: process.env.BREVO_USER,
        pass: process.env.BREVO_SMTP_KEY
      }
    });

    try {
      await transporter.sendMail({
        from: `"ShopFlow" <${process.env.FROM_EMAIL}>`,
        to: userEmail,
        subject: `Order Confirmed - #${orderId.slice(0,8).toUpperCase()}`,
        html: html
      });
      console.log(`Email sent successfully to ${userEmail}`);
    } catch (error) {
      console.error("Email error:", error);
    }
  }
);