import aiohttp
import asyncio
import json
from datetime import datetime


API_BASE = "http://localhost:8000"


class BaseAPITester:
    """Базовый класс для тестирования API."""
    
    def __init__(self, session, access_token):
        self.session = session
        self.access_token = access_token
    
    async def make_request(self, method, endpoint, data=None, auth_required=False):
        """Универсальный метод для выполнения запросов."""
        url = f"{API_BASE}{endpoint}"
        print(f"Request: {method} {endpoint}")
        
        headers = {"Content-Type": "application/json"}
        if auth_required and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            async with self.session.request(
                method, url, 
                json=data, 
                headers=headers,
                ssl=False
            ) as response:
                result = await response.json() if response.status != 204 else {"status": "success"}
                
                print(f"Status: {response.status}")
                if data:
                    print(f"Request data: {json.dumps(data, ensure_ascii=False)}")
                print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
                print()
                
                return result, response.status
        except Exception as e:
            print(f"Error: {e}")
            return None, 500


class AuthTester(BaseAPITester):
    """Тестирование аутентификации."""
    
    async def admin_login(self):
        """Аутентификация администратора."""
        print("Admin Authentication")
        print("=" * 40)
        
        auth = aiohttp.BasicAuth("superadmin", "superadmin123")
        
        async with self.session.post(
            f"{API_BASE}/auth/login", 
            auth=auth,
            ssl=False
        ) as response:
            if response.status == 200:
                result = await response.json()
                self.access_token = result["access_token"]
                print("✅ Authentication successful")
                print(f"Token: {self.access_token[:20]}...")
                return True
            else:
                print(f"❌ Authentication failed: {response.status}")
                return False


class HealthTester(BaseAPITester):
    """Тестирование health check эндпоинтов."""
    
    async def test_health_endpoints(self):
        """Тестирование health check эндпоинтов."""
        print("Testing Health Endpoints")
        print("=" * 40)
        
        await self.make_request("GET", "/health/", auth_required=True)
        await self.make_request("GET", "/health/status", auth_required=True)
        await self.make_request("GET", "/health/db", auth_required=True)


class AdminTester(BaseAPITester):
    """Тестирование административных эндпоинтов."""
    
    async def test_admin_endpoints(self):
        """Тестирование административных эндпоинтов."""
        print("Testing Admin Endpoints")
        print("=" * 40)
        
        await self.make_request("GET", "/management/me", auth_required=True)
        await self.make_request("GET", "/management/test", auth_required=True)


class EventTester(BaseAPITester):
    """Тестирование мероприятий."""
    
    def __init__(self, session, access_token):
        super().__init__(session, access_token)
        self.created_events = []
    
    async def test_events_crud(self):
        """Тестирование CRUD операций с мероприятиями."""
        print("Testing Events CRUD")
        print("=" * 40)
        
        # Создание мероприятия для тестирования CRUD
        event_data = {
            "name": f"Тестовое мероприятие CRUD {datetime.now().strftime('%H:%M:%S')}",
            "is_active": True
        }
        
        result, status = await self.make_request("POST", "/event/", event_data, auth_required=True)
        if status == 201:
            event_id = result['id']
            self.created_events.append(event_id)
            print(f"✅ Event created: ID={event_id}")
        
        # Чтение мероприятий
        if self.created_events:
            event_id = self.created_events[0]
            
            await self.make_request("GET", f"/event/{event_id}", auth_required=True)
            await self.make_request("GET", "/event/", auth_required=True)
            
            # Обновление мероприятия (деактивируем его)
            update_data = {
                "name": f"Обновленное мероприятие {datetime.now().strftime('%H:%M:%S')}",
                "is_active": False
            }
            await self.make_request("PUT", f"/event/{event_id}", update_data, auth_required=True)
    
    async def create_active_event(self):
        """Создать активное мероприятие для тестирования."""
        print("Creating Active Event")
        print("=" * 40)
        
        event_data = {
            "name": f"Активное мероприятие {datetime.now().strftime('%H:%M:%S')}",
            "is_active": True
        }
        
        result, status = await self.make_request("POST", "/event/", event_data, auth_required=True)
        if status == 201:
            event_info = {
                'id': result['id'],
                'code': result['code']
            }
            self.created_events.append(result['id'])
            print(f"✅ Active event created: ID={event_info['id']}, CODE={event_info['code']}")
            return event_info
        return None


