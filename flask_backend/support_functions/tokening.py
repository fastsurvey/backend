
import random


DIGITS = [chr(x) for x in range(48, 58)]      # Characters '0' through '9'
UPPERCASE = [chr(x) for x in range(65, 91)]   # Characters 'A' through 'Z'
LOWERCASE = [chr(x) for x in range(97, 123)]  # Characters 'a' through 'z'

def generate_random_key(length=32, numeric=False, existing_tokens=()):
    possible_characters = DIGITS

    if not numeric:
        # Characters 'A' through 'Z' and 'a' through 'z'
        possible_characters += UPPERCASE + LOWERCASE

    random_key = ''
    for i in range(length):
        random_key += random.choice(possible_characters)

    # Brute force generate random keys as long as key is not unique
    while random_key in existing_tokens:
        random_key = random_key[1:] + random.choice(possible_characters)

    return random_key
