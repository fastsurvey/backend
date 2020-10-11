import os
import httpx


# dev / production environment
ENV = os.getenv('ENV')
# backend url
BURL = os.getenv('BURL')
# mailgun api key
MGKEY = os.getenv('MGKEY')


class Letterbox:
    """Well ... you post it, and sometimes it arrives where it should."""

    def __init__(self):
        """Create a general email client to be used by all surveys."""

        # self.domain = 'sandboxef6ceb5ba442440191d0ec08141f43c0.mailgun.org'
        # self.endpoint = f'https://api.mailgun.net/v3/{self.domain}'

        self.domain = 'fastsurvey.io'
        self.subdomain = f'email.{self.domain}'
        self.endpoint = f'https://api.eu.mailgun.net/v3/{self.subdomain}'
        self.sender = f'FastSurvey <noreply@{self.domain}>'
        self.auth = ('api', MGKEY)
        self.client = httpx.AsyncClient(auth=self.auth, base_url=self.endpoint)

    async def send(self, receiver, html):
        """Send an email to the given receiver."""
        data = {
            'from': self.sender,
            'to': 'test@fastsurvey.io' if ENV == 'development' else receiver,
            'subject': 'Please verify your submission',
            'html': html,
            'o:testmode': ENV == 'development',
            'o:tag': [f'{ENV} transactional'],
        }
        response = await self.client.post('/messages', data=data)
        return response.status_code

    async def verify_email(
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
