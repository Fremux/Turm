"""API endpoints for system settings management."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlmodel import Session
from app.core.limiter import limiter
from app.core.logging import logger
from app.core.config import settings
import os

router = APIRouter()


class SMTPSettings(BaseModel):
    """SMTP configuration settings."""
    
    smtp_host: str = Field(..., description="SMTP server hostname (e.g., smtp.gmail.com)")
    smtp_port: int = Field(587, description="SMTP server port (587 for TLS, 465 for SSL)")
    smtp_username: str = Field(..., description="SMTP username (usually your email)")
    smtp_password: str = Field(..., description="SMTP password (use App Password for Gmail)")
    smtp_from_email: Optional[str] = Field(None, description="From email address (defaults to username)")
    smtp_use_tls: bool = Field(True, description="Use TLS encryption")


class SMTPSettingsResponse(BaseModel):
    """SMTP settings response (without password)."""
    
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_from_email: Optional[str]
    smtp_use_tls: bool
    is_configured: bool


@router.get("/settings/smtp", response_model=SMTPSettingsResponse)
@limiter.limit("10/minute")
async def get_smtp_settings(request: Request):
    """Get current SMTP settings (without password)."""
    try:
        is_configured = bool(
            settings.SMTP_HOST and
            settings.SMTP_PORT and
            settings.SMTP_USERNAME and
            settings.SMTP_PASSWORD
        )
        
        return SMTPSettingsResponse(
            smtp_host=settings.SMTP_HOST or "",
            smtp_port=settings.SMTP_PORT or 587,
            smtp_username=settings.SMTP_USERNAME or "",
            smtp_from_email=settings.SMTP_FROM_EMAIL or "",
            smtp_use_tls=settings.SMTP_USE_TLS if hasattr(settings, 'SMTP_USE_TLS') else True,
            is_configured=is_configured
        )
    except Exception as e:
        logger.error("get_smtp_settings_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve SMTP settings")


@router.post("/settings/smtp")
@limiter.limit("5/minute")
async def update_smtp_settings(request: Request, smtp_settings: SMTPSettings):
    """Update SMTP settings.
    
    Note: This updates runtime settings only. For persistent configuration,
    add these values to your .env file or docker-compose.yml.
    """
    try:
        # Update runtime settings
        settings.SMTP_HOST = smtp_settings.smtp_host
        settings.SMTP_PORT = smtp_settings.smtp_port
        settings.SMTP_USERNAME = smtp_settings.smtp_username
        settings.SMTP_PASSWORD = smtp_settings.smtp_password
        settings.SMTP_FROM_EMAIL = smtp_settings.smtp_from_email or smtp_settings.smtp_username
        settings.SMTP_USE_TLS = smtp_settings.smtp_use_tls
        
        logger.info(
            "smtp_settings_updated",
            smtp_host=smtp_settings.smtp_host,
            smtp_port=smtp_settings.smtp_port,
            smtp_username=smtp_settings.smtp_username
        )
        
        return {
            "message": "SMTP настройки обновлены успешно!",
            "warning": "⚠️ Изменения действуют до перезапуска. Для постоянной настройки добавьте в .env файл",
            "is_configured": True
        }
    except Exception as e:
        logger.error("update_smtp_settings_error", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update SMTP settings")


@router.post("/settings/smtp/test")
@limiter.limit("3/minute")
async def test_smtp_connection(request: Request):
    """Test SMTP connection with current settings."""
    import smtplib
    
    # Check if SMTP is configured
    if not all([settings.SMTP_HOST, settings.SMTP_PORT, settings.SMTP_USERNAME, settings.SMTP_PASSWORD]):
        raise HTTPException(
            status_code=400,
            detail="SMTP не настроен. Сначала заполните настройки SMTP."
        )
    
    try:
        # Try to connect
        if settings.SMTP_USE_TLS:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        
        # Try to login
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.quit()
        
        logger.info("smtp_test_success", smtp_host=settings.SMTP_HOST)
        
        return {
            "success": True,
            "message": f"✅ Успешное подключение к {settings.SMTP_HOST}:{settings.SMTP_PORT}",
            "details": {
                "host": settings.SMTP_HOST,
                "port": settings.SMTP_PORT,
                "username": settings.SMTP_USERNAME,
                "tls": settings.SMTP_USE_TLS
            }
        }
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error("smtp_test_auth_error", error=str(e))
        raise HTTPException(
            status_code=401,
            detail=f"❌ Ошибка аутентификации: {str(e)}. Проверьте логин и пароль."
        )
    except smtplib.SMTPException as e:
        logger.error("smtp_test_error", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"❌ Ошибка SMTP: {str(e)}"
        )
    except Exception as e:
        logger.error("smtp_test_connection_error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"❌ Ошибка подключения: {str(e)}"
        )

