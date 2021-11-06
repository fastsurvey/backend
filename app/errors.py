import fastapi


class _CustomError(fastapi.HTTPException):
    """Error class from which all more specific HTTP errors inherit from."""

    def __init__(self):
        super().__init__(self.STATUS_CODE, self.DETAIL)


########################################################################################
# 400 Bad Request
########################################################################################


class InvalidSyntaxError(_CustomError):
    STATUS_CODE = 400
    DETAIL = "invalid syntax"


class UsernameAlreadyTakenError(_CustomError):
    STATUS_CODE = 400
    DETAIL = "username already taken"


class EmailAddressAlreadyTakenError(_CustomError):
    STATUS_CODE = 400
    DETAIL = "email address already taken"


class SurveyNameAlreadyTakenError(_CustomError):
    STATUS_CODE = 400
    DETAIL = "survey name already taken"


class InvalidTimingError(_CustomError):
    STATUS_CODE = 400
    DETAIL = "invalid timing"


class SubmissionsExistError(_CustomError):
    STATUS_CODE = 400
    DETAIL = "submissions exist"


########################################################################################
# 401 Unauthorized
########################################################################################


class InvalidAccessTokenError(_CustomError):
    STATUS_CODE = 401
    DETAIL = "invalid access token"


class InvalidVerificationTokenError(_CustomError):
    STATUS_CODE = 401
    DETAIL = "invalid verification token"


class InvalidPasswordError(_CustomError):
    STATUS_CODE = 401
    DETAIL = "invalid password"


########################################################################################
# 403 Forbidden
########################################################################################


class AccessForbiddenError(_CustomError):
    STATUS_CODE = 403
    DETAIL = "access forbidden"


class AccountNotVerifiedError(_CustomError):
    STATUS_CODE = 403
    DETAIL = "account not verified"


########################################################################################
# 404 Not Found
########################################################################################


class UserNotFoundError(_CustomError):
    STATUS_CODE = 404
    DETAIL = "user not found"


class SurveyNotFoundError(_CustomError):
    STATUS_CODE = 404
    DETAIL = "survey not found"


########################################################################################
# 500 Internal Server Error
########################################################################################


class InternalServerError(_CustomError):
    STATUS_CODE = 500
    DETAIL = "internal server error"


########################################################################################
# 501 Not Implemented
########################################################################################


class NotImplementedError(_CustomError):
    STATUS_CODE = 501
    DETAIL = "not implemented"
