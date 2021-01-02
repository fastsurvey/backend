import pytest
import jwt
import os
import base64

from fastapi import HTTPException

import app.main as main
import app.cryptography as cryptography


def test_password_hashing():
    """Test password hashing and verifying with diverse passwords."""
    passwords = ['hello', 'world', 'A'*1000, '', 'Ӂ', 'ٸ', '៼']
    password_manager = main.account_manager.password_manager
    for password in passwords:
        password_hash = password_manager.hash_password(password)
        assert password_manager.verify_password(password, password_hash)


def test_valid_access_token_procedure(admin_name):
    """Test JWT access token generation and decoding procedure."""
    access_token = main.token_manager.generate(admin_name)
    assert main.token_manager.authorize(admin_name, access_token) is None


def test_invalid_access_token_procedure(admin_name):
    """Test that JWT decoding fails for some example invalid tokens."""
    with pytest.raises(HTTPException, match='unauthorized'):
        access_token = main.token_manager.generate('orange')
        main.token_manager.authorize(admin_name, access_token)
    with pytest.raises(HTTPException, match='invalid token format'):
        access_token = 'hello world'
        main.token_manager.authorize(admin_name, access_token)
    with pytest.raises(HTTPException, match='invalid token format'):
        access_token = None
        main.token_manager.authorize(admin_name, access_token)
    with pytest.raises(HTTPException, match='invalid token format'):
        access_token = {'access_token': 'abc', 'token_type': 'bearer'}
        main.token_manager.authorize(admin_name, access_token)
    with pytest.raises(HTTPException, match='token expired'):
        access_token = {
            'access_token': jwt.encode(
                {
                    'iss': 'FastSurvey',
                    'sub': admin_name,
                    'iat': 0,
                    'exp': 0,
                },
                key=cryptography.PRIVATE_RSA_KEY,
                algorithm='RS256',
            ),
            'token_type': 'bearer',
        }
        main.token_manager.authorize(admin_name, access_token)
    with pytest.raises(HTTPException, match='signature verification failed'):
        access_token = {
            'access_token': jwt.encode(
                {
                    'iss': 'FastSurvey',
                    'sub': admin_name,
                    'iat': 0,
                    'exp': 0,
                },
                key=base64.b64decode('LS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlKS0FJQkFBS0NBZ0VBMGdHZVVmOElqYlE2akN3R0lLRTBoM3N0Qlp6ZGU5N0Q3cXIwbU1IVU9BaG5KaXNFCnA0Z3QzRUxybWVoc1lPbm9yaTZsUjNYUGFscC93ZGxpKzRVdTliZCtRZTd2Ujk2YlZyTUtJTm1BazlGYk1xK0EKak84M2ZvWHczcGNzaWhxbStaem1MSWxlb0k2OXVKT0xNUkhBOW1MQUVack1XbXVyalQzUlV2MmhKNjRMb3BCRApSQVJXQkU3NGp2M3RpeGtVRmNmV3VVby9pS28wK2Z1U3pKTlFLUklwdktCVWNPRUpsdVoydk1pTnlMaDRwRXQ4CjNLNE1BSHNaK2xCYm9mekJsdUtoK29sMUdmNlc2Q2k5R1NpcWpSMFp4K2dVRmh0alVaWHliL3M0RWhieVRRTEIKcXlGTFZ3YjNRamJUWWhFK3JsYTR5SkFzZm5obS9yTjdEKzE3cTlFUGhmS0x1QnF1NHZnenJPUWVxYW1maklvbAprY2w2MkdNTW5Fckd4SlY2WmZMeWl3Um10YTl0MVN0TGI2am0vQmFxYWd1WWJKZDlDbjJLcDNuUzdlUkQ1VGJDCmQwY0hMYnIwQm1FNFhCQm9OZXpJbUViOG1kMC83NEFkWm52ZmdsNllLcWJqTFo3b2lVcUFXOUxHaTlTdzV0Uk0KWjVtWmVMbU1PbUg0MHIwV2dqWEZkdXpybC8yTSt6R0R2aFhxQWEwYm5XaVplLy93cENWRUdjaHdwdHhoRTV0Wgo1U0gxYUUzejNpb2FtMEw3ZUZzOHRHaFNoenRMWE4zcDhzcXBQczZWMlNrdTRlUUtPYlE3SmFrRGVOT1o4ZzFkCkhjM3g0M25BRGQzcE9BN0VVZ0NtY1ZMNGsvYTBJQ05PeDdVR0VkMUF2Y1NwUWtBcFducXFYMzlxMi8wQ0F3RUEKQVFLQ0FnRUF5dG5WVzg3RkxGdVMwaU1VS0NDTzVPOE9KZ1hIeXdiNnEyZG1yTWROZm5KZmNIYk5JQ1ppWmdnZQpHNlJ1UzQ2bHV0cER2Q3NJRnVzanpOTjIwUTFzdHR4dmtMQ0RZU0NkVzduRlpzV3hkUmNjeUhETjgxUitmakJTCjRpK1VUakpBWjR3dXFZWm5hUjk0RXZveDBVd2MzK0d6TlU0WlpwM3FMNXd1dmNOUUQwd0c0UmdJWVlMdXMycTAKblNxYWNXbmdCTW5ybHo4bzc1RzVhbDZmQmd5bHVZWloybUhrTHNTd3hwb0d4NFBSc0xpL2o3TjdBSTc5K05qdgoxdUlZSVBoTTVyb3pUQlhLanpsait3eWUyOVowSjZxY1pJVEFJanFDVFNSUjhlanYyRWxoOHhGZWtUYXYxM2hiCkRoSjNUSnJydU9yN3duL0Erc2pDYy9SYVFxQmFlM1BmL0hBNHpzWE1GUW96cEx4STFzelZZUHcvUVBIM1YrQXYKZGNwWXlVR2c2amkyZkNFUUpvWUlDMi9vVFo3ekF6WTdEMDFmWk9DZjJPTGNJekFESUNrRmpOaXRTQW96dGNOdgp3cHBvZm9NZHdxa1hDVHFHQTBIL0F4T2lvQlFBUysrcjYyZnFRVk1XcitMei80Vm0ydGpVVUY3c2I0MDNMV1BLCnB2WmZGSWFsOE0yNU4xbmlJaTQxaEJkOUhmQm5JRTFMYzFRNXVUTi83VWljdjJyb1haem9NanNmZHdhVlNGTGcKWk9oNEZSaGE3OHE0S1NOTVFRTGZuOW01ZzNKM1laK1FKa2N1aFJQM0MwMGx0VklhUzRiNGY2bkxtclozVGkzMQpqaHArM20vTXhWZWk2eVpiMHNjY0JEc3Y1ZkZWQmtYcU45YXkxWGxnWlpER0dJcDc2d0VDZ2dFQkFQV1VFWVlxCjlMQi9hSlQrSllTUHdiSVVVZnpZbkpyUGpUYWJzZnJsMGJUcnFRTExhRTY5d1crSG9FdXZ5RmdZQWViY0ZCZnkKUHNwRjZXQjJCcjBDdHpTMFZIZnZGaS9WV1Z1dU5oOWpvZlgyRWJFeGZUNFhCV0M2TThDZ2NlZG5RUjFQR0VOMgpqTDZqYS9WZVVaTHhmd2k1MnhybmdHTnFKSmtLenRuWWxuejdjNE55K0NTRkdjKzJLbnpRVjA3bWdjcTNWbGprCi91bVpKUU1TUjNuVU11KzZQRFpkc1FUUXRXTUlKbFY0T3cxVVJIZnRFTG1WYURlREwrbnQ5dFJOaEFJdGROazAKcm0yVXVySlUwYkZyVVdBeDZIN0RJUHBqVWxQbXdqY3BsWTAvaGdYcWNXc0o3VW1PWU1QOWZ6dlpFdnRXNStuagppVkRvVFpKVDJHNFRRQVVDZ2dFQkFOcnJHWU9Oa3g2QXhFazZVamd5SkJZSTVGd3dpQ2JXdkJWWU5PaDBweEVzCmNBZitTYnBOSkN1Ri9Id0RrK0FQVVB0T1ZGMWhVenVNWHN3dVFpZ0l1MGQyUGhmNmplNnN6SXZsV1NsTHRwZysKcmNQWmF0OXN3VUxsQlhlVVRHTnNRS3c5dkhxUXVtRkovTmc5UE9nWnc2YUpqL2NpWk53R2hiNGZtLzJhY3ViZQpqOHhDbjFEemtCRjN3WndUZnk1Q25YZm9HOWN5eEtrbVdkeXgxbXJLVzZPa2U3SXJkZjEwR0Q0eEJEMzc1elpFCmgyNEpNYURlMEhmVFN5b0o2QzNsSElGWUtQTVRheERDc01lcGo3QjhrVTBGVm1JakMwZC9hRlMySlI3QTlSc0QKNHVZb1ZhcGU4STVhZDY4VWxpVWxaUUZiZnhWUmYyMnBTdE1BMnNxN2haa0NnZ0VBSzYxU0VKTERRa0RtME5rQwp3emp1TWtYNjd3VjNsUEVsSkhrOGhtc3BpUXdBMjBaaUh0OFE4RTBtN1U4dVNyeTZXZHo2bGVlMzB6SHIrQVFGCjNzZ0UzWkxWRXgrcXlvY2ZoWGJPbVhhVzc2LzhKWSt2dnNOSmFaSzBjYVlYbkJoNU5FVkZBM3FxUFozRExiakEKdVduS05qc1lCUWozaExiMEcyUVl0aFlYYmRNckVFMzZaRVJuK3RGamJSK0E1NytIaGc1bGhSbjFYSWFvVm91Qgp1dUZLemVoSm5VRzhvaWFjbkNodTZQU2hUQldZdDl1cUJkZlUyVXF6MHQ5SDd5cDZPQWp0cDFQL1VlNEo1bjIvCmJkYXdlbk5sN21XMkQ5SnFhaEc0cVNiME9sTDUrME5mT0xKalNablJEQXFoL25yMUxVNmZvTEdmVW94K2YyLzYKSmxtMklRS0NBUUJhYng1R0V2a0FjODhpTlA1OENuS1B5N0tTUnRZbnZUTkxXZm5aUVQ4MnYvV3p4NThyWCt5ZQpNaVpnRUpaSXkrcjNOWjl5Ujk4N1RUeG4rb0FIeTd1WnhNWFg0QUE3NVpSR0FrTjM1TGdVWW1najdLL1Noam03CjZhSDlpUHlaWWNIQnBXc3o4bytiMnhXaE9vTHJtcUVSTGVpVC9kaE9jRDlWai9jL3AwcnFCbXkrdzVMT3ZSNzUKcUZBSnFxQXlPd0NUNVFXRE80eTBGNHl0dDZWTXpqVlcvMzY5MW1oU2dGLzNhUVpJbU1RbHpkOW9YRkh0RTc1bwprWmVPVVROaHFqREJXZXJvcDAvbVI1Y0JsQkV3cGZUY0xXVkcreFVRdnhnWlRuazlJQmJneHhVM1lOZ3FuamVmCmhzM0VQS3Zkd25uY09yRGYzSi9ZYkVQbHNJZXhrZytaQW9JQkFIYUJyaE9oazRZbmlyR0RwZ0Z3eE11ZlZxdEYKUE5hMWVaRnhHMmY2UTZYbXNaT1lVZ084VHRJZnVaZXhvUHRUQ2U4bUVxcmxPM0xOMDA4empDOHJIYnZwV3FhcQpmY1N5YnNyekRsMERKN1lGNU8vRmJjc2tyL2dUbGo4RkVjNTNxeEJKMUZhTmo1b0NIQTdiTS9iODErWkFSTlprCitiSmFGZFpIK3JWUjZraDVsTE95Qk5sS1k0UGVoZHpWZURDSTVIQzQ0MFlxYTR2UWk4WEdRVWplditkenhRd1oKcExZUitxVDYzWG5PbmdadkJQYldpQTk5TUwrUXdkb2NVOXNTKzFlWGhVZ0g1cW02S2VKaXU4RGUwR0ZmMHppZQpKNlR3NFRiT2ZYcCtTNHZ6VlhEaDR1dnBaU1EydmNiMTBDY1cyVHVhQk5lSER0QTBEd21UQUpYMWV3VT0KLS0tLS1FTkQgUlNBIFBSSVZBVEUgS0VZLS0tLS0K'),
                algorithm='RS256',
            ),
            'token_type': 'bearer',
        }
        main.token_manager.authorize(admin_name, access_token)

