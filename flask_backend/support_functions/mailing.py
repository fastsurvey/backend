from flask_backend import SENDGRID_API_KEY, BACKEND_URL

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, Content, MimeType, ReplyTo


def send_email(entry):
    message = Mail()

    message.from_email = From('tutorium.mint@mse.tum.de', 'MINT Projektmodul')
    message.reply_to = ReplyTo('tutorium.mint@mse.tum.de', 'MINT Projektmodul')
    message.to = To(entry["email"], entry["name"], p=1)

    adress_data = f'{entry["name"]} <em>(Ich wohne {"<strong>nicht</strong>" if entry["remote"] else ""} in München)</em>'
    verification_url = f'{BACKEND_URL}backend/verify/{entry["verification_token"]}'
    change_url = f'{BACKEND_URL}form?name={entry["name"]}&email={entry["email"]}' \
                 f'&remote={"true" if entry["remote"] else "false"}'
    message.subject = Subject('Bestätige deine Email Adresse')
    message.content = Content(
        MimeType.html,
        f'<h2>Willkommen beim MINT Projektmodul</h2>' +
        f'<p>Wir haben folgende Daten von dir erhalten:</p>' +
        f'<p>{adress_data}</p><br/>' +
        f'<p>Diese Daten <strong>bestätigen</strong>: <a href=\'{verification_url}\'>Bestätigungs-Link</a></p>' +
        f'<p>Diese Daten <strong>ändern</strong>: <a href=\'{change_url}\'>Änderungs-Link</a></p><br/>' +
        f'<p>Falls du diese Mail nicht erwartet hast, dann kannst du sie einfach ignorieren.</p>' +
        f'<p>Beste Grüße,<br/>Dein MINT-Team</p>'
    )

    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        return True
    except Exception as e:
        print(e)
        return False
