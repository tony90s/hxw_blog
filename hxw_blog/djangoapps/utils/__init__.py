import string
import random


def generate_verification_code():
    return ''.join(random.sample(string.digits, 6))
