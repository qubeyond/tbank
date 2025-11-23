import pytest
from fastapi.testclient import TestClient
import sys
import os

# Добавляем корень проекта в Python path
sys.path.insert(0, '/app')

from app.main import app  # Правильный импорт


@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def admin_client(client, admin_token):
    client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return client

@pytest.fixture
def db_session():
    """Фикстура для тестовой сессии БД"""
    # Ваша реализация тестовой сессии БД
    pass

@pytest.fixture
def test_queue2(db_session, test_ticket):
    """Вторая тестовая очередь для перемещения"""
    from app.db.models import Queue
    queue = Queue(event_id=test_ticket.queue.event_id, name="Q2")
    db_session.add(queue)
    db_session.commit()
    return queue