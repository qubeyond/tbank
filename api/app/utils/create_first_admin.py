import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models import Account
from app.core.security import security_service


async def create_first_admin() -> None:
    """Создает первого суперадминистратора системы.
    
    Суперадмин будет иметь полный доступ ко всем функциям системы
    и сможет создавать других администраторов в будущем.
    """

    async with AsyncSessionLocal() as session:  
        existing_admin = await session.scalar(
            select(Account).where(Account.username == "superadmin")
        )
        
        if existing_admin:
            print("Суперадминистратор уже существует")
            return
        
        admin = Account(
            username="superadmin",
            email="superadmin@tbank.ru",
            hashed_password=security_service.get_password_hash("superadmin123"),
            is_active=True
        )
        
        session.add(admin)
        await session.commit()
        

if __name__ == "__main__":
    asyncio.run(create_first_admin())