"""Calculator tool for mathematical calculations.

Simple calculator tool that can evaluate mathematical expressions safely.
"""

from typing import Type
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
import ast
import operator

from app.core.logging import logger


class CalculatorInput(BaseModel):
    """Input schema for calculator."""
    
    expression: str = Field(
        ...,
        description="Математическое выражение для вычисления, например: '2 + 2', '10 * 5 - 3', '100 / 4'"
    )


class CalculatorTool(BaseTool):
    """Tool for performing mathematical calculations."""
    
    name: str = "calculate"
    description: str = """
    Выполняет математические вычисления.
    
    Используй этот инструмент когда:
    - Нужно выполнить математические операции
    - Требуется точный расчет (суммы, проценты, разность и т.д.)
    
    Поддерживаемые операции:
    - Сложение (+), вычитание (-)
    - Умножение (*), деление (/)
    - Степень (**)
    - Скобки для приоритета операций
    
    Входные параметры:
    - expression: математическое выражение (например: "2 + 2", "10 * (5 + 3)")
    
    Возвращает результат вычисления.
    """
    args_schema: Type[BaseModel] = CalculatorInput
    
    # Safe operators for evaluation
    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
    }
    
    def _eval_expr(self, node):
        """Safely evaluate an AST node."""
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            op = self._operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
            return op(self._eval_expr(node.left), self._eval_expr(node.right))
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand>
            op = self._operators.get(type(node.op))
            if op is None:
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            return op(self._eval_expr(node.operand))
        else:
            raise ValueError(f"Unsupported expression type: {type(node).__name__}")
    
    async def _arun(self, expression: str) -> str:
        """Perform calculation asynchronously.
        
        Args:
            expression: Mathematical expression to evaluate
            
        Returns:
            Result of the calculation as string
        """
        try:
            logger.info("calculation_started", expression=expression)
            
            # Parse and evaluate the expression safely
            tree = ast.parse(expression, mode='eval')
            result = self._eval_expr(tree.body)
            
            # Format result
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            
            output = f"Результат вычисления '{expression}' = {result}"
            
            logger.info("calculation_completed", expression=expression, result=result)
            return output
            
        except ZeroDivisionError:
            error_msg = f"Ошибка: деление на ноль в выражении '{expression}'"
            logger.warning("calculation_division_by_zero", expression=expression)
            return error_msg
        except (ValueError, SyntaxError, TypeError) as e:
            error_msg = f"Ошибка в выражении '{expression}': {str(e)}"
            logger.warning("calculation_invalid_expression", expression=expression, error=str(e))
            return error_msg
        except Exception as e:
            error_msg = f"Ошибка при вычислении: {str(e)}"
            logger.error("calculation_error", error=str(e), expression=expression, exc_info=True)
            return error_msg
    
    def _run(self, expression: str) -> str:
        """Synchronous version (not implemented - use async)."""
        raise NotImplementedError("Use async version (_arun) instead")




