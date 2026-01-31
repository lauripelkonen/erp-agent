import { NextRequest, NextResponse } from "next/server";
import { google } from "googleapis";

interface DemoOffer {
  id: string;
  offer_number: string;
  customer: {
    name: string;
    email: string;
    street: string;
    postal_code: string;
    city: string;
    contact_person: string;
  };
  lines: Array<{
    product_code: string;
    product_name: string;
    quantity: number;
    unit_price: number;
    total_price: number;
    ai_confidence: number;
  }>;
  total_amount: number;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const offer: DemoOffer = body.offer;

    if (!offer) {
      return NextResponse.json(
        { error: "Missing offer data" },
        { status: 400 }
      );
    }

    // Get credentials from environment
    const credentialsJson = process.env.GOOGLE_SERVICE_ACCOUNT_CREDENTIALS;
    const recipientEmail = process.env.DEMO_EMAIL_RECIPIENT || "lauri@erp-agent.com";
    const senderEmail = process.env.EMAIL_FROM_ADDRESS || "automations@agent.lvi-wabek.fi";
    const appUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

    if (!credentialsJson) {
      console.error("GOOGLE_SERVICE_ACCOUNT_CREDENTIALS not configured");
      return NextResponse.json(
        { error: "Email service not configured" },
        { status: 500 }
      );
    }

    // Parse credentials
    let credentials;
    try {
      credentials = JSON.parse(credentialsJson);
    } catch (e) {
      console.error("Invalid GOOGLE_SERVICE_ACCOUNT_CREDENTIALS JSON");
      return NextResponse.json(
        { error: "Invalid email configuration" },
        { status: 500 }
      );
    }

    // Create auth client with domain-wide delegation
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: [
        "https://www.googleapis.com/auth/gmail.send",
      ],
    });

    // Create credentials with subject (impersonation)
    const authClient = await auth.getClient();

    // For service accounts with domain-wide delegation, we need to impersonate
    const jwt = new google.auth.JWT({
      email: credentials.client_email,
      key: credentials.private_key,
      scopes: ["https://www.googleapis.com/auth/gmail.send"],
      subject: senderEmail,
    });

    const gmail = google.gmail({ version: "v1", auth: jwt });

    // Build product lines HTML
    const productLinesHtml = offer.lines
      .map(
        (line) => `
          <tr>
            <td style="padding: 8px; border: 1px solid #e5e5e5;">${line.product_code}</td>
            <td style="padding: 8px; border: 1px solid #e5e5e5;">${line.product_name}</td>
            <td style="padding: 8px; border: 1px solid #e5e5e5; text-align: center;">${line.quantity}</td>
            <td style="padding: 8px; border: 1px solid #e5e5e5; text-align: right;">€${line.unit_price.toFixed(2)}</td>
            <td style="padding: 8px; border: 1px solid #e5e5e5; text-align: right; font-weight: bold;">€${line.total_price.toFixed(2)}</td>
            <td style="padding: 8px; border: 1px solid #e5e5e5; text-align: center;">
              <span style="background-color: ${line.ai_confidence >= 90 ? '#22c55e' : line.ai_confidence >= 80 ? '#eab308' : '#ef4444'}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">${line.ai_confidence}%</span>
            </td>
          </tr>
        `
      )
      .join("");

    // Build email HTML
    const htmlBody = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <style>
    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }
    .container { max-width: 800px; margin: 0 auto; padding: 20px; }
    .header { background-color: #0f172a; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }
    .content { background-color: #f8fafc; padding: 20px; border: 1px solid #e5e5e5; border-top: none; }
    .customer-info { background-color: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; background-color: white; }
    th { background-color: #0f172a; color: white; padding: 12px 8px; text-align: left; }
    .total-row { background-color: #f1f5f9; font-weight: bold; }
    .footer { margin-top: 20px; padding: 15px; background-color: #e5e5e5; text-align: center; border-radius: 0 0 8px 8px; font-size: 12px; }
    .cta-button { display: inline-block; padding: 12px 24px; background-color: #0f172a; color: white; text-decoration: none; border-radius: 6px; margin: 10px 5px; }
    .demo-badge { background-color: #eab308; color: #000; padding: 4px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <span class="demo-badge">DEMO</span>
      <h1>AI-Generated Offer</h1>
      <p>${offer.offer_number}</p>
    </div>

    <div class="content">
      <div class="customer-info">
        <h3>Customer</h3>
        <p><strong>${offer.customer.name}</strong></p>
        <p>${offer.customer.street}</p>
        <p>${offer.customer.postal_code} ${offer.customer.city}</p>
        <p>Contact: ${offer.customer.contact_person}</p>
      </div>

      <h3>Products (${offer.lines.length} items)</h3>
      <table>
        <thead>
          <tr>
            <th>Code</th>
            <th>Product</th>
            <th style="text-align: center;">Qty</th>
            <th style="text-align: right;">Unit Price</th>
            <th style="text-align: right;">Total</th>
            <th style="text-align: center;">AI Match</th>
          </tr>
        </thead>
        <tbody>
          ${productLinesHtml}
          <tr class="total-row">
            <td colspan="4" style="padding: 12px 8px; text-align: right;">Total:</td>
            <td style="padding: 12px 8px; text-align: right; font-size: 18px;">€${offer.total_amount.toFixed(2)}</td>
            <td></td>
          </tr>
        </tbody>
      </table>

      <div style="text-align: center; margin-top: 30px;">
        <a href="${appUrl}/offer-agent/demo/${offer.id}" class="cta-button">View Offer Details</a>
      </div>
    </div>

    <div class="footer">
      <p>This is a demo email from the AI Offer Generation system.</p>
      <p>Generated by ERP Agent | <a href="${appUrl}">Visit Dashboard</a></p>
    </div>
  </div>
</body>
</html>
    `.trim();

    // Create email message
    const subject = `Demo Offer: ${offer.offer_number} - ${offer.customer.name}`;

    const emailContent = [
      `To: ${recipientEmail}`,
      `From: ${senderEmail}`,
      `Subject: ${subject}`,
      `MIME-Version: 1.0`,
      `Content-Type: text/html; charset=UTF-8`,
      ``,
      htmlBody,
    ].join("\r\n");

    // Encode to base64url
    const encodedMessage = Buffer.from(emailContent)
      .toString("base64")
      .replace(/\+/g, "-")
      .replace(/\//g, "_")
      .replace(/=+$/, "");

    // Send email
    const result = await gmail.users.messages.send({
      userId: "me",
      requestBody: {
        raw: encodedMessage,
      },
    });

    console.log(`Demo email sent successfully. Message ID: ${result.data.id}`);

    return NextResponse.json({
      success: true,
      messageId: result.data.id,
    });
  } catch (error) {
    console.error("Failed to send demo email:", error);

    // Return more specific error info for debugging
    const errorMessage = error instanceof Error ? error.message : "Unknown error";

    return NextResponse.json(
      { error: "Failed to send email", details: errorMessage },
      { status: 500 }
    );
  }
}
