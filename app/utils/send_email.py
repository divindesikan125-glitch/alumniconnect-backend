from fastapi_mail import FastMail, MessageSchema, MessageType
from .core.email_config import conf

async def send_activation_email(email: str, token: str):

    activation_link = f"http://localhost:8000/auth/activate?token={token}"

    message = MessageSchema(
        subject="Activate Your AlumniConnect Account",
        recipients=[email],
        body=f"""
Hello,

Click the link below to activate your account:

{activation_link}

If the link does not work, use this activation token manually:

{token}

Thank you,
AlumniConnect
""",
        subtype=MessageType.plain
    )

    fm = FastMail(conf)
    await fm.send_message(message)
