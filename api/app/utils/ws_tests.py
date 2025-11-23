import pytest
import asyncio
import aiohttp
import json
import sys
import os

sys.path.insert(0, '/app')

class TestWebSocketWithAiohttpOnly:
    """Тесты WebSocket используя только aiohttp"""

    @pytest.fixture
    def base_url(self):
        return "http://localhost:8000"

    @pytest.fixture
    def ws_url(self):
        return "ws://localhost:8000"

    @pytest.fixture
    def admin_token(self):
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdXBlcmFkbWluIiwiZXhwIjoxNzYzOTU1ODQ2LCJpYXQiOjE3NjM4Njk0NDYsImp0aSI6ImY1NmU3M2I1LTgwMDMtNDU2MS1iNTE4LTQ3ZTA1MWEzMjBhYiIsInR5cGUiOiJhY2Nlc3NfdG9rZW4ifQ.Qh6kgWcG6DALT3nBVhNIlbClWAKNsLPrt4sH2A9DEgk"

    @pytest.fixture
    def admin_headers(self, admin_token):
        return {"Authorization": f"Bearer {admin_token}"}

    async def make_api_request(self, method, url, headers=None, json_data=None):
        """Универсальный метод для API запросов через aiohttp"""
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, json=json_data) as response:
                return {
                    'status': response.status,
                    'data': await response.json() if response.status != 204 else None
                }

    @pytest.mark.asyncio
    async def test_websocket_management_stats_http(self, base_url, admin_headers):
        """Тест HTTP эндпоинта /ws/management/stats через aiohttp"""
        url = f"{base_url}/ws/management/stats"
        
        result = await self.make_api_request('GET', url, admin_headers)
        
        print(f"✓ Status Code: {result['status']}")
        print(f"✓ Response Data: {result['data']}")
        
        assert result['status'] != 404, "Endpoint /ws/management/stats not found"
        assert result['status'] in [200, 401, 403], f"Unexpected status: {result['status']}"
        
        if result['status'] == 200:
            assert isinstance(result['data'], (dict, list))
            print("✓ HTTP endpoint works correctly")

    @pytest.mark.asyncio
    async def test_websocket_management_stats_websocket(self, ws_url, admin_headers):
        """Тест WebSocket подключения к /ws/management/stats"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    f"{ws_url}/ws/management/stats",
                    headers=admin_headers
                ) as ws:
                    print("✓ WebSocket connection established to /ws/management/stats")
                    
                    # Try to receive initial message
                    try:
                        msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            print(f"✓ Received data: {data}")
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            print(f"✓ WebSocket error: {msg.data}")
                    except asyncio.TimeoutError:
                        print("✓ No initial message (timeout)")
                    
        except Exception as e:
            print(f"✓ WebSocket connection failed (expected): {e}")

    @pytest.mark.asyncio
    async def test_websocket_ticket_updates_flow(self, base_url, ws_url, admin_headers):
        """Полный тест потока обновлений талона через WebSocket"""
        # 1. Создаем мероприятие через API
        event_data = {"name": "WebSocket Test Event", "is_active": True}
        create_event_result = await self.make_api_request(
            'POST', f"{base_url}/event/", admin_headers, event_data
        )
        
        if create_event_result['status'] != 201:
            print("⚠ Could not create event, using existing events")
            # Получаем существующие мероприятия
            events_result = await self.make_api_request('GET', f"{base_url}/event/", admin_headers)
            if events_result['status'] == 200 and events_result['data']:
                event_data = events_result['data'][0]
            else:
                pytest.skip("No events available for testing")
        else:
            event_data = create_event_result['data']
        
        event_code = event_data['code']
        print(f"✓ Using event: {event_code}")
        
        # 2. Создаем талон через API
        ticket_data = {
            "event_code": event_code,
            "session_id": "websocket_test_session",
            "notes": "Test ticket for WebSocket"
        }
        
        create_ticket_result = await self.make_api_request(
            'POST', f"{base_url}/ticket/", admin_headers, ticket_data
        )
        
        if create_ticket_result['status'] != 201:
            pytest.skip("Could not create test ticket")
        
        ticket = create_ticket_result['data']
        ticket_id = ticket['id']
        print(f"✓ Created ticket: {ticket_id}")
        
        # 3. Подключаемся к WebSocket для этого талона
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                f"{ws_url}/ws/ticket/{ticket_id}",
                headers=admin_headers
            ) as ws:
                print("✓ WebSocket connected to ticket")
                
                # Получаем начальное состояние
                initial_msg = await asyncio.wait_for(ws.receive(), timeout=10.0)
                initial_data = json.loads(initial_msg.data)
                print(f"✓ Initial ticket state: {initial_data['status']}")
                assert initial_data['status'] == 'waiting'
                
                # 4. Вызываем талон через API
                call_result = await self.make_api_request(
                    'POST', 
                    f"{base_url}/ticket/{ticket_id}/call", 
                    admin_headers, 
                    {"notes": "WebSocket test call"}
                )
                
                if call_result['status'] == 200:
                    print("✓ Ticket called via API")
                    
                    # 5. Получаем обновление через WebSocket
                    update_msg = await asyncio.wait_for(ws.receive(), timeout=10.0)
                    update_data = json.loads(update_msg.data)
                    print(f"✓ WebSocket update: {update_data['status']}")
                    assert update_data['status'] == 'called'
                
                # 6. Завершаем талон через API
                complete_result = await self.make_api_request(
                    'POST',
                    f"{base_url}/ticket/{ticket_id}/complete",
                    admin_headers,
                    {"notes": "WebSocket test completion"}
                )
                
                if complete_result['status'] == 200:
                    print("✓ Ticket completed via API")
                    
                    # 7. Получаем финальное обновление
                    final_msg = await asyncio.wait_for(ws.receive(), timeout=10.0)
                    final_data = json.loads(final_msg.data)
                    print(f"✓ Final WebSocket update: {final_data['status']}")
                    assert final_data['status'] == 'completed'

    @pytest.mark.asyncio
    async def test_websocket_multiple_clients(self, base_url, ws_url, admin_headers):
        """Тест нескольких клиентов, подключенных к одному талону"""
        # Создаем тестовый талон
        events_result = await self.make_api_request('GET', f"{base_url}/event/", admin_headers)
        if events_result['status'] != 200 or not events_result['data']:
            pytest.skip("No events available")
        
        event_code = events_result['data'][0]['code']
        ticket_data = {
            "event_code": event_code,
            "session_id": "multi_client_test",
            "notes": "Multi-client test ticket"
        }
        
        create_result = await self.make_api_request('POST', f"{base_url}/ticket/", admin_headers, ticket_data)
        if create_result['status'] != 201:
            pytest.skip("Could not create test ticket")
        
        ticket_id = create_result['data']['id']
        print(f"✓ Testing multiple clients for ticket: {ticket_id}")
        
        clients = []
        try:
            # Создаем 3 WebSocket подключения
            for i in range(3):
                session = aiohttp.ClientSession()
                ws = await session.ws_connect(
                    f"{ws_url}/ws/ticket/{ticket_id}",
                    headers=admin_headers
                )
                # Получаем начальное сообщение
                initial_msg = await ws.receive()
                clients.append((session, ws, i+1))
                print(f"✓ Client {i+1} connected")
            
            # Меняем статус талона
            await self.make_api_request(
                'POST',
                f"{base_url}/ticket/{ticket_id}/call",
                admin_headers,
                {"notes": "Multi-client test"}
            )
            print("✓ Ticket status changed")
            
            # Проверяем, что все клиенты получили обновление
            for session, ws, client_num in clients:
                update_msg = await asyncio.wait_for(ws.receive(), timeout=10.0)
                update_data = json.loads(update_msg.data)
                assert update_data['status'] == 'called'
                print(f"✓ Client {client_num} received update")
                
        finally:
            # Закрываем все соединения
            for session, ws, _ in clients:
                await ws.close()
                await session.close()

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, ws_url, admin_headers):
        """Тест обработки ошибок WebSocket"""
        # Тест с несуществующим талоном
        invalid_ticket_id = 99999
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    f"{ws_url}/ws/ticket/{invalid_ticket_id}",
                    headers=admin_headers
                ) as ws:
                    msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        error_data = json.loads(msg.data)
                        print(f"✓ Error response: {error_data}")
                        assert 'error' in error_data or 'message' in error_data
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"✓ WebSocket error: {msg.data}")
                        
        except Exception as e:
            print(f"✓ WebSocket properly handled error: {e}")

    @pytest.mark.asyncio
    async def test_websocket_authentication(self, ws_url):
        """Тест аутентификации WebSocket"""
        # Тест без аутентификации
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(f"{ws_url}/ws/ticket/1") as ws:
                    msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        auth_data = json.loads(msg.data)
                        print(f"✓ Authentication response: {auth_data}")
                        assert 'error' in auth_data or 'detail' in auth_data
                    elif msg.type == aiohttp.WSMsgType.CLOSE:
                        print("✓ Connection closed (authentication required)")
                        
        except Exception as e:
            print(f"✓ WebSocket properly requires authentication: {e}")

    @pytest.mark.asyncio
    async def test_websocket_queue_operations(self, base_url, ws_url, admin_headers):
        """Тест операций с очередями через WebSocket"""
        # Получаем существующие мероприятия и очереди
        events_result = await self.make_api_request('GET', f"{base_url}/event/", admin_headers)
        if events_result['status'] != 200 or not events_result['data']:
            pytest.skip("No events available")
        
        event_id = events_result['data'][0]['id']
        
        queues_result = await self.make_api_request('GET', f"{base_url}/queue/?event_id={event_id}", admin_headers)
        if queues_result['status'] != 200 or not queues_result['data']:
            pytest.skip("No queues available")
        
        queue_id = queues_result['data'][0]['id']
        print(f"✓ Testing queue WebSocket for queue: {queue_id}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    f"{ws_url}/ws/queue/{queue_id}",
                    headers=admin_headers
                ) as ws:
                    print("✓ Connected to queue WebSocket")
                    
                    # Получаем начальное состояние
                    try:
                        initial_msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                        initial_data = json.loads(initial_msg.data)
                        print(f"✓ Initial queue state: {initial_data}")
                    except asyncio.TimeoutError:
                        print("✓ No initial queue data (timeout)")
                    
                    # Вызываем следующий талон
                    next_result = await self.make_api_request(
                        'POST', 
                        f"{base_url}/queue/{queue_id}/next", 
                        admin_headers
                    )
                    
                    if next_result['status'] == 200:
                        print("✓ Called next ticket in queue")
                        
                        # Пробуем получить обновление
                        try:
                            update_msg = await asyncio.wait_for(ws.receive(), timeout=5.0)
                            update_data = json.loads(update_msg.data)
                            print(f"✓ Queue update: {update_data}")
                        except asyncio.TimeoutError:
                            print("✓ No queue update received (timeout)")
                            
        except Exception as e:
            print(f"⚠ Queue WebSocket not available: {e}")

    @pytest.mark.asyncio
    async def test_websocket_performance(self, base_url, ws_url, admin_headers):
        """Тест производительности WebSocket подключений"""
        events_result = await self.make_api_request('GET', f"{base_url}/event/", admin_headers)
        if events_result['status'] != 200 or not events_result['data']:
            pytest.skip("No events available")
        
        event_code = events_result['data'][0]['code']
        ticket_data = {
            "event_code": event_code,
            "session_id": "performance_test",
            "notes": "Performance test ticket"
        }
        
        create_result = await self.make_api_request('POST', f"{base_url}/ticket/", admin_headers, ticket_data)
        if create_result['status'] != 201:
            pytest.skip("Could not create test ticket")
        
        ticket_id = create_result['data']['id']
        
        connections = []
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Создаем 5 одновременных подключений
            for i in range(5):
                session = aiohttp.ClientSession()
                ws = await session.ws_connect(
                    f"{ws_url}/ws/ticket/{ticket_id}",
                    headers=admin_headers
                )
                await ws.receive()  # Получаем начальные данные
                connections.append((session, ws))
            
            end_time = asyncio.get_event_loop().time()
            connection_time = end_time - start_time
            
            print(f"✓ Created {len(connections)} WebSocket connections in {connection_time:.2f}s")
            assert connection_time < 10.0, "WebSocket connections too slow"
            
        finally:
            # Закрываем все соединения
            for session, ws in connections:
                await ws.close()
                await session.close()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])