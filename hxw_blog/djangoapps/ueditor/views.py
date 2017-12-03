from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def editor_test(request, template='ueTest.html'):
    return render_to_response(template)
