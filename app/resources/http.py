import httpx

import app.settings as settings


# email sending client
client = httpx.AsyncClient(
    base_url=settings.MAILGUN_ENDPOINT,
    auth=('api', settings.MAILGUN_API_KEY),
)
