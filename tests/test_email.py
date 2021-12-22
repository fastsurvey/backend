import pytest

import app.email as email


@pytest.mark.asyncio
async def test_sending_an_email():
    """Test that an email is successfully handled by the email provider."""
    status = await email._send(
        email_address="test+status@fastsurvey.de",
        subject="FastSurvey test email",
        text="This is an automatically generated test email.",
        html="<p>This is an automatically generated test email.</p>",
        tag="test",
    )
    assert status == 200
