import os
import httpx


# mailgun api key
MGKEY = os.getenv('MGKEY')


domain = 'email.fastsurvey.io'
endpoint = f'https://api.eu.mailgun.net/v3/{domain}/messages'

domain = 'sandboxef6ceb5ba442440191d0ec08141f43c0.mailgun.org'
endpoint = f'https://api.mailgun.net/v3/{domain}/messages'

auth = ('api', MGKEY)
data = {
    'from': f'FELIX <mailgun@{domain}>',
    'to': 'felix@felixboehm.dev',
    'subject': 'HELLO',
    'text': 'Do you copy?',
}

response = httpx.post(endpoint, auth=auth, data=data)
print(response.text)