class QueueTester(BaseAPITester):
    """Тестирование очередей."""
    
    def __init__(self, session, access_token):
        super().__init__(session, access_token)
        self.created_queues = []
    
    async def test_queues_crud(self, event_id):
        """Тестирование CRUD операций с очередями."""
        print("Testing Queues CRUD")
        print("=" * 40)
        
        if not event_id:
            print("❌ No event ID provided, skipping queue tests")
            return []
        
        # Создание первой очереди
        queue_data = {
            "event_id": event_id,
            "is_active": True
        }
        
        result, status = await self.make_request("POST", "/queue/", queue_data, auth_required=True)
        if status == 201:
            queue_id = result['id']
            self.created_queues.append(queue_id)
            print(f"✅ Queue created: ID={queue_id}")
        
        # Создание второй очереди
        result, status = await self.make_request("POST", "/queue/", queue_data, auth_required=True)
        if status == 201:
            queue_id = result['id']
            self.created_queues.append(queue_id)
            print(f"✅ Second queue created: ID={queue_id}")
        
        # Операции с очередями
        if self.created_queues:
            queue_id = self.created_queues[0]
            
            await self.make_request("GET", f"/queue/{queue_id}", auth_required=True)
            await self.make_request("GET", f"/queue/?event_id={event_id}", auth_required=True)
        
        return self.created_queues
    
    async def test_queue_operations(self, queue_id):
        """Тестирование операций с очередями."""
        print("Testing Queue Operations")
        print("=" * 40)
        
        if not queue_id:
            print("❌ No queue ID provided, skipping operations tests")
            return
        
        await self.make_request("GET", f"/queue/{queue_id}/status", auth_required=True)
        await self.make_request("POST", f"/queue/{queue_id}/next", auth_required=True)
        await self.make_request("POST", f"/queue/{queue_id}/reset", auth_required=True)
        await self.make_request("GET", f"/ticket/queue/{queue_id}", auth_required=True)
    
    async def test_queue_deletion_with_tickets(self, queue_id, target_queue_id=None):
        """Тестирование удаления очереди с талонами."""
        print("Testing Queue Deletion with Tickets")
        print("=" * 40)
        
        if not queue_id:
            print("❌ No queue ID provided, skipping deletion test")
            return
        
        delete_data = {
            "hard_delete": False,
            "move_tickets_to": target_queue_id
        }
        
        result, status = await self.make_request(
            "DELETE", f"/queue/{queue_id}", delete_data, auth_required=True
        )
        
        if status == 200:
            print(f"✅ Queue {queue_id} deleted successfully")
            if target_queue_id:
                print(f"✅ Tickets moved to queue {target_queue_id}")
        else:
            print(f"❌ Failed to delete queue {queue_id}")


class TicketTester(BaseAPITester):
    """Тестирование талонов."""
    
    def __init__(self, session, access_token):
        super().__init__(session, access_token)
        self.created_tickets = []
    
    async def test_ticket_creation(self, event_code, count=3):
        """Тестирование создания талонов (публичный эндпоинт)."""
        print("Testing Ticket Creation (Public)")
        print("=" * 40)
        
        if not event_code:
            print("❌ No event code available, skipping ticket tests")
            return []
        
        # Создание нескольких талонов для тестирования распределения по очередям
        for i in range(count):
            ticket_data = {
                "event_code": event_code,
                "user_identity": f"test_user_{datetime.now().strftime('%H%M%S')}_{i}",
                "notes": f"Тестовый талон #{i+1}"
            }
            
            result, status = await self.make_request("POST", "/ticket/", ticket_data, auth_required=False)
            if status == 201:
                ticket_id = result['id']
                self.created_tickets.append(ticket_id)
                print(f"✅ Ticket #{i+1} created: ID={ticket_id}, Queue={result['queue_id']}")
            else:
                print(f"❌ Failed to create ticket #{i+1}")
        
        return self.created_tickets
    
    async def test_ticket_operations(self, ticket_ids, queue_ids=None):
        """Тестирование операций с талонами."""
        print("Testing Ticket Operations")
        print("=" * 40)
        
        if not ticket_ids:
            print("❌ No tickets created, skipping operations tests")
            return
        
        # Тестируем операции с первым талоном
        ticket_id = ticket_ids[0]
        
        await self.make_request("GET", f"/ticket/{ticket_id}", auth_required=True)
        await self.make_request("GET", f"/ticket/{ticket_id}/position", auth_required=True)
        
        # Вызвать талон
        call_data = {"notes": "Тестовый вызов"}
        await self.make_request("POST", f"/ticket/{ticket_id}/call", call_data, auth_required=True)
        
        # Завершить талон
        complete_data = {"notes": "Обслуживание завершено"}
        await self.make_request("POST", f"/ticket/{ticket_id}/complete", complete_data, auth_required=True)
        
        # Тестируем операции со вторым талоном (отмена)
        if len(ticket_ids) > 1:
            ticket_id2 = ticket_ids[1]
            await self.make_request("POST", f"/ticket/{ticket_id2}/cancel", auth_required=True)
            
        # Тестируем перемещение третьего талона
        if len(ticket_ids) > 2 and queue_ids and len(queue_ids) > 1:
            ticket_id3 = ticket_ids[2]
            target_queue_id = queue_ids[1]
            move_data = {"target_queue_id": target_queue_id}
            await self.make_request("POST", f"/ticket/{ticket_id3}/move", move_data, auth_required=True)
    
    async def test_user_tickets(self, ticket_ids):
        """Тестирование получения талонов пользователя."""
        print("Testing User Tickets")
        print("=" * 40)
        
        if not ticket_ids:
            print("❌ No tickets created, skipping user tickets test")
            return
        
        # Берем user_identity из первого созданного талона
        ticket_id = ticket_ids[0]
        result, status = await self.make_request("GET", f"/ticket/{ticket_id}", auth_required=True)
        if status == 200:
            user_identity = result['user_identity']
            await self.make_request("GET", f"/ticket/user/{user_identity}", auth_required=True)


