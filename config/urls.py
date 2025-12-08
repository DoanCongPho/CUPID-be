from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.shortcuts import render

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def api_index(request):
    return render(request, 'api_index.html')

urlpatterns = [
    path('admin/', admin.site.urls),

    # API documentation endpoints
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Render developer index at exact /api/
    path('api/', api_index),

    # include users app routes under /api/
    path('api/', include('users.urls')),

    path('', RedirectView.as_view(url='/api/', permanent=False)),
]
