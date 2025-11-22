import uuid
from datetime import datetime, timedelta
from typing import Optional, Set
import hashlib

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic_settings import BaseSettings


token_blacklist: Set[str] = set()


class SecuritySettings(BaseSettings):
    """Настройки безопасности системы."""
    
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 часа
    
    class Config:
        env_file = ".env"
        case_sensitive = False


CORS_SETTINGS = {
    "allow_origins": [
        "http://frontend:80",
        "http://localhost:3000",
        "http://localhost",
        "http://localhost:5173",
    ],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}


class SecurityService:
    """Сервис для работы с безопасностью и аутентификацией."""
    
    def __init__(self, settings: SecuritySettings = SecuritySettings()):
        self.settings = settings
        self.pwd_context = CryptContext(
            schemes=["pbkdf2_sha256"], 
            deprecated="auto",
            pbkdf2_sha256__default_rounds=30000
        )
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Проверяет соответствие пароля и хеша."""

        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Создает хеш пароля."""

        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: dict) -> str:
        """Создает JWT access токен."""
        
        if not self.settings.JWT_SECRET_KEY:
            raise ValueError("JWT_SECRET_KEY не установлен")
        
        to_encode = data.copy()
        
        expire = datetime.utcnow() + timedelta(minutes=self.settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),  
            "jti": str(uuid.uuid4()),  
            "type": "access_token"
        })
        
        return jwt.encode(to_encode, self.settings.JWT_SECRET_KEY, algorithm=self.settings.JWT_ALGORITHM)
    
    def verify_access_token(self, token: str) -> Optional[dict]:
        """Проверяет и декодирует JWT токен."""

        try:
            if self.is_token_blacklisted(token):
                return None
                
            payload = jwt.decode(
                token, 
                self.settings.JWT_SECRET_KEY, 
                algorithms=[self.settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError:
            return None
    
    def add_to_blacklist(self, token: str):
        """Добавляет токен в blacklist."""
        
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        token_blacklist.add(token_hash)
    
    def is_token_blacklisted(self, token: str) -> bool:
        """Проверяет, находится ли токен в blacklist."""

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token_hash in token_blacklist
    
    def clear_blacklist(self):
        """Очищает blacklist (для тестирования)."""

        token_blacklist.clear()


security_service = SecurityService()
