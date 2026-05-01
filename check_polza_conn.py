import os
import requests
from dotenv import load_dotenv

def check_connection():
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    # В vite.config.ts прокси указывает на https://api.polza.ai
    # Обычно API эндпоинт /api/v1
    base_url = "https://api.polza.ai/api/v1"
    
    if not api_key:
        print("Ошибка: GEMINI_API_KEY не найден в .env")
        return

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    print(f"Проверка связи с {base_url}...")
    try:
        # Пробуем получить список моделей
        response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
        print(f"Статус ответа: {response.status_code}")
        if response.status_code == 200:
            models = response.json().get('data', [])
            print(f"Связь установлена успешно. Доступно моделей: {len(models)}")
            if models:
                print(f"Пример модели: {models[0].get('id')}")
        else:
            print(f"Ошибка при подключении: {response.text}")
    except Exception as e:
        print(f"Исключение при запросе: {e}")

if __name__ == "__main__":
    check_connection()
