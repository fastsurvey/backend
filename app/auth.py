import functools
import hashlib
import secrets

import passlib.context as context
import pymongo.errors

import app.database as database
import app.email as email
import app.errors as errors
import app.utils as utils


_CONTEXT = context.CryptContext(schemes=["argon2"], deprecated="auto")


########################################################################################
# Password Utilities
########################################################################################


def hash_password(password):
    """Hash the given password and return the hash as string."""
    return _CONTEXT.hash(password)


def verify_password(password, password_hash):
    """Return true if the password results in the hash, else False."""
    return _CONTEXT.verify(password, password_hash)


########################################################################################
# Token Utilities
########################################################################################


def generate_token():
    """Create and return a random string useful for authentication."""
    return secrets.token_hex(32)


def hash_token(token):
    """Hash the given token and return the hash as string."""
    return hashlib.sha512(token.encode("utf-8")).hexdigest()


########################################################################################
# Access Token Flow
########################################################################################


def authorize(func):
    """Enforce proper authorization for the given fastapi route."""

    @functools.wraps(func)
    async def wrapper(**kwargs):
        access_token = kwargs["data"].access_token
        res = await database.database["access_tokens"].find_one_and_update(
            filter={"access_token_hash": hash_token(access_token), "active": True},
            update={"$set": {"issuance_time": utils.now()}},
            projection={"_id": False, "username": True},
        )
        if res is None:
            raise errors.InvalidAccessTokenError()
        if kwargs["data"].username != res["username"]:
            raise errors.AccessForbiddenError()
        return await func(**kwargs)

    return wrapper


async def create_access_token(identifier, password=None):
    """
    Authenticate user via username or email address and optionally a password.

    When no password is provided, we perform a magic login via email. We create and
    return an invalid access token that will be marked verified once the user sends
    us the verification token they received via email.

    """
    account_data = await database.database["accounts"].find_one(
        filter=(
            {"email_address": identifier}
            if "@" in identifier
            else {"username": identifier}
        ),
        projection={
            "_id": False,
            "username": True,
            "email_address": True,
            "password_hash": True,
            "verified": True,
        },
    )
    if account_data is None:
        raise errors.UserNotFoundError()
    if account_data["verified"] is False:
        raise errors.AccountNotVerifiedError()
    if password is None:
        return await _create_magic_access_token(
            username=account_data["username"],
            email_address=account_data["email_address"],
        )
    if not verify_password(password, account_data["password_hash"]):
        raise errors.InvalidPasswordError()
    return await _create_standard_access_token(account_data["username"])


async def _create_standard_access_token(username):
    """Write new standard access token to the database."""
    access_token = generate_token()
    while True:
        try:
            await database.database["access_tokens"].insert_one(
                {
                    "username": username,
                    "access_token_hash": hash_token(access_token),
                    "issuance_time": utils.now(),
                    "active": True,
                }
            )
            break
        except pymongo.errors.DuplicateKeyError as error:
            index = str(error).split()[7]
            if index == "access_token_hash_unique_index":
                access_token = generate_token()
            else:
                raise errors.InternalServerError()
    return {"username": username, "access_token": access_token}


async def _create_magic_access_token(username, email_address):
    """Write new magic access token to the database and send magic link via email."""
    access_token = generate_token()
    verification_token = generate_token()
    while True:
        try:
            await database.database["access_tokens"].insert_one(
                {
                    "username": username,
                    "access_token_hash": hash_token(access_token),
                    "issuance_time": utils.now(),
                    "active": False,
                    "verification_token_hash": hash_token(verification_token),
                }
            )
            break
        except pymongo.errors.DuplicateKeyError as error:
            index = str(error).split()[7]
            if index == "access_token_hash_unique_index":
                access_token = generate_token()
            elif index == "verification_token_hash_partial_unique_index":
                verification_token = generate_token()
            else:
                raise errors.InternalServerError()

    # Sending the magic login email can fail (e.g. because of an invalid email
    # address). Nevertheless, we don't react to this happening here as the user can
    # simply request a new verification email.

    await email.send_magic_login(email_address, username, verification_token)
    return {"username": username, "access_token": access_token}


async def verify_access_token(verification_token):
    """
    Activate an access token issued via magic login with its verification token.

    This method additionally creates and returns another access token in order to be
    able to request the magic link on one device, verify the access token on another
    and be authenticated in both. The verification link can be used only once and
    is valid for 24 hours.

    Another possibility to do this would be to directly send an access token (not a
    validation token) in the verification email. This would save us this verification
    procedure entirely, because the client can directly authenticate using the access
    token from the email. The main downside is that the authentication works only
    for the device that the email link was clicked on. Also, we would either need to
    send the username in the email as well, or find out the username from the access
    token somehow, so the frontend knows what can be authenticated with it.

    """
    res = await database.database["access_tokens"].find_one_and_update(
        filter={
            "verification_token_hash": hash_token(verification_token),
            "active": False,
        },
        update={"$set": {"active": True}},
        projection={"_id": False, "username": True},
    )
    if res is None:
        raise errors.InvalidVerificationTokenError()
    return await _create_standard_access_token(res["username"])


async def delete_access_token(access_token):
    """Logout a user by rendering their access token useless."""
    res = await database.database["access_tokens"].delete_one(
        filter={"access_token_hash": hash_token(access_token), "active": True},
    )
    if res.deleted_count == 0:
        raise errors.InvalidAccessTokenError()
