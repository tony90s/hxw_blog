import string
import random


def generate_verification_code(length=6):
    return ''.join(random.sample(string.digits, length))
