"""hxw_blog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import os

from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from error_handler.views import page_forbidden, page_not_found, page_error
from index.views import index_views
from ueditor.controller import handler
from site_info.views import disclaimer_views, about_us_views, downloads_views

urlpatterns = [
    url(r'^$', index_views, name='index'),
    url(r'^aboutus$', about_us_views, name='aboutus'),
    url(r'^disclaimer$', disclaimer_views, name='disclaimer'),
    url(r'^downloads$', downloads_views, name='downloads'),
    url(r'^account/', include('account.urls', namespace='account')),
    url(r'^article/', include('article.urls', namespace='article')),
    url(r'^oauth2/', include('oauth.urls', namespace='oauth2')),
    # url(r'^admin/', admin.site.urls),
    url(r'^ueEditorControler', handler),
    url(r'^api/v1/', include('restful_api.urls', namespace='api')),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static('/upload/', document_root=os.path.join(settings.ENV_ROOT, "upload"))
    urlpatterns += static('/downloads/', document_root=os.path.join(settings.ENV_ROOT, "downloads"))

handler403 = page_forbidden
handler404 = page_not_found
handler500 = page_error
