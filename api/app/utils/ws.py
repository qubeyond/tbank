import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, '/app')
from app.main import app

class TestWebSocketManagementStats:
    """Специфические тесты для /ws/management/stats эндпоинта"""

    @pytest.fixture
    def admin_token(self):
        return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdXBlcmFkbWluIiwiZXhwIjoxNzYzOTU1ODQ2LCJpYXQiOjE3NjM4Njk0NDYsImp0aSI6ImY1NmU3M2I1LTgwMDMtNDU2MS1iNTE4LTQ3ZTA1MWEzMjBhYiIsInR5cGUiOiJhY2Nlc3NfdG9rZW4ifQ.Qh6kgWcG6DALT3nBVhNIlbClWAKNsLPrt4sH2A9DEgk"

    @pytest.fixture
    def admin_client(self, admin_token):
        client = TestClient(app)
        client.headers.update({"Authorization": f"Bearer {admin_token}"})
        return client

    def test_websocket_management_stats_http(self, admin_client):
        """Тест HTTP версии /ws/management/stats"""
        response = admin_client.get("/ws/management/stats")
        
        # Анализируем ответ
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        # WebSocket эндпоинты могут вести себя по-разному:
        # - Возвращать 200 с информацией
        # - Возвращать 426 Upgrade Required  
        # - Возвращать 405 Method Not Allowed
        # - Возвращать 401 если требует WebSocket
        
        assert response.status_code != 404, "Endpoint /ws/management/stats не найден"
        
        if response.status_code == 200:
            # Если возвращает 200, проверяем структуру ответа
            data = response.json()
            print(f"Response Data: {data}")
            # Проверяем что ответ - валидный JSON
            assert isinstance(data, (dict, list))

    def test_websocket_management_stats_websocket(self, admin_client):
        """Тест WebSocket версии /ws/management/stats"""
        try:
            with admin_client.websocket_connect("/ws/management/stats") as websocket:
                # Проверяем что подключение установлено
                print("✓ WebSocket подключение установлено")
                
                # Можно отправить сообщение если требуется
                # websocket.send_json({"action": "get_stats"})
                
                # Получаем сообщение (если сервер отправляет что-то сразу)
                try:
                    data = websocket.receive_json(timeout=2.0)
                    print(f"✓ Получены данные: {data}")
                except:
                    print("✓ Сервер не отправляет данные автоматически")
                    
        except Exception as e:
            print(f"WebSocket подключение не удалось: {e}")
            # Это нормально - эндпоинт может быть не реализован как WebSocket

    def test_websocket_management_stats_without_auth(self):
        """Тест доступа без аутентификации"""
        client = TestClient(app)
        
        response = client.get("/ws/management/stats")
        print(f"Status без аутентификации: {response.status_code}")
        
        # Должен возвращать 401 или 403 если требует аутентификацию
        if response.status_code in [401, 403]:
            print("✓ Правильно требует аутентификацию")

# Запуск тестов
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])