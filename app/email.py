import os
import os.path

import httpx

import app.settings as settings


def _read_templates():
    """Read all available email templates into a dictionary."""
    templates = {}
    base = os.path.dirname(__file__)
    for name in os.listdir(os.path.join(base, "emails")):
        if name.endswith(".html"):
            with open(os.path.join(base, "emails", name)) as file:
                templates[name[:-5]] = file.read()
    return templates


# HTML email templates
_TEMPLATES = _read_templates()
# email HTTP client
_CLIENT = httpx.AsyncClient(base_url="https://api.postmarkapp.com")


async def _send(email_address, subject, content):
    """Send the given email to the given email address."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-Postmark-Server-Token": settings.POSTMARK_SERVER_TOKEN,
    }
    json = {
        "From": settings.SENDER,
        "To": email_address,
        "Subject": subject,
        "HtmlBody": content,
        "MessageStream": "outbound",
    }
    response = await _CLIENT.post(url="/email", headers=headers, json=json)
    return response.status_code


async def send_account_verification(email_address, username, verification_token):
    """Send a confirmation email to verify an account email address."""
    subject = "Welcome to FastSurvey!"
    content = _TEMPLATES["account_verification"].format(
        username=username,
        link=f"{settings.CONSOLE_URL}/verify?token={verification_token}",
    )
    return await _send(email_address, subject, content)


async def send_submission_verification(
    email_address,
    username,
    survey_name,
    title,
    verification_token,
):
    """Send a confirmation email to verify a submission email address."""
    subject = "Please verify your submission"
    content = _TEMPLATES["submission_verification"].format(
        title=title,
        link=(
            f"{settings.FRONTEND_URL}/{username}/{survey_name}"
            f"/verify?token={verification_token}"
        ),
    )
    return await _send(email_address, subject, content)


async def send_magic_login(email_address, username, verification_token):
    """Send an email that allows a user to authenticate without their password."""
    subject = "Your FastSurvey Access"
    content = _TEMPLATES["magic_login"].format(
        username=username,
        link=f"{settings.CONSOLE_URL}/magic?token={verification_token}",
    )
    return await _send(email_address, subject, content)
