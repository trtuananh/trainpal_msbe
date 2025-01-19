"""
ASGI config for trainpal_dj project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trainpal_dj.settings')
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from base.routing import websocket_urlpatterns
from base.middleware import WebSocketAuthMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trainpal_dj.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        WebSocketAuthMiddleware(
            URLRouter(
                websocket_urlpatterns
            )
        )
    ),
})
