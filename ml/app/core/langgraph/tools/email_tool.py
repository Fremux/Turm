"""Email sending tool for agents.

This tool enables agents to send emails using SMTP.
Supports both text and HTML emails with configurable SMTP settings.
"""

import asyncio
from typing import Type, Optional
from pydantic import BaseModel, Field, EmailStr
from langchain_core.tools import BaseTool
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.config import settings
from app.core.logging import logger


class EmailInput(BaseModel):
    """Input schema for sending emails."""
    
    to: str = Field(
        ...,
        description="Email получателя (например: user@example.com)"
    )
    subject: str = Field(
        ...,
        description="Тема письма"
    )
    body: str = Field(
        ...,
        description="Содержание письма (текст)"
    )
    cc: Optional[str] = Field(
        default=None,
        description="Email для копии (CC), опционально"
    )


class EmailTool(BaseTool):
    """Tool for sending emails via SMTP."""
    
    name: str = "send_email"
    description: str = """
    Отправляет email сообщения через SMTP.
    
    Используй этот инструмент когда:
    - Нужно отправить уведомление пользователю
    - Требуется переслать информацию по email
    - Нужно отправить подтверждение или напоминание
    
    Входные параметры:
    - to: email получателя (обязательно)
    - subject: тема письма (обязательно)
    - body: текст письма (обязательно)
    - cc: копия письма (опционально)
    
    Требует настройки SMTP сервера в конфигурации системы.
    """
    args_schema: Type[BaseModel] = EmailInput
    
    def _is_configured(self) -> bool:
        """Check if SMTP is configured."""
        return bool(
            getattr(settings, 'SMTP_HOST', None) and
            getattr(settings, 'SMTP_PORT', None) and
            getattr(settings, 'SMTP_USERNAME', None) and
            getattr(settings, 'SMTP_PASSWORD', None)
        )
    
    async def _arun(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None
    ) -> str:
        """Send email asynchronously.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (text)
            cc: CC email address (optional)
            
        Returns:
            Success or error message
        """
        try:
            # Check if SMTP is configured
            if not self._is_configured():
                error_msg = """SMTP не настроен! 

Для отправки email необходимо настроить SMTP сервер в админ-панели:
1. Перейдите в раздел "Настройки"
2. Заполните данные SMTP сервера
3. Сохраните настройки

Или задайте переменные окружения:
- SMTP_HOST (например: smtp.gmail.com)
- SMTP_PORT (обычно 587 для TLS)
- SMTP_USERNAME (ваш email)
- SMTP_PASSWORD (пароль приложения)
"""
                logger.warning("email_tool_not_configured")
                return error_msg
            
            logger.info("email_sending_started", to=to, subject=subject)
            
            # Get SMTP settings
            smtp_host = settings.SMTP_HOST
            smtp_port = settings.SMTP_PORT
            smtp_user = settings.SMTP_USERNAME
            smtp_password = settings.SMTP_PASSWORD
            smtp_from = getattr(settings, 'SMTP_FROM_EMAIL', smtp_user)
            use_tls = getattr(settings, 'SMTP_USE_TLS', True)
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = smtp_from
            msg['To'] = to
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
            
            # Add body
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)
            
            # Send email in thread pool to avoid blocking
            def send_sync():
                try:
                    # Connect to SMTP server
                    if use_tls:
                        server = smtplib.SMTP(smtp_host, smtp_port)
                        server.starttls()
                    else:
                        server = smtplib.SMTP_SSL(smtp_host, smtp_port)
                    
                    # Login
                    server.login(smtp_user, smtp_password)
                    
                    # Send email
                    recipients = [to]
                    if cc:
                        recipients.append(cc)
                    
                    server.sendmail(smtp_from, recipients, msg.as_string())
                    server.quit()
                    
                    return True
                except Exception as e:
                    logger.error("smtp_send_error", error=str(e), exc_info=True)
                    raise
            
            # Run in executor
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, send_sync)
            
            success_msg = f"""✅ Email успешно отправлен!

Кому: {to}
Тема: {subject}
{f'Копия: {cc}' if cc else ''}

Письмо доставлено через {smtp_host}"""
            
            logger.info(
                "email_sent_successfully",
                to=to,
                subject=subject,
                smtp_host=smtp_host
            )
            
            return success_msg
            
        except smtplib.SMTPAuthenticationError:
            error_msg = f"""❌ Ошибка аутентификации SMTP!

Проверьте:
1. Логин и пароль SMTP сервера
2. Для Gmail используйте "Пароль приложения" (App Password)
3. Включена ли двухфакторная аутентификация

Текущий сервер: {getattr(settings, 'SMTP_HOST', 'не настроен')}
Пользователь: {getattr(settings, 'SMTP_USERNAME', 'не настроен')}"""
            
            logger.error("smtp_auth_error", to=to)
            return error_msg
            
        except smtplib.SMTPException as e:
            error_msg = f"❌ Ошибка SMTP: {str(e)}"
            logger.error("smtp_error", error=str(e), to=to, exc_info=True)
            return error_msg
            
        except Exception as e:
            error_msg = f"❌ Ошибка отправки email: {str(e)}"
            logger.error("email_send_error", error=str(e), to=to, exc_info=True)
            return error_msg
    
    def _run(
        self,
        to: str,
        subject: str,
        body: str,
        cc: Optional[str] = None
    ) -> str:
        """Synchronous version (not implemented - use async)."""
        raise NotImplementedError("Use async version (_arun) instead")




