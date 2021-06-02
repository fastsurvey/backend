import fastapi


################################################################################
# 400 Bad Request
################################################################################


class InvalidAccountDataError(fastapi.HTTPException):
    STATUS_CODE = 400
    DETAIL = 'invalid account data'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


class InvalidConfigurationError(fastapi.HTTPException):
    STATUS_CODE = 400
    DETAIL = 'invalid configuration'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


class InvalidSubmissionError(fastapi.HTTPException):
    STATUS_CODE = 400
    DETAIL = 'invalid submission'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


class UsernameAlreadyTakenError(fastapi.HTTPException):
    STATUS_CODE = 400
    DETAIL = 'username already taken'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


class EmailAddressAlreadyTakenError(fastapi.HTTPException):
    STATUS_CODE = 400
    DETAIL = 'email address already taken'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


class SurveyNameAlreadyTakenError(fastapi.HTTPException):
    STATUS_CODE = 400
    DETAIL = 'survey name already taken'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


class SurveyDoesNotAcceptSubmissionsAtTheMomentError(fastapi.HTTPException):
    STATUS_CODE = 400
    DETAIL = 'survey does not accept submissions at the moment'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


################################################################################
# 401 Unauthorized
################################################################################


class InvalidAccessTokenError(fastapi.HTTPException):
    STATUS_CODE = 401
    DETAIL = 'invalid access token'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


class InvalidVerificationTokenError(fastapi.HTTPException):
    STATUS_CODE = 401
    DETAIL = 'invalid verification token'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


class InvalidPasswordError(fastapi.HTTPException):
    STATUS_CODE = 401
    DETAIL = 'invalid password'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


################################################################################
# 403 Forbidden
################################################################################


class AccessForbiddenError(fastapi.HTTPException):
    STATUS_CODE = 403
    DETAIL = 'access forbidden'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


class AccountNotVerifiedError(fastapi.HTTPException):
    STATUS_CODE = 403
    DETAIL = 'account not verified'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


################################################################################
# 404 Not Found
################################################################################


class UserNotFoundError(fastapi.HTTPException):
    STATUS_CODE = 404
    DETAIL = 'user not found'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


class SurveyNotFoundError(fastapi.HTTPException):
    STATUS_CODE = 404
    DETAIL = 'survey not found'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


################################################################################
# 500 Internal Server Error
################################################################################


class InternalServerError(fastapi.HTTPException):
    STATUS_CODE = 500
    DETAIL = 'internal server error'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


################################################################################
# 501 Not Implemented
################################################################################


class NotImplementedError(fastapi.HTTPException):
    STATUS_CODE = 501
    DETAIL = 'not implemented'
    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)
