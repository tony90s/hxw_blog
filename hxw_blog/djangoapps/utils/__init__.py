import string
import random

from django.core.exceptions import PermissionDenied


def generate_verification_code(length=6):
    return ''.join(random.sample(string.digits, length))


def check_object_permission(request, obj, field_name, raise_exception=False):
    if request.user.id == obj.__getattribute__(field_name):
        return True
    if raise_exception:
        raise PermissionDenied
    return False
