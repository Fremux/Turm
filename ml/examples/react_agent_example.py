"""Example of using the ReAct Agent for problem analysis.

This example demonstrates how to:
1. Classify a user message
2. Trigger the ReAct agent if category is not "other"
3. Get a comprehensive analysis result
"""

import asyncio
import json
from typing import Dict, Any

# Mock imports for example purposes
# In real usage, these would be actual imports from the application


async def mock_classify(message: str) -> Dict[str, Any]:
    """Mock classification function."""
    # Simulate classification
    if "пароль" in message.lower() or "войти" in message.lower():
        return {
            "category": "it",
            "priority": "high",
            "reasoning": "Проблема с доступом к системе",
            "confidence": 0.92
        }
    elif "справка" in message.lower() or "отпуск" in message.lower():
        return {
            "category": "hr",
            "priority": "medium",
            "reasoning": "Запрос на HR услуги",
            "confidence": 0.88
        }
    else:
        return {
            "category": "other",
            "priority": "low",
            "reasoning": "Общий вопрос",
            "confidence": 0.75
        }


async def mock_react_agent_analyze(
    message: str,
    classification: Dict[str, Any],
    session_id: str
) -> Dict[str, Any]:
    """Mock ReAct agent analysis."""
    return {
        "classification": classification,
        "session_id": session_id,
        "summary": f"""
=== АНАЛИЗ ПРОБЛЕМЫ ===

Проблема пользователя:
{message}

Классификация:
- Отдел: {classification['category'].upper()}
- Приоритет: {classification['priority'].upper()}
- Обоснование: {classification['reasoning']}

Решение:
[Здесь будет детальное решение проблемы от ReAct агента]

=== КОНЕЦ АНАЛИЗА ===
""",
        "solution": "Детальное решение проблемы...",
        "problem": message
    }


async def example_1_basic_usage():
    """Example 1: Basic usage of classifier and ReAct agent."""
    print("=" * 80)
    print("EXAMPLE 1: Basic Usage")
    print("=" * 80)
    
    # User message
    user_message = "Не могу войти в систему, пишет неверный пароль"
    session_id = "user123_1234567890"
    
    print(f"\nUser message: {user_message}")
    print(f"Session ID: {session_id}\n")
    
    # Step 1: Classify
    print("Step 1: Classifying message...")
    classification = await mock_classify(user_message)
    print(f"Classification: {json.dumps(classification, indent=2, ensure_ascii=False)}\n")
    
    # Step 2: Check if category is not "other"
    if classification["category"] != "other":
        print("Step 2: Category is not 'other', triggering ReAct agent...")
        
        # Step 3: Run ReAct agent
        result = await mock_react_agent_analyze(
            message=user_message,
            classification=classification,
            session_id=session_id
        )
        
        print("\nReAct Agent Result:")
        print(f"  Category: {result['classification']['category']}")
        print(f"  Priority: {result['classification']['priority']}")
        print(f"  Session ID: {result['session_id']}")
        print(f"\nSummary:\n{result['summary']}")
    else:
        print("Step 2: Category is 'other', skipping ReAct agent")


async def example_2_multiple_scenarios():
    """Example 2: Testing multiple scenarios."""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Multiple Scenarios")
    print("=" * 80)
    
    scenarios = [
        {
            "message": "Мне нужна справка 2-НДФЛ",
            "expected_category": "hr"
        },
        {
            "message": "Не работает VPN",
            "expected_category": "it"
        },
        {
            "message": "Как погода сегодня?",
            "expected_category": "other"
        },
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\nScenario {i}:")
        print(f"  Message: {scenario['message']}")
        
        classification = await mock_classify(scenario['message'])
        print(f"  Classified as: {classification['category']}")
        print(f"  Expected: {scenario['expected_category']}")
        
        if classification["category"] != "other":
            print(f"  ✓ ReAct agent would be triggered")
        else:
            print(f"  ✗ ReAct agent would NOT be triggered")


async def example_3_api_usage():
    """Example 3: API usage examples."""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: API Usage Examples")
    print("=" * 80)
    
    print("\n1. Analyze with ReAct Agent:")
    print("""
    curl -X POST "http://localhost:8000/api/v1/agent/analyze?session_id=test123" \\
      -H "Content-Type: application/json" \\
      -d '{"message": "Не работает почта Outlook"}'
    """)
    
    print("\n2. Chat with auto ReAct Agent:")
    print("""
    curl -X POST "http://localhost:8000/api/v1/chatbot/chat?session_id=test123&user_id=1&use_react_agent=true" \\
      -H "Content-Type: application/json" \\
      -d '{"messages": [{"role": "user", "content": "Нужен пропуск в офис"}]}'
    """)
    
    print("\n3. Classify only (no agent):")
    print("""
    curl -X POST "http://localhost:8000/api/v1/classifier/classify?session_id=test123" \\
      -H "Content-Type: application/json" \\
      -d '{"message": "Не работает принтер"}'
    """)


async def example_4_workflow():
    """Example 4: Complete workflow visualization."""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Complete Workflow")
    print("=" * 80)
    
    print("""
    User Message: "Не могу войти в корпоративную почту"
         ↓
    ┌────────────────────┐
    │   Классификатор    │
    └────────────────────┘
         ↓
    Результат:
    - Категория: IT
    - Приоритет: HIGH
    - Уверенность: 0.92
         ↓
    Проверка: category != "other" ? ✓ ДА
         ↓
    ┌────────────────────┐
    │    ReAct Agent     │
    │                    │
    │  1. Анализ         │
    │  2. Поиск решений  │
    │  3. Использование  │
    │     инструментов   │
    └────────────────────┘
         ↓
    Инструменты:
    - search_knowledge_base("outlook login issues")
    - get_similar_tickets("outlook login problems")
         ↓
    Результат:
    {
      "classification": {...},
      "session_id": "...",
      "summary": "...",
      "solution": "..."
    }
    """)


async def main():
    """Run all examples."""
    await example_1_basic_usage()
    await example_2_multiple_scenarios()
    await example_3_api_usage()
    await example_4_workflow()
    
    print("\n" + "=" * 80)
    print("Examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

