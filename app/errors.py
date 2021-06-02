import fastapi


################################################################################
# 400 Bad Request
################################################################################


INVALID_ACCOUNT_DATA = 'invalid account data'
INVALID_CONFIGURATION = 'invalid configuration'
INVALID_SUBMISSION = 'invalid submission'

USERNAME_ALREADY_TAKEN = 'username already taken'
EMAIL_ADDRESS_ALREADY_TAKEN = 'email address already taken'
SURVEY_NAME_ALREADY_TAKEN = 'survey name already taken'

SURVEY_IS_CLOSED = 'survey is closed'
SURVEY_IS_NOT_OPEN = 'survey is not open'
SURVEY_IS_NOT_CLOSED = 'survey is not closed'

ACCOUNT_ALREADY_VERIFIED = 'account already verified'


class InvalidAccountDataError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(400, INVALID_ACCOUNT_DATA)


class InvalidConfigurationError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(400, INVALID_CONFIGURATION)


class InvalidSubmissionError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(400, INVALID_SUBMISSION)


class UsernameAlreadyTakenError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(400, USERNAME_ALREADY_TAKEN)


class EmailAddressAlreadyTakenError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(400, EMAIL_ADDRESS_ALREADY_TAKEN)


class SurveyNameAlreadyTakenError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(400, SURVEY_NAME_ALREADY_TAKEN)


class SurveyIsClosedError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(400, SURVEY_IS_CLOSED)


class SurveyIsNotOpenError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(400, SURVEY_IS_NOT_OPEN)


class SurveyIsNotClosedError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(400, SURVEY_IS_NOT_CLOSED)


class AccountAlreadyVerifiedError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(400, ACCOUNT_ALREADY_VERIFIED)


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
# 403 Forbidden
################################################################################


ACCOUNT_NOT_VERIFIED = 'account not verified'


class AccountNotVerifiedError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(403, ACCOUNT_NOT_VERIFIED)


################################################################################
# 404 Not Found
################################################################################


USER_NOT_FOUND = 'user not found'
SURVEY_NOT_FOUND = 'survey not found'


class UserNotFoundError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(404, USER_NOT_FOUND)


class SurveyNotFoundError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(404, SURVEY_NOT_FOUND)


################################################################################
# 500 Internal Server Error
################################################################################


INTERNAL_SERVER_ERROR = 'internal server error'


class InternalServerError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(500, INTERNAL_SERVER_ERROR)


################################################################################
# 501 Not Implemented
################################################################################


NOT_IMPLEMENTED = 'not implemented'


class NotImplementedError(fastapi.HTTPException):
    def __init__(self):
        super().__init__(501, NOT_IMPLEMENTED)
