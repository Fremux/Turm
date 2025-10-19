"""DateTime tool for working with dates and time.

This tool helps with date/time operations like getting current time,
calculating differences, formatting dates, etc.
"""

from typing import Type, Optional
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from datetime import datetime, timedelta
import pytz

from app.core.logging import logger


class DateTimeInput(BaseModel):
    """Input schema for datetime operations."""
    
    operation: str = Field(
        ...,
        description="Операция: 'current' (текущее время), 'add' (добавить дни), 'diff' (разница между датами), 'format' (форматировать дату)"
    )
    date: Optional[str] = Field(
        default=None,
        description="Дата в формате YYYY-MM-DD (опционально, для операций add/diff/format)"
    )
    days: Optional[int] = Field(
        default=None,
        description="Количество дней для добавления (для операции add)"
    )
    date2: Optional[str] = Field(
        default=None,
        description="Вторая дата для операции diff (формат YYYY-MM-DD)"
    )
    timezone: Optional[str] = Field(
        default="Europe/Moscow",
        description="Часовой пояс (по умолчанию Europe/Moscow)"
    )


class DateTimeTool(BaseTool):
    """Tool for date and time operations."""
    
    name: str = "datetime_helper"
    description: str = """
    Помогает работать с датами и временем.
    
    Используй этот инструмент когда:
    - Нужно узнать текущую дату/время
    - Требуется вычислить дату в будущем/прошлом
    - Нужно рассчитать разницу между датами
    - Требуется отформатировать дату
    
    Операции:
    - current: получить текущую дату и время
    - add: добавить N дней к дате (параметры: date, days)
    - diff: разница между двумя датами в днях (параметры: date, date2)
    - format: отформатировать дату (параметр: date)
    
    Входные параметры:
    - operation: тип операции
    - date: дата в формате YYYY-MM-DD (для add/diff/format)
    - days: количество дней (для add)
    - date2: вторая дата (для diff)
    - timezone: часовой пояс (по умолчанию Europe/Moscow)
    """
    args_schema: Type[BaseModel] = DateTimeInput
    
    async def _arun(
        self,
        operation: str,
        date: Optional[str] = None,
        days: Optional[int] = None,
        date2: Optional[str] = None,
        timezone: str = "Europe/Moscow"
    ) -> str:
        """Perform datetime operation asynchronously.
        
        Args:
            operation: Type of operation
            date: Date string (YYYY-MM-DD)
            days: Number of days to add
            date2: Second date for diff operation
            timezone: Timezone name
            
        Returns:
            Result of the operation as string
        """
        try:
            logger.info("datetime_operation_started", operation=operation, date=date)
            
            tz = pytz.timezone(timezone)
            
            # Current date/time
            if operation == "current":
                now = datetime.now(tz)
                result = f"Текущая дата и время ({timezone}): {now.strftime('%Y-%m-%d %H:%M:%S')}"
                result += f"\nДень недели: {self._get_weekday_ru(now.weekday())}"
                return result
            
            # Add days to date
            elif operation == "add":
                if not date or days is None:
                    return "Ошибка: для операции 'add' нужны параметры date и days"
                
                base_date = datetime.strptime(date, "%Y-%m-%d")
                new_date = base_date + timedelta(days=days)
                
                result = f"{date} + {days} дней = {new_date.strftime('%Y-%m-%d')}"
                result += f"\nДень недели: {self._get_weekday_ru(new_date.weekday())}"
                return result
            
            # Difference between dates
            elif operation == "diff":
                if not date or not date2:
                    return "Ошибка: для операции 'diff' нужны параметры date и date2"
                
                date1_obj = datetime.strptime(date, "%Y-%m-%d")
                date2_obj = datetime.strptime(date2, "%Y-%m-%d")
                diff = abs((date2_obj - date1_obj).days)
                
                result = f"Разница между {date} и {date2}: {diff} дней"
                
                # Add weeks if > 7 days
                if diff >= 7:
                    weeks = diff // 7
                    remaining_days = diff % 7
                    result += f" ({weeks} недель и {remaining_days} дней)"
                
                return result
            
            # Format date
            elif operation == "format":
                if not date:
                    return "Ошибка: для операции 'format' нужен параметр date"
                
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                
                result = f"Дата {date}:\n"
                result += f"- Полный формат: {date_obj.strftime('%d %B %Y')}\n"
                result += f"- День недели: {self._get_weekday_ru(date_obj.weekday())}\n"
                result += f"- Неделя года: {date_obj.isocalendar()[1]}\n"
                result += f"- Квартал: {(date_obj.month - 1) // 3 + 1}"
                
                return result
            
            else:
                return f"Неизвестная операция: {operation}. Доступные: current, add, diff, format"
            
        except ValueError as e:
            error_msg = f"Ошибка в формате даты: {str(e)}. Используйте формат YYYY-MM-DD"
            logger.warning("datetime_invalid_format", error=str(e))
            return error_msg
        except Exception as e:
            error_msg = f"Ошибка при работе с датой: {str(e)}"
            logger.error("datetime_error", error=str(e), operation=operation, exc_info=True)
            return error_msg
    
    def _get_weekday_ru(self, weekday: int) -> str:
        """Get Russian weekday name."""
        days = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        return days[weekday]
    
    def _run(
        self,
        operation: str,
        date: Optional[str] = None,
        days: Optional[int] = None,
        date2: Optional[str] = None,
        timezone: str = "Europe/Moscow"
    ) -> str:
        """Synchronous version (not implemented - use async)."""
        raise NotImplementedError("Use async version (_arun) instead")




