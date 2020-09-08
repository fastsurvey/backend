import os


# dev / production environment
ENV = os.getenv('ENV')
# backend url
BURL = os.getenv('BURL')


class Postman:
    """The conscientious fellow that delivers our electronic letters."""

    def __init__(
            self,
            configuration,
            postmark,
        ):
        """Create a mailing client for a survey using its configuration."""
        self.s_admin = configuration['admin']
        self.s_name = configuration['name']
        self.s_title = configuration['title']
        self.sender = 'noreply@fastsurvey.io'
        self.postmark = postmark

    def _generate_verify_url(self, submission):
        """Generate the url that users need to visit to verify their email."""
        token = submission['token']
        return f"{BURL}/{self.s_admin}/{self.s_name}/verify/{token}"

    def on_submit(self, submission):
        """Send a confirmation email used to verify a user's email address."""
        email = self.postmark.emails.Email(
            From=self.sender,
            To=(
                'test@blackhole.postmarkapp.com'
                if ENV == 'development'
                else submission['email']
            ),
            Subject='Please verify your submission',
            HtmlBody=(
                '<h2>We received your submission!</h2>'
                + f'<p>Survey: {self.s_title}</p>'
                + f'<p>Please verify your submission by <a href=\'{self._generate_verify_url(submission)}\'>clicking here</a></p>'
                + '<p>We hope to have you over answering cool surveys again, soon!</p>'
                + '<p>Your FastSurvey team</p>'
            ),
        )
        email.send()
