import os
import base64
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from sib_api_v3_sdk.models.send_smtp_email import SendSmtpEmail

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
MAIL_FROM = os.getenv("MAIL_FROM", "no-reply@convocation.com")


def send_ticket_email(to_email, name, ticket_url, pdf_bytes):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    # Encode PDF
    pdf_b64 = base64.b64encode(pdf_bytes).decode()

    email = SendSmtpEmail(
        sender={"email": MAIL_FROM, "name": "Convocation Team"},
        to=[{"email": to_email, "name": name}],
        subject="Convocation 2025 – Your Ticket",
        html_content=f"""
            <h2>Hello {name},</h2>
            <p>Your Convocation 2025 RSVP has been approved.</p>
            <p>Download your ticket here:</p>
            <p><a href="{ticket_url}">Click to Download</a></p>
            <p>A PDF of the ticket is also attached.</p>
            <br>
            <p>Regards,<br>Convocation Team</p>
        """,
        attachment=[
            {
                "name": "convocation_ticket.pdf",
                "content": pdf_b64,
                "type": "application/pdf"
            }
        ]
    )

    try:
        api_instance.send_transac_email(email)
        print("Email sent successfully")
        return True
    except ApiException as e:
        print("Email send error:", e)
        return False



def send_rejection_email(to_email, name):
    configuration = sib_api_v3_sdk.Configuration()
    configuration.api_key['api-key'] = BREVO_API_KEY

    api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

    email = SendSmtpEmail(
        sender={"email": MAIL_FROM, "name": "Convocation Team"},
        to=[{"email": to_email, "name": name}],
        subject="Convocation 2025 – RSVP Rejected",
        html_content=f"""
            <h2>Hello {name},</h2>
            <p>We could not verify your student details in our database.</p>
            <p>Your RSVP has been rejected.</p>
            <p>If this seems incorrect, please try registering again.</p>
            <br>
            <p>Regards,<br>Convocation Team</p>
        """
    )

    try:
        api_instance.send_transac_email(email)
        print("Rejection email sent")
        return True
    except ApiException as e:
        print("Email send error:", e)
        return False
