import re

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class RegMatchValidator(object):
    message = _("The value doesn't match the regular expression.")

    def __init__(self, pattern, message=None):
        self.pattern = pattern
        self.message = message or self.message

    def __call__(self, value):
        reg_compile = re.compile(self.pattern)
        if not reg_compile.match(value):
            raise serializers.ValidationError(self.message)
