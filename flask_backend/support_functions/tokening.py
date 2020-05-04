
import secrets


def generate_random_key(length=32, existing_tokens=()):
    random_key = secrets.token_hex(length)

    # Brute force generate random keys as long as key is not unique
    while random_key in existing_tokens:
        random_key = secrets.token_hex(length)

    return random_key
