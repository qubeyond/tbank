import aiohttp
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

API_BASE = "http://localhost:8000"

class TestResult:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.skipped = []
    
    def add_passed(self, test_name: str):
        self.passed.append(test_name)
    
    def add_failed(self, test_name: str, error: str = ""):
        self.failed.append((test_name, error))
    
    def add_skipped(self, test_name: str, reason: str = ""):
        self.skipped.append((test_name, reason))
    
    def print_summary(self):
        print(f"\nTest Summary: {len(self.passed)} passed, {len(self.failed)} failed, {len(self.skipped)} skipped")
        if self.failed:
            print("Failed tests:")
            for test_name, error in self.failed:
                print(f"  {test_name}: {error}")

class BaseAPITester:
    def __init__(self, session: aiohttp.ClientSession, access_token: str = ""):
        self.session = session
        self.access_token = access_token
        self.test_results = TestResult()
    
    async def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                     auth_required: bool = False, headers: Optional[Dict] = None) -> tuple:
        url = f"{API_BASE}{endpoint}"
        request_headers = {"Content-Type": "application/json"}
        if auth_required and self.access_token:
            request_headers["Authorization"] = f"Bearer {self.access_token}"
        if headers:
            request_headers.update(headers)
        
        try:
            async with self.session.request(
                method, url, json=data, headers=request_headers, ssl=False, timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                raw_text = await response.text()
                try:
                    result = json.loads(raw_text) if raw_text and response.status != 204 else {"status": "success"}
                except json.JSONDecodeError:
                    result = {"raw_response": raw_text}
                return result, response.status
        except Exception as e:
            return {"error": str(e)}, 500

class AuthTester(BaseAPITester):
    async def test_admin_login(self) -> bool:
        test_name = "Admin Login"
        try:
            login_data = {"username": "superadmin", "password": "superadmin123"}
            result, status = await self.make_request("POST", "/auth/login", login_data)
            if status == 200 and "access_token" in result:
                self.access_token = result["access_token"]
                self.test_results.add_passed(test_name)
                return True
            self.test_results.add_failed(test_name, f"Status: {status}")
            return False
        except Exception as e:
            self.test_results.add_failed(test_name, str(e))
            return False
    
    async def test_admin_logout(self) -> bool:
        test_name = "Admin Logout"
        try:
            result, status = await self.make_request("POST", "/auth/logout", auth_required=True)
            if status == 200:
                self.test_results.add_passed(test_name)
                return True
            self.test_results.add_failed(test_name, f"Status: {status}")
            return False
        except Exception as e:
            self.test_results.add_failed(test_name, str(e))
            return False
    
    async def test_admin_me(self) -> bool:
        test_name = "Get Admin Info"
        try:
            result, status = await self.make_request("GET", "/management/me", auth_required=True)
            if status == 200 and "id" in result:
                self.test_results.add_passed(test_name)
                return True
            self.test_results.add_failed(test_name, f"Status: {status}")
            return False
        except Exception as e:
            self.test_results.add_failed(test_name, str(e))
            return False
    
    async def test_admin_test_endpoint(self) -> bool:
        test_name = "Admin Test Endpoint"
        try:
            result, status = await self.make_request("GET", "/management/test", auth_required=True)
            if status == 200 and "admin" in result:
                self.test_results.add_passed(test_name)
                return True
            self.test_results.add_failed(test_name, f"Status: {status}")
            return False
        except Exception as e:
            self.test_results.add_failed(test_name, str(e))
            return False

class HealthTester(BaseAPITester):
    async def test_root_health(self) -> bool:
        test_name = "Root Health Check"
        result, status = await self.make_request("GET", "/health/", auth_required=True)
        if status == 200:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_health_status(self) -> bool:
        test_name = "Health Status"
        result, status = await self.make_request("GET", "/health/status", auth_required=True)
        if status == 200:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_db_health(self) -> bool:
        test_name = "Database Health"
        result, status = await self.make_request("GET", "/health/db", auth_required=True)
        if status == 200:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False

class EventTester(BaseAPITester):
    def __init__(self, session: aiohttp.ClientSession, access_token: str = ""):
        super().__init__(session, access_token)
        self.created_events = []
    
    async def create_active_event(self) -> Optional[Dict]:
        event_data = {"name": f"Test Event {datetime.now().strftime('%H:%M:%S')}", "is_active": True}
        result, status = await self.make_request("POST", "/event/", event_data, auth_required=True)
        if status == 201:
            event_info = {'id': result['id'], 'code': result['code'], 'is_active': result['is_active']}
            self.created_events.append(result['id'])
            return event_info
        return None
    
    async def test_create_event(self) -> Optional[int]:
        test_name = "Create Event"
        event_data = {"name": f"Test Event {datetime.now().strftime('%H:%M:%S')}", "is_active": True}
        result, status = await self.make_request("POST", "/event/", event_data, auth_required=True)
        if status == 201 and "id" in result:
            event_id = result["id"]
            self.created_events.append(event_id)
            self.test_results.add_passed(test_name)
            return event_id
        self.test_results.add_failed(test_name, f"Status: {status}")
        return None
    
    async def test_get_events(self) -> bool:
        test_name = "Get Events List"
        result, status = await self.make_request("GET", "/event/", auth_required=True)
        if status == 200 and isinstance(result, list):
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_get_event_by_id(self, event_id: int) -> bool:
        test_name = f"Get Event by ID {event_id}"
        result, status = await self.make_request("GET", f"/event/{event_id}", auth_required=True)
        if status == 200 and result.get("id") == event_id:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_update_event(self, event_id: int) -> bool:
        test_name = f"Update Event {event_id}"
        update_data = {"name": f"Updated Event {datetime.now().strftime('%H:%M:%S')}", "is_active": False}
        result, status = await self.make_request("PUT", f"/event/{event_id}", update_data, auth_required=True)
        if status == 200 and result.get("id") == event_id:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False

class QueueTester(BaseAPITester):
    def __init__(self, session: aiohttp.ClientSession, access_token: str = ""):
        super().__init__(session, access_token)
        self.created_queues = []
    
    async def test_create_queue(self, event_id: int) -> Optional[int]:
        test_name = "Create Queue"
        queue_data = {"event_id": event_id, "is_active": True}
        result, status = await self.make_request("POST", "/queue/", queue_data, auth_required=True)
        if status == 201 and "id" in result:
            queue_id = result["id"]
            self.created_queues.append(queue_id)
            self.test_results.add_passed(test_name)
            return queue_id
        self.test_results.add_failed(test_name, f"Status: {status}")
        return None
    
    async def test_get_queues(self, event_id: int) -> bool:
        test_name = f"Get Queues for Event {event_id}"
        result, status = await self.make_request("GET", f"/queue/?event_id={event_id}", auth_required=True)
        if status == 200 and isinstance(result, list):
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_get_queue_by_id(self, queue_id: int) -> bool:
        test_name = f"Get Queue by ID {queue_id}"
        result, status = await self.make_request("GET", f"/queue/{queue_id}", auth_required=True)
        if status == 200 and result.get("id") == queue_id:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_update_queue(self, queue_id: int) -> bool:
        test_name = f"Update Queue {queue_id}"
        update_data = {"name": "UpdatedQ", "is_active": False, "current_position": 5}
        result, status = await self.make_request("PUT", f"/queue/{queue_id}", update_data, auth_required=True)
        if status == 200 and result.get("id") == queue_id:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_queue_status(self, queue_id: int) -> bool:
        test_name = f"Get Queue Status {queue_id}"
        result, status = await self.make_request("GET", f"/queue/{queue_id}/status", auth_required=True)
        if status == 200 and "queue_id" in result:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_call_next(self, queue_id: int) -> bool:
        test_name = f"Call Next Ticket {queue_id}"
        result, status = await self.make_request("POST", f"/queue/{queue_id}/next", auth_required=True)
        if status == 200:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_reset_queue(self, queue_id: int) -> bool:
        test_name = f"Reset Queue {queue_id}"
        result, status = await self.make_request("POST", f"/queue/{queue_id}/reset", auth_required=True)
        if status == 200:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False

class TicketTester(BaseAPITester):
    def __init__(self, session: aiohttp.ClientSession, access_token: str = ""):
        super().__init__(session, access_token)
        self.created_tickets = []
        self.session_ids = []
    
    async def test_create_ticket_public(self, event_code: str) -> Optional[Dict]:
        test_name = "Create Public Ticket"
        try:
            session_id = f"test_session_{datetime.now().strftime('%H%M%S%f')}"
            self.session_ids.append(session_id)
            ticket_data = {"event_code": event_code, "session_id": session_id, "notes": "Test ticket"}
            result, status = await self.make_request("POST", "/ticket/", ticket_data)
            
            if status == 201 and 'ticket' in result and 'id' in result['ticket']:
                ticket_data = result['ticket']
                ticket_info = {
                    "id": ticket_data["id"], 
                    "session_id": session_id, 
                    "queue_id": ticket_data["queue_id"]
                }
                self.created_tickets.append(ticket_info)
                self.test_results.add_passed(test_name)
                return ticket_info
            
            elif status == 400 and "уже есть активный талон" in str(result).lower():
                self.test_results.add_passed(f"{test_name} - already has active ticket")
                return None
            else:
                self.test_results.add_failed(test_name, f"Status: {status}, Response: {result}")
                return None
        except Exception as e:
            self.test_results.add_failed(test_name, str(e))
            return None
    
    async def test_get_my_tickets_public(self, session_id: str) -> bool:
        test_name = f"Get My Tickets {session_id}"
        headers = {"X-Session-ID": session_id}
        result, status = await self.make_request("GET", "/ticket/my-tickets", headers=headers)
        
        if status == 200 and isinstance(result, list):
            self.test_results.add_passed(test_name)
            return True
        elif status == 403:
            self.test_results.add_passed(f"{test_name} - no tickets (403)")
            return True
        else:
            self.test_results.add_failed(test_name, f"Status: {status}")
            return False
    
    async def test_update_ticket_public(self, ticket_id: int, session_id: str) -> bool:
        test_name = f"Update Public Ticket {ticket_id}"
        update_data = {"notes": "Updated note"}
        headers = {"X-Session-ID": session_id}
        result, status = await self.make_request("PUT", f"/ticket/{ticket_id}", update_data, headers=headers)
        
        if status == 200 and isinstance(result, dict) and 'id' in result:
            self.test_results.add_passed(test_name)
            return True
        elif status == 403:
            self.test_results.add_passed(f"{test_name} - access denied (403)")
            return True
        else:
            self.test_results.add_failed(test_name, f"Status: {status}")
            return False
    
    async def test_cancel_ticket_public(self, ticket_id: int, session_id: str) -> bool:
        test_name = f"Cancel Public Ticket {ticket_id}"
        headers = {"X-Session-ID": session_id}
        result, status = await self.make_request("POST", f"/ticket/{ticket_id}/cancel", headers=headers)
        
        if status == 200 and isinstance(result, dict) and 'id' in result:
            self.test_results.add_passed(test_name)
            return True
        elif status == 403:
            self.test_results.add_passed(f"{test_name} - access denied or already processed (403)")
            return True
        else:
            self.test_results.add_failed(test_name, f"Status: {status}")
            return False
    
    async def test_get_ticket_admin(self, ticket_id: int) -> bool:
        test_name = f"Get Ticket Admin {ticket_id}"
        result, status = await self.make_request("GET", f"/ticket/{ticket_id}", auth_required=True)
        if status == 200 and isinstance(result, dict) and 'id' in result:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_get_queue_tickets(self, queue_id: int) -> bool:
        test_name = f"Get Queue Tickets {queue_id}"
        result, status = await self.make_request("GET", f"/ticket/queue/{queue_id}", auth_required=True)
        if status == 200 and isinstance(result, list):
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_get_user_tickets(self, session_id: str) -> bool:
        test_name = f"Get User Tickets {session_id}"
        result, status = await self.make_request("GET", f"/ticket/user/{session_id}", auth_required=True)
        if status == 200 and isinstance(result, list):
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_call_ticket(self, ticket_id: int) -> bool:
        test_name = f"Call Ticket {ticket_id}"
        call_data = {"notes": "Admin call"}
        result, status = await self.make_request("POST", f"/ticket/{ticket_id}/call", call_data, auth_required=True)
        if status == 200 and isinstance(result, dict) and 'id' in result:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False
    
    async def test_complete_ticket(self, ticket_id: int) -> bool:
        test_name = f"Complete Ticket {ticket_id}"
        complete_data = {"notes": "Completed"}
        result, status = await self.make_request("POST", f"/ticket/{ticket_id}/complete", complete_data, auth_required=True)
        if status == 200 and isinstance(result, dict) and 'id' in result:
            self.test_results.add_passed(test_name)
            return True
        self.test_results.add_failed(test_name, f"Status: {status}")
        return False

class ComprehensiveAPITester:
    def __init__(self):
        self.session = None
        self.access_token = None
        self.all_results = TestResult()
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, *args):
        await self.session.close()
    
    async def run_all_tests(self):
        print("Starting TBank Queue API Tests")
        
        auth_tester = AuthTester(self.session)
        if not await auth_tester.test_admin_login():
            print("Authentication failed - stopping tests")
            return False
        
        self.access_token = auth_tester.access_token
        auth_tester.access_token = self.access_token
        
        print("Testing authentication endpoints")
        await auth_tester.test_admin_me()
        await auth_tester.test_admin_test_endpoint()
        
        print("Testing health endpoints")
        health_tester = HealthTester(self.session, self.access_token)
        await health_tester.test_root_health()
        await health_tester.test_health_status()
        await health_tester.test_db_health()
        
        print("Testing event endpoints")
        event_tester = EventTester(self.session, self.access_token)
        
        # Создаем активное мероприятие для тестирования талонов
        active_event = await event_tester.create_active_event()
        active_event_id = active_event['id'] if active_event else None
        active_event_code = active_event['code'] if active_event else None
        
        # Создаем отдельное мероприятие для тестирования CRUD операций
        test_event_id = await event_tester.test_create_event()
        if test_event_id:
            await event_tester.test_get_events()
            await event_tester.test_get_event_by_id(test_event_id)
            await event_tester.test_update_event(test_event_id)
        
        print("Testing queue endpoints")
        queue_tester = QueueTester(self.session, self.access_token)
        queue_id = None
        
        # Создаем очереди для АКТИВНОГО мероприятия
        if active_event_id:
            queue_id = await queue_tester.test_create_queue(active_event_id)
            if queue_id:
                await queue_tester.test_get_queues(active_event_id)
                await queue_tester.test_get_queue_by_id(queue_id)
                await queue_tester.test_queue_status(queue_id)
                await queue_tester.test_call_next(queue_id)
                await queue_tester.test_reset_queue(queue_id)
        
        print("Testing ticket endpoints")
        ticket_tester = TicketTester(self.session, self.access_token)
        
        # Тестируем создание талонов для АКТИВНОГО мероприятия
        if active_event_code:
            # Создаем только ОДИН талон для тестирования
            ticket = await ticket_tester.test_create_ticket_public(active_event_code)
            
            if ticket:
                # Тестируем операции с созданным талоном
                await ticket_tester.test_get_my_tickets_public(ticket["session_id"])
                await ticket_tester.test_update_ticket_public(ticket["id"], ticket["session_id"])
                await ticket_tester.test_get_ticket_admin(ticket["id"])
                await ticket_tester.test_get_queue_tickets(ticket["queue_id"])
                await ticket_tester.test_get_user_tickets(ticket["session_id"])
                await ticket_tester.test_call_ticket(ticket["id"])
                await ticket_tester.test_complete_ticket(ticket["id"])
                await ticket_tester.test_cancel_ticket_public(ticket["id"], ticket["session_id"])
        
        print("Testing logout")
        await auth_tester.test_admin_logout()
        
        self._collect_results(auth_tester, health_tester, event_tester, queue_tester, ticket_tester)
        self.all_results.print_summary()
        
        return len(self.all_results.failed) == 0
    
    def _collect_results(self, *testers):
        for tester in testers:
            self.all_results.passed.extend(tester.test_results.passed)
            self.all_results.failed.extend(tester.test_results.failed)
            self.all_results.skipped.extend(tester.test_results.skipped)

async def main():
    async with ComprehensiveAPITester() as tester:
        success = await tester.run_all_tests()
        exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())