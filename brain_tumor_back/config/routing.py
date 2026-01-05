from django.urls import path

from apps.accounts.consumers import UserPermissionConsumer, PresenceConsumer
from apps.authorization.consumers import PermissionConsumer

websocket_urlpatterns = [
    path("ws/permissions/", PermissionConsumer.as_asgi()),
    path("ws/user-permissions/", UserPermissionConsumer.as_asgi()),
    path("ws/presence/", PresenceConsumer.as_asgi()),
]
