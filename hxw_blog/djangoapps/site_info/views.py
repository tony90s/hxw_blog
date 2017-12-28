import logging

from django.conf import settings
from django.shortcuts import render, render_to_response
from django.http import JsonResponse

logger = logging.getLogger('site_info.views')


def disclaimer_views(request):
    template = 'site_info/disclaimer.html'
    return render(request, template)


def about_us_views(request):
    template = 'site_info/aboutus.html'
    return render(request, template)


def downloads_views(request):
    template = 'site_info/downloads.html'
    return render(request, template)
