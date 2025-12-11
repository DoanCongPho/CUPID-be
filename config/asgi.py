"""
ASGI config for config project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

# If channels is available, we will wrap the ASGI app later. Otherwise use Django's ASGI app.
try:
    import django
    django.setup()
    from channels.routing import ProtocolTypeRouter, URLRouter
    from channels.auth import AuthMiddlewareStack
    # import websocket routes
    from users import routing as users_routing

    application = ProtocolTypeRouter({
        "http": get_asgi_application(),
        "websocket": AuthMiddlewareStack(
            URLRouter(users_routing.websocket_urlpatterns)
        ),
    })
except Exception:
    # fallback to simple ASGI app
    application = get_asgi_application()