class QueueDeletionTester(BaseAPITester):
    """Специальный тестер для проверки удаления очередей с талонами."""
    
    def __init__(self, session, access_token):
        super().__init__(session, access_token)
        self.test_event_id = None
        self.test_queues = []
        self.test_tickets = []
    
    async def setup_test_environment(self):
        """Настройка тестового окружения."""
        print("Setting up Queue Deletion Test Environment")
        print("=" * 50)
        
        # Создаем мероприятие
        event_data = {
            "name": f"Тест удаления очередей {datetime.now().strftime('%H:%M:%S')}",
            "is_active": True
        }
        
        result, status = await self.make_request("POST", "/event/", event_data, auth_required=True)
        if status == 201:
            self.test_event_id = result['id']
            event_code = result['code']
            print(f"✅ Test event created: ID={self.test_event_id}, CODE={event_code}")
            
            # Создаем 3 очереди
            for i in range(3):
                queue_data = {"event_id": self.test_event_id, "is_active": True}
                result, status = await self.make_request("POST", "/queue/", queue_data, auth_required=True)
                if status == 201:
                    self.test_queues.append(result['id'])
                    print(f"✅ Queue {i+1} created: ID={result['id']}")
            
            # Создаем талоны в разных очередях
            for i in range(6):
                ticket_data = {
                    "event_code": event_code,
                    "user_identity": f"deletion_test_user_{i}",
                    "notes": f"Тестовый талон для удаления #{i+1}"
                }
                result, status = await self.make_request("POST", "/ticket/", ticket_data, auth_required=False)
                if status == 201:
                    self.test_tickets.append(result['id'])
                    print(f"✅ Ticket {i+1} created in queue {result['queue_id']}")
            
            return True
        return False
    
    async def test_queue_deletion_scenarios(self):
        """Тестирование различных сценариев удаления очередей."""
        print("Testing Queue Deletion Scenarios")
        print("=" * 50)
        
        if len(self.test_queues) < 3:
            print("❌ Not enough queues for deletion tests")
            return
        
        # Сценарий 1: Удаление очереди без перемещения талонов (soft delete)
        print("\n1. Testing queue deletion WITHOUT moving tickets")
        print("-" * 40)
        queue_to_delete = self.test_queues[0]
        await self.make_request("GET", f"/ticket/queue/{queue_to_delete}", auth_required=True)
        
        delete_data = {"hard_delete": False, "move_tickets_to": None}
        await self.make_request("DELETE", f"/queue/{queue_to_delete}", delete_data, auth_required=True)
        
        # Проверяем, что очередь удалена
        await self.make_request("GET", f"/queue/{queue_to_delete}", auth_required=True)
        
        # Сценарий 2: Удаление очереди с перемещением талонов
        print("\n2. Testing queue deletion WITH moving tickets")
        print("-" * 40)
        source_queue = self.test_queues[1]
        target_queue = self.test_queues[2]
        
        # Смотрим талоны до удаления
        await self.make_request("GET", f"/ticket/queue/{source_queue}", auth_required=True)
        await self.make_request("GET", f"/ticket/queue/{target_queue}", auth_required=True)
        
        delete_data = {"hard_delete": False, "move_tickets_to": target_queue}
        await self.make_request("DELETE", f"/queue/{source_queue}", delete_data, auth_required=True)
        
        # Проверяем, что талоны переместились
        await self.make_request("GET", f"/ticket/queue/{target_queue}", auth_required=True)
        
        # Сценарий 3: Создание новой очереди после удаления
        print("\n3. Testing new queue creation after deletion")
        print("-" * 40)
        new_queue_data = {"event_id": self.test_event_id, "is_active": True}
        result, status = await self.make_request("POST", "/queue/", new_queue_data, auth_required=True)
        if status == 201:
            new_queue_id = result['id']
            print(f"✅ New queue created after deletion: ID={new_queue_id}")
            
            # Создаем талон в новой очереди
            event_info = await self.make_request("GET", f"/event/{self.test_event_id}", auth_required=True)
            if event_info[1] == 200:
                ticket_data = {
                    "event_code": event_info[0]['code'],
                    "user_identity": "new_queue_test_user",
                    "notes": "Талон в новой очереди"
                }
                await self.make_request("POST", "/ticket/", ticket_data, auth_required=False)


