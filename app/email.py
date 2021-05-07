import httpx
import os
import os.path


# development / production / testing environment
ENVIRONMENT = os.getenv('ENVIRONMENT')
# frontend url
BACKEND_URL = os.getenv('BACKEND_URL')
# console url
CONSOLE_URL = os.getenv('CONSOLE_URL')
# mailgun api key
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')


def _read_templates():
    """Read all available email templates into a dictionary."""
    templates = {}
    base = os.path.dirname(__file__)
    for name in os.listdir(os.path.join(base, 'emails')):
        if name.endswith('.html'):
            with open(os.path.join(base, 'emails', name)) as file:
                templates[name[:-5]] = file.read()
    return templates


# main domain of the service
DOMAIN = 'fastsurvey.io'
# sender email address
SENDER = f'FastSurvey <noreply@{DOMAIN}>'
# email sending client
CLIENT = httpx.AsyncClient(
    base_url=f'https://api.eu.mailgun.net/v3/email.{DOMAIN}',
    auth=('api', MAILGUN_API_KEY),
)
# html email templates
TEMPLATES = _read_templates()


async def _send(email_address, subject, content):
    """Send the given email to the given email address."""
    data = {
        'from': SENDER,
        'to': f'test@{DOMAIN}' if ENVIRONMENT == 'testing' else email_address,
        'subject': subject,
        'html': content,
        'o:testmode': ENVIRONMENT == 'testing',
        'o:tag': [f'{ENVIRONMENT} transactional'],
    }
    response = await CLIENT.post('/messages', data=data)
    return response.status_code


async def send_account_verification(
        email_address,
        username,
        verification_token,
    ):
    """Send a confirmation email to verify an account email address."""
    subject = 'Welcome to FastSurvey!'
    link = f'{CONSOLE_URL}/verify?token={verification_token}'
    content = TEMPLATES['account_verification'].format(
        username=username,
        link=link,
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
    subject = 'Please verify your submission'
    link = (
        f'{BACKEND_URL}/users/{username}/surveys/{survey_name}'
        f'/verification/{verification_token}'
    )
    content = TEMPLATES['submission_verification'].format(
        title=title,
        link=link,
    )
    return await _send(email_address, subject, content)
