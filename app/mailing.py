import os
import httpx


# development / production / testing environment
ENVIRONMENT = os.getenv('ENVIRONMENT')
# backend url
BACKEND_URL = os.getenv('BACKEND_URL')
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
            admin_name,
            survey_name,
            title,
            receiver,
            verification_token,
        ):
        """Send confirmation email to verify a submission email address."""
        subject = 'Please verify your submission'
        verification_url = (
            f'{BACKEND_URL}/{admin_name}/{survey_name}'
            f'/verification/{verification_token}'
        )
        html = (
            f'<p>Hi there, we received your submission!</p>'
            f'<p>Survey: <strong>{title}</strong></p>'
            f'<p>Please verify your submission by <a href="{verification_url}" target="_blank">clicking here</a>.</p>'
            f'<p>Best, the FastSurvey team</p>'
        )
        return await self.send(receiver, subject, html)

    async def send_account_verification_email(
            self,
            admin_name,
            receiver,
            verification_token,
        ):
        """Send confirmation email to verify an account email address."""

        # TODO

        '''
        subject = 'Welcome to FastSurvey!'
        # verification url
        vurl = f'{FRONTEND_URL}/verify?token={token}'
        html = (
            f'<p>Welcome to FastSurvey, {admin_name}!</p>'
            + f'<p>Please verify your email address by <a href="{vurl}" target="_blank">clicking here</a>.</p>'
            + '<p>The verification link is valid for 10 minutes.</p>'
            + '<p>Best, the FastSurvey team</p>'
        )
        return await self.send(receiver, subject, html)
        '''

        return 200

    async def send_password_reset_email(
            self,
            admin_name,
            receiver,
            token,
        ):
        """Send email in order to reset the password of an existing account."""

        # TODO

        '''
        subject = 'Reset Your FastSurvey Password'
        # password reset url
        rurl = f'{FRONTEND_URL}/set-password?token={token}'
        html = (
            f'<p>Hello {admin_name}!</p>'
            + f'<p>You can set your new password by <a href="{rurl}" target="_blank">clicking here</a>.</p>'
            + '<p>Best, the FastSurvey team</p>'
        )
        return await self.send(receiver, subject, html)
        '''

        return 200
