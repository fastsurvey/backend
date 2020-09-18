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

        # self.domain = 'email.fastsurvey.io'
        # self.endpoint = f'https://api.eu.mailgun.net/v3/{domain}'

        self.domain = 'sandboxef6ceb5ba442440191d0ec08141f43c0.mailgun.org'
        self.endpoint = f'https://api.mailgun.net/v3/{self.domain}'
        self.sender = f'FastSurvey <noreply@{self.domain}>'
        self.auth = ('api', MGKEY)
        self.client = httpx.AsyncClient(auth=self.auth, base_url=self.endpoint)

    async def verify_email(self, admin_name, survey_name, title, receiver, token):
        """Send confirmation email in order to verify an email address."""

        # verification url used to verify the users email
        vu = f'{BURL}/{admin_name}/{survey_name}/verification/{token}'
        html = (
            '<p>Hey there, we received your submission!</p>'
            + f'<p>Survey: <strong>{title}</strong></p>'
            + f'<p>Please verify your submission by <a href="{vu}" target="_blank">clicking here</a></p>'
            + '<p>Your FastSurvey team</p>'
        )
        data = {
            'from': self.sender,
            'to': receiver,
            'subject': 'Please verify your submission',
            'html': html,
            # 'o:testmode': ENV == 'development',
        }
        response = await httpx.post('/messages', data=data)
        return response.status_code
