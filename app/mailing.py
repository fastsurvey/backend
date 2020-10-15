import os
import httpx


# development / production / testing environment
ENV = os.getenv('ENV')
# backend url
BURL = os.getenv('BURL')
# mailgun api key
MGKEY = os.getenv('MGKEY')


class Letterbox:
    """Well ... you post it, and sometimes it arrives where it should."""

    def __init__(self):
        """Create a general email client to be used by all surveys."""
        self.domain = 'fastsurvey.io'
        self.sender = f'FastSurvey <noreply@{self.domain}>'
        self.client = httpx.AsyncClient(
            auth=('api', MGKEY),
            base_url=f'https://api.eu.mailgun.net/v3/email.{self.domain}',
        )

    async def send(self, receiver, html):
        """Send an email to the given receiver."""
        data = {
            'from': self.sender,
            'to': 'test@fastsurvey.io' if ENV != 'production' else receiver,
            'subject': 'Please verify your submission',
            'html': html,
            'o:testmode': ENV == 'testing',
            'o:tag': [f'{ENV} transactional'],
        }
        response = await self.client.post('/messages', data=data)
        return response.status_code

    async def send_verification_email(
            self,
            admin_name,
            survey_name,
            title,
            receiver,
            token,
        ):
        """Send confirmation email in order to verify an email address."""
        # verification url
        vu = f'{BURL}/{admin_name}/{survey_name}/verification/{token}'
        html = (
            '<p>Hi there, we received your submission!</p>'
            + f'<p>Survey: <strong>{title}</strong></p>'
            + f'<p>Please verify your submission by <a href="{vu}" target="_blank">clicking here</a></p>'
            + '<p>Your FastSurvey team</p>'
        )
        return await self.send(receiver, html)
