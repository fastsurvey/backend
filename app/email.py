import os
import httpx


# development / production / testing environment
ENVIRONMENT = os.getenv('ENVIRONMENT')
# frontend url
FRONTEND_URL = os.getenv('FRONTEND_URL')
# console url
CONSOLE_URL = os.getenv('CONSOLE_URL')
# mailgun api key
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')


# main domain of the service
DOMAIN = 'fastsurvey.io'
# sender email address
SENDER = f'FastSurvey <noreply@{DOMAIN}>'
# email sending client
CLIENT = httpx.AsyncClient(
    base_url=f'https://api.eu.mailgun.net/v3/email.{DOMAIN}',
    auth=('api', MAILGUN_API_KEY),
)


async def _send(receiver, subject, html):
    """Send the given email to the given receiver."""
    data = {
        'from': SENDER,
        'to': f'test@{DOMAIN}' if ENVIRONMENT == 'testing' else receiver,
        'subject': subject,
        'html': html,
        'o:testmode': ENVIRONMENT == 'testing',
        'o:tag': [f'{ENVIRONMENT} transactional'],
    }
    response = await CLIENT.post('/messages', data=data)
    return response.status_code


async def send_submission_verification(
        username,
        survey_name,
        title,
        receiver,
        verification_token,
    ):
    """Send a confirmation email to verify a submission email address."""
    subject = 'Please verify your submission'

    # TODO check with moritz what this link should be
    link = (
        f'{FRONTEND_URL}/{username}/{survey_name}'
        f'/verification/{verification_token}'
    )

    html = (
        f'<p>Hi there, we received your submission!</p>'
        f'<p>Survey: <strong>{title}</strong></p>'
        f'<p>Please verify your submission by <a href="{link}" target="_blank">clicking here</a>.</p>'
        f'<p>Best, the FastSurvey team</p>'
    )
    return await _send(receiver, subject, html)


async def send_account_verification(username, receiver, verification_token):
    """Send a confirmation email to verify an account email address."""
    subject = 'Welcome to FastSurvey!'
    link = f'{CONSOLE_URL}/verify?token={verification_token}'
    html = (
        f'<p>Welcome to FastSurvey, {username}!</p>'
        f'<p>Please verify your email address by <a href="{link}" target="_blank">clicking here</a>.</p>'
        f'<p>The verification link is valid for 10 minutes.</p>'
        f'<p>Best, the FastSurvey team</p>'
    )
    return await _send(receiver, subject, html)
