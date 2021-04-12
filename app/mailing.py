import os
import httpx


# development / production / testing environment
ENVIRONMENT = os.getenv('ENVIRONMENT')
# backend url
FRONTEND_URL = os.getenv('BACKEND_URL')
# mailgun api key
MAILGUN_API_KEY = os.getenv('MAILGUN_API_KEY')


class Letterbox:
    """Well ... you post it, and sometimes it arrives where it should."""

    def __init__(self):
        """Create a general email client to be used by all surveys."""
        self.domain = 'fastsurvey.io'
        self.sender = f'FastSurvey <noreply@{self.domain}>'
        self.client = httpx.AsyncClient(
            auth=('api', MAILGUN_API_KEY),
            base_url=f'https://api.eu.mailgun.net/v3/email.{self.domain}',
        )

    async def send(self, receiver, subject, html):
        """Send an email to the given receiver."""
        data = {
            'from': self.sender,
            'to': (
                f'test@{self.domain}'
                if ENVIRONMENT != 'production'
                else receiver
            ),
            'subject': subject,
            'html': html,
            'o:testmode': ENVIRONMENT == 'testing',
            'o:tag': [f'{ENVIRONMENT} transactional'],
        }
        response = await self.client.post('/messages', data=data)
        return response.status_code

    async def send_submission_verification_email(
            self,
            username,
            survey_name,
            title,
            receiver,
            token,
        ):
        """Send confirmation email to verify a submission email address."""
        subject = 'Please verify your submission'

        # TODO check with moritz what this link should be
        link = (
            f'{FRONTEND_URL}/{username}/{survey_name}'
            f'/verification/{token}'
        )

        html = (
            f'<p>Hi there, we received your submission!</p>'
            f'<p>Survey: <strong>{title}</strong></p>'
            f'<p>Please verify your submission by <a href="{link}" target="_blank">clicking here</a>.</p>'
            f'<p>Best, the FastSurvey team</p>'
        )
        return await self.send(receiver, subject, html)

    async def send_email_address_verification_email(
            self,
            username,
            receiver,
            token,
        ):
        """Send confirmation email to verify an account email address."""
        subject = 'Welcome to FastSurvey!'

        # TODO check with moritz what this link should be
        link = f'{FRONTEND_URL}/verification/{token}'

        html = (
            f'<p>Welcome to FastSurvey, {username}!</p>'
            f'<p>Please verify your email address by <a href="{link}" target="_blank">clicking here</a>.</p>'
            f'<p>The verification link is valid for 10 minutes.</p>'
            f'<p>Best, the FastSurvey team</p>'
        )
        return await self.send(receiver, subject, html)
