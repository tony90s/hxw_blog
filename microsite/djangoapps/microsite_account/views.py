import logging

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

logger = logging.getLogger('microsite_account.views')


@login_required
def user_center(request):
    template_name = 'account/user_center.html'
    return render(request, template_name)


@login_required
def user_avatar_preview(request):
    template_name = 'account/avatar_preview.html'
    return render(request, template_name)


@login_required
def user_messages(request):
    template_name = 'account/messages.html'
    return render(request, template_name)
