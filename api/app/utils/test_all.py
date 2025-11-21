"""Скрипт для автоматического тестирования всех эндпоинтов API."""
import asyncio
import aiohttp
import json
from datetime import datetime

API_BASE = "http://localhost:8000"

class APITester:
    def __init__(self):
        self.session = None
        self.created_ids = {
            'events': [],
            'queues': [], 
            'tickets': []
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def make_request(self, method, endpoint, data=None):
        """Универсальный метод для запросов."""
        url = f"{API_BASE}{endpoint}"
        print(f"🔸 {method} {endpoint}")
        
        try:
            async with self.session.request(method, url, json=data) as response:
                result = await response.json() if response.status != 204 else {"status": "success"}
                status_emoji = "✅" if 200 <= response.status < 300 else "❌"
                print(f"{status_emoji} Status: {response.status}")
                
                if data:
                    print(f"   Request: {json.dumps(data, ensure_ascii=False)}")
                print(f"   Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
                print()
                
                return result, response.status
        except Exception as e:
            print(f"❌ Error: {e}")
            return None, 500
    
    async def test_health(self):
        """Тестирование health check эндпоинтов."""
        print("🎯 Testing Health Endpoints")
        print("=" * 50)
        
        await self.make_request("GET", "/health/status")
        await self.make_request("GET", "/health/db")
    
    async def test_events(self):
        """Тестирование мероприятий."""
        print("\n🎯 Testing Events")
        print("=" * 50)
        
        # Создание мероприятия
        event_data = {
            "name": f"Тестовое мероприятие {datetime.now().strftime('%H:%M:%S')}",
            "is_active": True
        }
        result, status = await self.make_request("POST", "/event/", event_data)
        if status == 201:
            self.created_ids['events'].append(result['id'])
        
        # Получение всех мероприятий
        await self.make_request("GET", "/event/")
        
        # Получение конкретного мероприятия
        if self.created_ids['events']:
            event_id = self.created_ids['events'][0]
            await self.make_request("GET", f"/event/{event_id}")
    
    async def test_queues(self):
        """Тестирование очередей."""
        print("\n🎯 Testing Queues") 
        print("=" * 50)
        
        if not self.created_ids['events']:
            print("❌ No events created, skipping queue tests")
            return
        
        event_id = self.created_ids['events'][0]
        
        # Создание нескольких очередей
        for i in range(3):
            queue_data = {
                "event_id": event_id,
                "is_active": True
            }
            result, status = await self.make_request("POST", "/queue/", queue_data)
            if status == 201:
                self.created_ids['queues'].append(result['id'])
        
        # Получение очередей мероприятия
        await self.make_request("GET", f"/queue/event/{event_id}")
        
        # Получение статуса очереди
        if self.created_ids['queues']:
            queue_id = self.created_ids['queues'][0]
            await self.make_request("GET", f"/queue/{queue_id}/status")
    
    async def test_tickets(self):
        """Тестирование талонов с автоматическим распределением."""
        print("\n🎯 Testing Tickets with Auto-Distribution")
        print("=" * 50)
        
        if not self.created_ids['events']:
            print("❌ No events created, skipping ticket tests")
            return
        
        event_id = self.created_ids['events'][0]
        
        # Создание нескольких талонов для тестирования распределения
        users = [
            {"user_identity": "user_001", "notes": "Первый клиент"},
            {"user_identity": "user_002", "notes": "Второй клиент"}, 
            {"user_identity": "user_003", "notes": "Третий клиент"},
            {"user_identity": "user_004", "notes": "VIP клиент"},
        ]
        
        for user in users:
            ticket_data = {
                "event_id": event_id,
                "user_identity": user["user_identity"],
                "notes": user["notes"]
            }
            result, status = await self.make_request("POST", "/ticket/", ticket_data)
            if status == 201:
                self.created_ids['tickets'].append(result['id'])
        
        # Показать распределение
        await self.show_distribution(event_id)
    
    async def show_distribution(self, event_id):
        """Показать распределение талонов по очередям."""
        print("\n📊 Distribution Analysis")
        print("=" * 50)
        
        # Получить все очереди мероприятия
        queues_result, _ = await self.make_request("GET", f"/queue/event/{event_id}")
        
        if not queues_result:
            return
        
        for queue in queues_result:
            queue_id = queue['id']
            queue_name = queue['name']
            
            # Получить талоны этой очереди
            tickets_result, _ = await self.make_request("GET", f"/ticket/queue/{queue_id}")
            
            print(f"\n📋 Queue {queue_name} (ID: {queue_id}):")
            print(f"   Current Position: {queue['current_position']}")
            print(f"   Active: {queue['is_active']}")
            
            if tickets_result:
                for ticket in tickets_result:
                    status_emoji = {
                        'waiting': '⏳',
                        'called': '📢', 
                        'completed': '✅',
                        'cancelled': '❌'
                    }.get(ticket['status'], '❓')
                    
                    print(f"   {status_emoji} Ticket {ticket['position']}: {ticket['user_identity']} ({ticket['status']})")
            else:
                print("   No tickets")
    
    async def test_queue_operations(self):
        """Тестирование операций с очередями."""
        print("\n🎯 Testing Queue Operations")
        print("=" * 50)
        
        if not self.created_ids['queues']:
            print("❌ No queues created, skipping operations tests")
            return
        
        queue_id = self.created_ids['queues'][0]
        
        # Вызвать следующего
        await self.make_request("POST", f"/queue/{queue_id}/next")
        
        # Получить обновленный статус
        await self.make_request("GET", f"/queue/{queue_id}/status")
    
    async def run_all_tests(self):
        """Запуск всех тестов."""
        print("🚀 Starting Comprehensive API Tests")
        print("=" * 60)
        
        await self.test_health()
        await self.test_events() 
        await self.test_queues()
        await self.test_tickets()
        await self.test_queue_operations()
        
        print("\n🎉 All tests completed!")
        print(f"📊 Created: {len(self.created_ids['events'])} events, "
              f"{len(self.created_ids['queues'])} queues, "
              f"{len(self.created_ids['tickets'])} tickets")

async def main():
    async with APITester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())