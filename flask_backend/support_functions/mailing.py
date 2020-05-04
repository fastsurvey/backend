from flask_backend import SENDGRID_API_KEY

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, From, To, Subject, Content, MimeType, ReplyTo


def send_email(
        email=None, form_data=None, change_url=None, verify_url=None,
        reply_to="noreply-survey@mse.tum.de", reply_to_name="MSE Survey",
        survey_name=None
):

    if any([key is None for key in (email, form_data, change_url, verify_url)]):
        return False

    message = Mail()

    message.from_email = From('noreply-survey@mse.tum.de', 'MSE Survey')
    message.reply_to = ReplyTo(reply_to, reply_to_name)
    message.to = To(email)

    message.subject = Subject('Bestätige deine Email Adresse')
    message.content = Content(
        MimeType.html,
        f'<h2>Daten erfolgreich übermittelt!</h2>' +
        (f'<em>Umfrage: {survey_name}</em><br/>' if (survey_name is not None) else '') +
        f'<p>Wir haben folgende Daten von dir erhalten:</p>' + form_data + '<br/>' +
        f'<p>Dieser Eintrag wird erst gewertet, sobald du ihn bestätigt hast!</p>' +
        f'<p>Diese Daten <strong>bestätigen</strong>: <a href=\'{verify_url}\'>Bestätigungs-Link</a></p>' +
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
