import logging

from django.conf import settings
from django.shortcuts import render_to_response
from django.http import JsonResponse

logger = logging.getLogger('site_info.views')


def disclaimer_views(request):
    template = 'site_info/disclaimer.html'
    user = request.user
    context = {'user': user}
    return render_to_response(template, context)


def about_us_views(request):
    template = 'site_info/aboutus.html'
    user = request.user
    context = {'user': user}
    return render_to_response(template, context)
