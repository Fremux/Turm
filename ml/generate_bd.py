import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from openai import OpenAI

# Конфигурация
LLM_API_KEY = "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"
LLM_MODEL = "openai/gpt-oss-120b"
LLM_BASE_URL = "https://openrouter.ai/api/v1"
NUM_THREADS = 12

# Промпт для классификации
CLASSIFICATION_PROMPT = """Классифицируй заявку в техподдержку по одной категории.

Категории:
HR - отпуска, командировки, зарплата, льготы, справки (2-НДФЛ, 182н), обучение/LMS, оклад, индексация
IT - доступы AD/VPN, установка ПО, почта Teams/Outlook, сеть Wi-Fi, GitLab/Jenkins/K8s, Docker, мониторинг, принтеры, базы данных
Finance - бухучёт, НДС, декларации, платежи в банк, 1С/SAP, ЭДО (Диадок/СБИС/Контур), проводки, реестры
Office - пропуска, парковка, переговорные, оборудование рабочих мест, гостевой Wi-Fi, телефония

Заявка: {text}

Ответь одним словом: HR, IT, Finance или Office"""

# Инициализация клиента OpenAI
client = OpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_BASE_URL
)


def classify_text(text: str, line_num: int, retry_count: int = 2) -> dict:
    """Классифицирует текст с помощью OpenAI API"""
    if not text or text.strip() == "":
        return {
            "line": line_num,
            "text": text,
            "category": "EMPTY",
            "raw_response": "",
            "error": None
        }
    
    for attempt in range(retry_count):
        try:
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": CLASSIFICATION_PROMPT.format(text=text)
                    }
                ],
                temperature=0.1,
                max_tokens=50
            )
            
            raw_response = response.choices[0].message.content.strip()
            
            # Если ответ пустой, пробуем еще раз
            if not raw_response and attempt < retry_count - 1:
                continue
            
            category = raw_response.upper()
            
            # Валидация категории
            valid_categories = ["HR", "IT", "FINANCE", "OFFICE"]
            if category not in valid_categories:
                # Попытка найти категорию в ответе
                found = False
                for valid_cat in valid_categories:
                    if valid_cat in category:
                        category = valid_cat
                        found = True
                        break
                
                # Если не нашли и есть еще попытки, пробуем снова
                if not found and attempt < retry_count - 1:
                    continue
                elif not found:
                    category = "UNKNOWN"
            
            return {
                "line": line_num,
                "text": text,
                "category": category,
                "raw_response": raw_response,
                "error": None
            }
        
        except Exception as e:
            if attempt < retry_count - 1:
                continue
            return {
                "line": line_num,
                "text": text,
                "category": "ERROR",
                "raw_response": "",
                "error": str(e)
            }
    
    # На случай, если все попытки провалились
    return {
        "line": line_num,
        "text": text,
        "category": "UNKNOWN",
        "raw_response": raw_response if 'raw_response' in locals() else "",
        "error": "All retry attempts failed"
    }


def load_dataset(file_path: str) -> list:
    """Загружает датасет из файла"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Удаляем номера строк в начале (если есть)
    cleaned_lines = []
    for i, line in enumerate(lines, 1):
        # Если строка начинается с номера и |, убираем это
        if '|' in line:
            text = line.split('|', 1)[1].strip()
        else:
            text = line.strip()
        cleaned_lines.append((i, text))
    
    return cleaned_lines


def main():
    """Основная функция"""
    print("🚀 Начинаем классификацию заявок...")
    
    # Загрузка датасета
    print("📖 Загрузка датасета...")
    dataset_path = "/root/Turm/ml/dataset.txt"
    lines = load_dataset(dataset_path)
    print(f"✅ Загружено {len(lines)} строк")
    
    # Классификация с многопоточностью
    print(f"🔄 Классификация в {NUM_THREADS} потоков...")
    results = []
    
    with ThreadPoolExecutor(max_workers=NUM_THREADS) as executor:
        # Создаём задачи
        futures = {
            executor.submit(classify_text, text, line_num): (line_num, text)
            for line_num, text in lines
        }
        
        # Обработка результатов с прогресс-баром
        for future in tqdm(as_completed(futures), total=len(futures), desc="Классификация"):
            result = future.result()
            results.append(result)
    
    # Сортировка по номеру строки
    results.sort(key=lambda x: x["line"])
    
    # Вывод первых 5 сырых ответов для отладки
    print("\n🔍 Примеры сырых ответов модели (первые 5):")
    for i, result in enumerate(results[:5]):
        print(f"  [{i+1}] Строка {result['line']}: '{result.get('raw_response', 'N/A')}' → {result['category']}")
    
    # Группировка по категориям
    print("\n📊 Группировка по категориям...")
    categorized = {
        "HR": [],
        "IT": [],
        "FINANCE": [],
        "OFFICE": [],
        "EMPTY": [],
        "UNKNOWN": [],
        "ERROR": []
    }
    
    for result in results:
        category = result["category"]
        categorized[category].append({
            "line": result["line"],
            "text": result["text"]
        })
        if result["error"]:
            print(f"⚠️  Ошибка на строке {result['line']}: {result['error']}")
    
    # Статистика
    print("\n📈 Статистика классификации:")
    for category, items in categorized.items():
        if items:
            print(f"  {category}: {len(items)} заявок")
    
    # Сохранение результатов
    output_file = "/root/Turm/ml/classified_dataset.json"
    print(f"\n💾 Сохранение результатов в {output_file}...")
    
    output = {
        "total": len(results),
        "statistics": {cat: len(items) for cat, items in categorized.items()},
        "categories": categorized,
        "all_results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Классификация завершена! Результаты сохранены в {output_file}")
    
    # Сохранение отдельных файлов по категориям
    print("\n💾 Сохранение отдельных файлов по категориям...")
    category_name_mapping = {
        "HR": "hr",
        "IT": "it",
        "FINANCE": "finance",
        "OFFICE": "office"
    }
    
    for category, items in categorized.items():
        if items and category in category_name_mapping:
            category_file = f"/root/Turm/ml/category_{category_name_mapping[category]}.json"
            with open(category_file, 'w', encoding='utf-8') as f:
                json.dump(items, f, ensure_ascii=False, indent=2)
            print(f"  ✅ {category}: {category_file}")
    
    print("\n🎉 Готово!")


if __name__ == "__main__":
    main()

