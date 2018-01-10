import logging

from django.conf import settings
from django.shortcuts import render, render_to_response
from django.http import JsonResponse
from django.views.decorators.cache import cache_page

logger = logging.getLogger('site_info.views')


@cache_page(60 * 5)
def disclaimer_views(request):
    template = 'site_info/disclaimer.html'
    return render(request, template)


@cache_page(60 * 5)
def about_us_views(request):
    template = 'site_info/aboutus.html'
    return render(request, template)


@cache_page(60 * 15)
def downloads_views(request):
    template = 'site_info/downloads.html'
    return render(request, template)
