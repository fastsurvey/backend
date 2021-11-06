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
_CLIENT = httpx.AsyncClient(
    base_url=settings.MAILGUN_ENDPOINT,
    auth=("api", settings.MAILGUN_API_KEY),
)


async def _send(email_address, subject, content):
    """Send the given email to the given email address."""
    data = {
        "from": settings.SENDER,
        "to": email_address,
        "subject": subject,
        "html": content,
        "o:testmode": "true" if settings.ENVIRONMENT == "test" else "false",
        "o:tag": [f"{settings.ENVIRONMENT} transactional"],
    }
    response = await _CLIENT.post("/messages", data=data)
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
