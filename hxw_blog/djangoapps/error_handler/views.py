from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def page_not_found(request):
    return render(request, 'error/error_404.html')


@csrf_exempt
def page_forbidden(request):
    return render(request, 'error/error_403.html')


@csrf_exempt
def page_error(request):
    return render(request, 'error/error_500.html')
