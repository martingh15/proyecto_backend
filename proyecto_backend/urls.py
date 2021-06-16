from base.token import CustomAuthToken
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('base.urls', namespace='base')),
    path('auth/', CustomAuthToken.as_view()),
    path('producto/', include('producto.urls', namespace='producto')),
    path('gastronomia/', include('gastronomia.urls', namespace='gastronomia')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)