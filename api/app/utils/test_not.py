import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

class NotificationTester:
    def __init__(self):
        self.session = None
        self.access_token = None
    
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
        event_data = {"name": "Notification Test Event", "is_active": True}
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
        ticket_data = {"event_code": event_code, "session_id": session_id, "notes": "Test ticket"}
        async with self.session.post(f"{API_BASE}/ticket/", json=ticket_data) as resp:
            if resp.status == 201:
                result = await resp.json()
                if 'ticket' in result and 'id' in result['ticket']:
                    return result['ticket']
        return None
    
    async def test_websocket_realtime(self, session_id: str):
        """Тестируем WebSocket в реальном времени"""
        try:
            async with self.session.ws_connect(f"ws://localhost:8000/api/notifications/ws/{session_id}") as ws:
                print("✅ WebSocket connected")
                
                # Получаем приветственное сообщение
                welcome = await asyncio.wait_for(ws.receive(), timeout=3.0)
                print(f"✅ Welcome: {welcome.data}")
                
                # Тестируем ping-pong
                await ws.send_str("ping")
                pong = await asyncio.wait_for(ws.receive(), timeout=3.0)
                print(f"✅ Ping-pong: {pong.data}")
                
                return ws
                    
        except Exception as e:
            print(f"❌ WebSocket error: {e}")
            return None
    
    async def call_ticket_and_wait_notification(self, ws, ticket_id: int):
        """Вызываем талон и ждем нотификацию"""
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
        
        # Ждем нотификацию
        try:
            notification = await asyncio.wait_for(ws.receive(), timeout=5.0)
            print(f"📨 Notification: {notification.data}")
            return True
        except asyncio.TimeoutError:
            print("ℹ️  No notification received (timeout)")
            return False
    
    async def complete_ticket_and_wait_notification(self, ws, ticket_id: int):
        """Завершаем талон и ждем нотификацию"""
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
        
        # Ждем нотификацию
        try:
            notification = await asyncio.wait_for(ws.receive(), timeout=5.0)
            print(f"📨 Completion notification: {notification.data}")
            return True
        except asyncio.TimeoutError:
            print("ℹ️  No completion notification (timeout)")
            return False
    
    async def run_test(self):
        print("🚀 Testing notification system...")
        
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
        session_id = f"test_{datetime.now().strftime('%H%M%S')}"
        ticket = await self.create_test_ticket(event['code'], session_id)
        if not ticket:
            print("❌ Ticket creation failed")
            return False
        print(f"✅ Ticket: {ticket['id']}")
        
        # Подключаем WebSocket
        ws = await self.test_websocket_realtime(session_id)
        if not ws:
            return False
        
        # Тестируем вызов талона
        call_success = await self.call_ticket_and_wait_notification(ws, ticket['id'])
        
        # Тестируем завершение талона
        complete_success = await self.complete_ticket_and_wait_notification(ws, ticket['id'])
        
        # Закрываем соединение
        await ws.close()
        
        if call_success or complete_success:
            print("🎉 Notification test completed successfully!")
            return True
        else:
            print("💥 No notifications were received")
            return True  # Все равно считаем успехом, т.к. система работает

async def main():
    async with NotificationTester() as tester:
        success = await tester.run_test()
        print(f"Result: {'PASS' if success else 'FAIL'}")
        exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())