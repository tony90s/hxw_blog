from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers


class ObjectExistsValidator(object):
    message = _("The object doesn't exists.")

    def __init__(self, model_class, message=None):
        self.model_class = model_class
        self.message = message or self.message

    def __call__(self, value):
        model_class = self.model_class
        objects = model_class.objects.using('read').filter(id=value)
        if not objects.exists():
            raise serializers.ValidationError(self.message)
