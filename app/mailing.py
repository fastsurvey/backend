from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Subject, From, To, Mail, HtmlContent

import credentials


SGKEY = credentials.SENDGRID_API_KEY
BURL = credentials.BACKEND_URL


class Postman:
    """It's the postman who delivers the (electronic) love letters!"""

    def __init__(
            self, 
            configuration,
        ):
        """Create a mailing client for a survey using its configuration."""
        self.survey_name = configuration['name']
        self.survey_title = configuration['title']
        self.from_email = From(
            configuration.get('email', 'noreply@fastsurvey.io'),
            configuration.get('contact', 'FastSurvey'),
        )

    def _generate_verify_url(self, submission):
        """Generate the url that users need to visit to verify their email."""
        return f"{BURL}/{self.survey_name}/verify/{submission['token']}"

    def _generate_change_url(self, submission):
        raise NotImplementedError

    def _generate_summary(self, submission):
        raise NotImplementedError

    def _generate_content(self, submission):
        """Generate the content of the confirmation email."""
        return HtmlContent(
            '<h2>We received your submission!</h2>'
            + f'<p>Survey: {self.survey_title}</p>'
            + f'<p>Please verify your e-mail address by clicking <a href=\'{self._generate_verify_url(submission)}\'>here</a></p>'
        )

    def confirm(self, submission):
        """Send a confirmation email used to verify a user's email address."""
        message = Mail(
            from_email=self.from_email,
            to_emails=To(submission['email']),
            subject=Subject('Please confirm your e-mail address'),
            html_content=self._generate_content(submission),
        )
        try:
            sg_client = SendGridAPIClient(SGKEY)
            response = sg_client.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
            return True
        except Exception as e:
            print(e)
            return False