class MainAPITester:
    """Главный класс для запуска всех тестов."""
    
    def __init__(self):
        self.session = None
        self.access_token = None
        self.results = {
            'events': [],
            'queues': [], 
            'tickets': []
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def run_basic_tests(self):
        """Запуск основных тестов."""
        print("Starting Basic API Tests")
        print("=" * 50)
        
        # Аутентификация
        auth_tester = AuthTester(self.session, self.access_token)
        if not await auth_tester.admin_login():
            print("❌ Authentication failed, stopping tests")
            return False
        
        self.access_token = auth_tester.access_token
        
        # Health checks
        health_tester = HealthTester(self.session, self.access_token)
        await health_tester.test_health_endpoints()
        
        # Admin endpoints
        admin_tester = AdminTester(self.session, self.access_token)
        await admin_tester.test_admin_endpoints()
        
        # Events CRUD
        event_tester = EventTester(self.session, self.access_token)
        await event_tester.test_events_crud()
        
        # Создаем активное мероприятие для дальнейших тестов
        active_event = await event_tester.create_active_event()
        if not active_event:
            print("❌ Failed to create active event, stopping tests")
            return False
        
        # Queues CRUD
        queue_tester = QueueTester(self.session, self.access_token)
        queue_ids = await queue_tester.test_queues_crud(active_event['id'])
        self.results['queues'] = queue_ids
        
        # Ticket operations
        ticket_tester = TicketTester(self.session, self.access_token)
        ticket_ids = await ticket_tester.test_ticket_creation(active_event['code'], count=3)
        self.results['tickets'] = ticket_ids
        
        if ticket_ids:
            await ticket_tester.test_ticket_operations(ticket_ids, queue_ids)
            await ticket_tester.test_user_tickets(ticket_ids)
        
        # Queue operations
        if queue_ids:
            await queue_tester.test_queue_operations(queue_ids[0])
        
        return True
    
    async def run_queue_deletion_tests(self):
        """Запуск тестов удаления очередей."""
        print("\n" + "=" * 60)
        print("Starting Queue Deletion Tests")
        print("=" * 60)
        
        if not self.access_token:
            print("❌ Not authenticated, skipping deletion tests")
            return
        
        deletion_tester = QueueDeletionTester(self.session, self.access_token)
        if await deletion_tester.setup_test_environment():
            await deletion_tester.test_queue_deletion_scenarios()
    
    async def run_all_tests(self):
        """Запуск всех тестов."""
        if await self.run_basic_tests():
            await self.run_queue_deletion_tests()
        
        print("🎉 All tests completed!")
        print(f"📊 Created: {len(self.results['events'])} events, "
              f"{len(self.results['queues'])} queues, "
              f"{len(self.results['tickets'])} tickets")


async def main():
    """Основная функция запуска тестов."""
    async with MainAPITester() as tester:
        await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())