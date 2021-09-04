import pymongo.errors
import pymongo
import fastapi

import app.email as email
import app.authentication as auth
import app.utils as utils
import app.resources.database as database
import app.errors as errors
import app.survey as sve


async def fetch(username):
    """Return the account data corresponding to given user name."""
    account_data = await database.database['accounts'].find_one(
        filter={'username': username},
        projection={'_id': False, 'email_address': True, 'verified': True},
    )
    if account_data is None:
        raise errors.UserNotFoundError()
    return account_data


async def create(account_data):
    """Create new user account with some default account data."""
    timestamp = utils.now()
    password_hash = auth.hash_password(account_data['password'])
    verification_token = auth.generate_token()
    verification_token_hash = auth.hash_token(verification_token)
    while True:
        try:
            await database.database['accounts'].insert_one(
                document={
                    'username': account_data['username'],
                    'email_address': account_data['email_address'],
                    'password_hash': password_hash,
                    'creation_time': timestamp,
                    'modification_time': timestamp,
                    'verified': False,
                    'verification_token_hash': verification_token_hash,
                },
            )
            break
        except pymongo.errors.DuplicateKeyError as error:
            index = str(error).split()[7]
            if index == 'username_index':
                raise errors.UsernameAlreadyTakenError()
            if index == 'email_address_index':
                raise errors.EmailAddressAlreadyTakenError()
            if index == 'verification_token_hash_index':
                verification_token = auth.generate_token()
                verification_token_hash = auth.hash_token(verification_token)
            else:
                raise errors.InternalServerError()
    status = await email.send_account_verification(
        account_data['email_address'],
        account_data['username'],
        verification_token,
    )
    if status != 200:
        # we do not delete the unverified account here, as the user could
        # request a new verification email, and the account gets deleted
        # anyways after a while
        raise fastapi.HTTPException(
            422,
            [{
                'loc': ['body', 'email_address'],
                'msg': 'invalid email_address',
                'type': 'value_error',
            }]
        )


async def verify(verification_token):
    """Verify an existing account via its unique verification token."""
    res = await database.database['accounts'].update_one(
        filter={
            'verification_token_hash': auth.hash_token(verification_token),
            'verified': False,
        },
        update={'$set': {'verified': True}}
    )
    if res.matched_count == 0:
        raise errors.InvalidVerificationTokenError()


async def update(username, account_data):
    """Update existing user account data in the database."""
    x = await database.database['accounts'].find_one(
        filter={'username': username},
        projection={
            '_id': False,
            'email_address': True,
            'password_hash': True,
        },
    )
    if x is None:
        raise errors.UserNotFoundError()
    # determine update steps
    update = {'modification_time': utils.now()}
    if account_data['username'] != username:
        update['username'] = account_data['username']
    if account_data['email_address'] != x['email_address']:
        raise errors.NotImplementedError()
    if not auth.verify_password(account_data['password'], x['password_hash']):
        update['password_hash'] = auth.hash_password(account_data['password'])
    if len(update) == 1:
        return
    # perform update (with transaction if needed)
    if 'username' in update.keys():
        with database.client.start_session() as session:
            with session.start_transaction():
                res = await database.database['accounts'].update_one(
                    filter={'username': username},
                    update={'$set': update},
                )
                await database.database['configurations'].update_many(
                    filter={'username': username},
                    update={'$set': {'username': account_data['username']}},
                )
                await database.database['access_tokens'].update_many(
                    filter={'username': username},
                    update={'$set': {'username': account_data['username']}},
                )
    else:
        res = await database.database['accounts'].update_one(
            filter={'username': username},
            update={'$set': update},
        )
    if res.matched_count == 0:
        raise errors.UserNotFoundError()


async def delete(username):
    """Delete the user including all their surveys from the database."""
    with database.client.start_session() as session:
        with session.start_transaction():
            await database.database['accounts'].delete_one(
                filter={'username': username},
            )
            await database.database['access_tokens'].delete_many(
                filter={'username': username},
            )
            cursor = database.database['configurations'].find(
                filter={'username': username},
                projection={'_id': True},
            )
            survey_ids = [x['_id'] for x in await cursor.to_list(None)]
            await database.database['configurations'].delete_many(
                filter={'_id': {'$in': survey_ids}},
            )
            for survey_id in survey_ids:
                base = f'surveys.{str(survey_id)}'
                await database.database[f'{base}.submissions'].drop()
                await database.database[f'{base}.unverified-submissions'].drop()


async def login(identifier, password):
    """Authenticate user by their username or email and their password."""
    expression = (
        {'email_address': identifier}
        if '@' in identifier
        else {'username': identifier}
    )
    account_data = await database.database['accounts'].find_one(
        filter=expression,
        projection={
            '_id': False,
            'username': True,
            'password_hash': True,
            'verified': True,
        },
    )
    if account_data is None:
        raise errors.UserNotFoundError()
    if account_data['verified'] is False:
        raise errors.AccountNotVerifiedError()
    if not auth.verify_password(password, account_data['password_hash']):
        raise errors.InvalidPasswordError()
    access_token = auth.generate_token()
    while True:
        try:
            await database.database['access_tokens'].insert_one(
                document={
                    'username': account_data['username'],
                    'access_token_hash': auth.hash_token(access_token),
                    'issuance_time': utils.now(),
                },
            )
            break
        except pymongo.errors.DuplicateKeyError as error:
            index = str(error).split()[7]
            if index == 'access_token_hash_index':
                access_token = auth.generate_token()
            else:
                raise errors.InternalServerError()
    return {
        'username': account_data['username'],
        'access_token': access_token,
    }


async def logout(access_token):
    """Logout a user by rendering their access token useless."""
    res = await database.database['access_tokens'].delete_one(
        filter={'access_token_hash': auth.hash_token(access_token)},
    )
    if res.deleted_count == 0:
        raise errors.InvalidAccessTokenError()


async def fetch_configurations(username, skip, limit):
    """Return a list of the user's survey configurations."""
    cursor = database.database['configurations'].find(
        filter={'username': username},
        projection={'_id': False, 'username': False},
        sort=[('start', pymongo.DESCENDING)],
        skip=skip,
        limit=limit,
    )
    return await cursor.to_list(None)
