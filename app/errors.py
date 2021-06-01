import fastapi


################################################################################
# 400 Bad Request
################################################################################


INVALID_ACCOUNT_DATA = 'invalid account data'
INVALID_CONFIGURATION = 'invalid configuration'
USERNAME_ALREADY_TAKEN = 'username already taken'
EMAIL_ADDRESS_ALREADY_TAKEN = 'email address already taken'
ACCOUNT_NOT_VERIFIED = 'account not verified'
ACCOUNT_ALREADY_VERIFIED = 'account already verified'
SURVEY_EXISTS = 'survey exists'
NOT_AN_EXISTING_SURVEY = 'not an existing survey'
SURVEY_IS_NOT_OPEN_YET = 'survey is not open yet'
SURVEY_IS_CLOSED = 'survey is closed'
SURVEY_IS_NOT_YET_CLOSED = 'survey is not yet closed'
INVALID_SUBMISSION = 'invalid submission'


################################################################################
# 401 Unauthorized
################################################################################


INVALID_ACCESS_TOKEN = 'invalid access token'
INVALID_VERIFICATION_TOKEN = 'invalid verification token'
INVALID_PASSWORD = 'invalid password'


class InvalidAccessTokenError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(401, INVALID_ACCESS_TOKEN)


class InvalidVerificationTokenError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(401, INVALID_VERIFICATION_TOKEN)


class InvalidPasswordError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(401, INVALID_PASSWORD)


################################################################################
# 404 Not Found
################################################################################


USER_NOT_FOUND = 'user not found'
SURVEY_NOT_FOUND = 'survey not found'


################################################################################
# 500 Internal Server Error
################################################################################


ACCOUNT_CREATION_ERROR = 'account creation error'
EMAIL_DELIVERY_FAILURE = 'email delivery failure'


################################################################################
# 501 Not Implemented
################################################################################


NOT_IMPLEMENTED = 'not implemented'
