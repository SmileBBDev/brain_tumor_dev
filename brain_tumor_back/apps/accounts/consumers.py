from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

# 사용자 권한 변경 알림 Consumer
class UserPermissionConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        
        if user.is_anonymous :
            await self.close()
            return
        
        self.group_name = f"user_{user.id}"
        
        await self.accept()
    
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )
    
    async def permission_changed(self, event):
        await self.send_json({
            "type": "PERMISSION_CHANGED"
        })

# 사용자 접속 상태 관리 Consumer
class PresenceConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        
        if user.is_anonymous:
            await self.close()
            return

        self.user = user  # connect 시점에 user 상태 세팅

        await self.accept()

        # 최초 접속 시 last_seen 기록
        # await self.update_last_seen()

    async def receive_json(self, content):
        print("❤️ heartbeat", content)
        #  클라이언트에서 heartbeat 메시지를 보내면 last_seen 갱신
        if content.get("type") == "heartbeat":
            await self.update_last_seen()

    async def disconnect(self, close_code):
        user = getattr(self, "user", None)
        # 연결 종료 시에도 기록
        if user and user.is_authenticated:
            await self.update_last_seen()

    @database_sync_to_async
    def update_last_seen(self):
        User = get_user_model()
        user = getattr(self, "user", None)
        if user and user.is_authenticated:
            User.objects.filter(id=user.id).update(
                last_seen=timezone.now()
            )