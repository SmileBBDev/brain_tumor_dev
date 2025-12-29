from channels.generic.websocket import AsyncJsonWebsocketConsumer

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