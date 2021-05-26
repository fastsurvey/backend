import httpx

import app.settings as settings


# email sending client
client = httpx.AsyncClient(
    base_url=f'https://api.eu.mailgun.net/v3/email.fastsurvey.io',
    auth=('api', settings.MAILGUN_API_KEY),
)
