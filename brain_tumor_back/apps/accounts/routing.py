from django.urls import path
from .consumers import UserPermissionConsumer

# WebSocket Routing
websocket_urlpatterns = [
    path("ws/permissions/", UserPermissionConsumer.as_asgi()),
]