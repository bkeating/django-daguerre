from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings
from django.urls import re_path


urlpatterns = static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + [
    re_path(r'^', include('daguerre.urls')),
]
