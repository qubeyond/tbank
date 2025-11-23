import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

class NotificationTester:
    def __init__(self):
        self.session = None
        self.access_token = None
        self.notifications_received = []
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def admin_login(self):
        login_data = {"username": "superadmin", "password": "superadmin123"}
        async with self.session.post(f"{API_BASE}/auth/login", json=login_data) as resp:
            if resp.status == 200:
                result = await resp.json()
                self.access_token = result["access_token"]
                return True
        return False
    
    async def create_test_event(self):
        event_data = {"name": "Final Notification Test", "is_active": True}
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with self.session.post(f"{API_BASE}/event/", json=event_data, headers=headers) as resp:
            if resp.status == 201:
                return await resp.json()
        return None
    
    async def create_test_queue(self, event_id: int):
        queue_data = {"event_id": event_id, "is_active": True}
        headers = {"Authorization": f"Bearer {self.access_token}"}
        async with self.session.post(f"{API_BASE}/queue/", json=queue_data, headers=headers) as resp:
            if resp.status == 201:
                return await resp.json()
        return None
    
    async def create_test_ticket(self, event_code: str, session_id: str):
        ticket_data = {"event_code": event_code, "session_id": session_id, "notes": "Final test"}
        async with self.session.post(f"{API_BASE}/ticket/", json=ticket_data) as resp:
            if resp.status == 201:
                result = await resp.json()
                if 'ticket' in result and 'id' in result['ticket']:
                    return result['ticket']
        return None
    
    async def websocket_listener(self, session_id: str):
        """Слушаем WebSocket сообщения в фоне"""
        try:
            async with self.session.ws_connect(f"ws://localhost:8000/api/notifications/ws/{session_id}") as ws:
                print("🎧 WebSocket listener started")
                
                # Получаем приветствие
                welcome = await ws.receive()
                print(f"✅ {welcome.data}")
                
                # Слушаем сообщения
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        if msg.data:  # Игнорируем None
                            notification = json.loads(msg.data)
                            self.notifications_received.append(notification)
                            print(f"📨 Notification: {notification}")
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"WebSocket error: {msg.data}")
                        break
                        
        except Exception as e:
            print(f"WebSocket listener error: {e}")
    
    async def call_ticket(self, ticket_id: int):
        """Вызываем талон"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        call_data = {"notes": "Test call"}
        
        print("📞 Calling ticket...")
        async with self.session.post(
            f"{API_BASE}/ticket/{ticket_id}/call", 
            json=call_data, 
            headers=headers
        ) as resp:
            if resp.status == 200:
                print("✅ Ticket called")
                return True
        return False
    
    async def complete_ticket(self, ticket_id: int):
        """Завершаем талон"""
        headers = {"Authorization": f"Bearer {self.access_token}"}
        complete_data = {"notes": "Test completion"}
        
        print("✅ Completing ticket...")
        async with self.session.post(
            f"{API_BASE}/ticket/{ticket_id}/complete", 
            json=complete_data, 
            headers=headers
        ) as resp:
            if resp.status == 200:
                print("✅ Ticket completed")
                return True
        return False
    
    async def run_test(self):
        print("🚀 Final notification test...")
        
        # Логин
        if not await self.admin_login():
            print("❌ Admin login failed")
            return False
        
        # Создаем тестовые данные
        event = await self.create_test_event()
        if not event:
            print("❌ Event creation failed")
            return False
        print(f"✅ Event: {event['code']}")
        
        queue = await self.create_test_queue(event['id'])
        if not queue:
            print("❌ Queue creation failed")
            return False
        print(f"✅ Queue: {queue['name']}")
        
        # Создаем талон
        session_id = f"final_test_{datetime.now().strftime('%H%M%S')}"
        ticket = await self.create_test_ticket(event['code'], session_id)
        if not ticket:
            print("❌ Ticket creation failed")
            return False
        print(f"✅ Ticket: {ticket['id']}")
        
        # Запускаем WebSocket слушатель в фоне
        listener_task = asyncio.create_task(self.websocket_listener(session_id))
        
        # Ждем подключения
        await asyncio.sleep(2)
        
        # Вызываем талон
        await self.call_ticket(ticket['id'])
        await asyncio.sleep(1)
        
        # Завершаем талон
        await self.complete_ticket(ticket['id'])
        await asyncio.sleep(1)
        
        # Останавливаем слушатель
        listener_task.cancel()
        try:
            await listener_task
        except asyncio.CancelledError:
            pass
        
        # Проверяем полученные нотификации
        print(f"\n📊 Received {len(self.notifications_received)} notifications:")
        for i, notification in enumerate(self.notifications_received, 1):
            print(f"  {i}. {notification.get('type', 'unknown')}: {notification.get('message', 'no message')}")
        
        if len(self.notifications_received) > 0:
            print("🎉 Notifications are working!")
            return True
        else:
            print("💥 No notifications received")
            return False

async def main():
    async with NotificationTester() as tester:
        success = await tester.run_test()
        print(f"\nResult: {'PASS' if success else 'FAIL'}")
        exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())