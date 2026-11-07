import os
import json
from openai import OpenAI

# ================= НАСТРОЙКИ =================
API_KEY = os.environ.get("API_KEY", "").strip()
FOLDER_ID = os.environ.get("FOLDER_ID", "").strip()
# Выделенная папка для агента (абсолютный путь)
# ALLOWED_DIRECTORY = os.path.abspath("./sandbox")
ALLOWED_DIRECTORY = "C:\\Users\\vadim\\Desktop\\Yandex_GPT_API\\SandBox"

# Создаем папку, если её нет
if not os.path.exists(ALLOWED_DIRECTORY):
    os.makedirs(ALLOWED_DIRECTORY)
# =============================================

# Инициализируем клиент OpenAI, настроенный на Yandex Cloud API
client = OpenAI(
    base_url="https://ai.api.cloud.yandex.net/v1",
    api_key=API_KEY,
    default_headers={"OpenAI-Project": FOLDER_ID} # Передаем Folder ID в специальном заголовке
)

# Модель (rc — версия с поддержкой function calling / tools в YandexGPT)
MODEL_NAME = f"gpt://{FOLDER_ID}/yandexgpt/rc"


# --- Локальные функции (безопасные инструменты для ПК) ---

def is_safe_path(filename):
    """Проверяет, находится ли файл строго внутри разрешенной папки."""
    target_path = os.path.abspath(os.path.join(ALLOWED_DIRECTORY, filename))
    return target_path.startswith(ALLOWED_DIRECTORY)

def list_directory():
    try:
        files = os.listdir(ALLOWED_DIRECTORY)
        return json.dumps({"status": "success", "files": files}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def read_file(filename):
    if not is_safe_path(filename):
        return json.dumps({"status": "error", "message": "Доступ запрещен. Файл вне песочницы."})
    
    path = os.path.join(ALLOWED_DIRECTORY, filename)
    if not os.path.exists(path):
        return json.dumps({"status": "error", "message": "Файл не найден."})
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(10000) # Ограничим чтение 10к символов для экономии контекста
        return json.dumps({"status": "success", "content": content}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def write_file(filename, content):
    if not is_safe_path(filename):
        return json.dumps({"status": "error", "message": "Доступ запрещен. Запись невозможна."})
    
    path = os.path.join(ALLOWED_DIRECTORY, filename)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"status": "success", "message": f"Файл {filename} успешно сохранен."}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

def append_file(filename, content):
    if not is_safe_path(filename):
        return json.dumps({"status": "error", "message": "Доступ запрещен."})
    path = os.path.join(ALLOWED_DIRECTORY, filename)
    try:
        with open(path, 'a', encoding='utf-8') as f:  # Режим 'a' (append) дописывает в конец
            f.write(content)
        return json.dumps({"status": "success", "message": f"Текст добавлен в {filename}."}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)})

# --- Манифест инструментов (Tools JSON Schema для YandexGPT) ---
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Показывает список всех файлов и папок внутри разрешенной директории.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Читает текстовое содержимое указанного файла из разрешенной папки.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Имя файла (например, notes.txt)"}
                },
                "required": ["filename"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Создает новый файл или перезаписывает существующий в разрешенной папке.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Имя создаваемого файла"},
                    "content": {"type": "string", "description": "Текстовое содержимое файла"}
                },
                "required": ["filename", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "append_file",
            "description": "Дозаписывает текстовое содержимое в конец сущесвтующего файла в разрешенной папке.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Имя сущесвтующего файла"},
                    "content": {"type": "string", "description": "Добавляемое текстовое содержимое файла"}
                },
                "required": ["filename","content"]
            }
        }
    }
]

# --- Основной цикл Агента ---

def run_agent():
    print(f"🤖 Агент запущен! Доступная папка: {ALLOWED_DIRECTORY}")
    print("Напишите 'exit' для выхода.")
    
    # Храним историю переписки для удержания контекста
    messages = [
        {"role": "system", "content": "Ты полезный ИИ-агент. У тебя есть доступ к локальным файлам в выделенной папке. Используй инструменты для чтения, создания файлов и вывода списков по запросу пользователя."}
    ]
    
    while True:
        user_input = input("\nВы: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
        if not user_input:
            continue
            
        messages.append({"role": "user", "content": user_input})
        
        # Шаг 1: отправляем запрос в YandexGPT со списком доступных инструментов
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                max_tokens=8192
            )
        except Exception as e:
            print(f"❌ Ошибка API: {e}")
            messages.pop() # Удаляем последний запрос пользователя из-за ошибки
            continue

        response_message = response.choices[0].message
        
        # Шаг 2: Проверяем, решила ли модель вызвать функцию (инструмент)
        if response_message.tool_calls:
            # Модель решила запустить функцию. Добавляем ее ответ в историю
            messages.append(response_message)
            
            # Обрабатываем все вызовы (их может быть несколько в одном ответе)
            for tool_call in response_message.tool_calls:
                function_name = tool_call.function.name
                # function_args = json.loads(tool_call.function.arguments)
                try:
                    function_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    print("⚠️ Ошибка: Модель попыталась передать слишком длинный текст, и JSON оборвался.")
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps({"status": "error", "message": "JSON оборвался из-за слишком длинного текста. Разбей текст на части и запиши через write_file и append_file."}, ensure_ascii=False)
                    })
                    continue
                
                print(f"⚙️ Вызов функции [{function_name}] с аргументами: {function_args}")
                
                # Исполняем реальный код на Python в зависимости от выбора ИИ
                if function_name == "list_directory":
                    result = list_directory()
                elif function_name == "read_file":
                    result = read_file(function_args.get("filename"))
                elif function_name == "write_file":
                    result = write_file(function_args.get("filename"), function_args.get("content"))
                elif function_name == "append_file":
                    result = append_file(function_args.get("filename"), function_args.get("content"))
                else:
                    result = json.dumps({"error": "Неизвестная функция"})
                
                # Отправляем результат выполнения функции обратно модели
                messages.append({
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": result
                })
            
            # Шаг 3: Получаем финальный ответ от модели с учетом выполненных функций
            second_response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages
            )
            final_text = second_response.choices[0].message.content
            print(f"\n🤖 Агент: {final_text}")
            messages.append({"role": "assistant", "content": final_text})
            
        else:
            # Если модель ответила просто текстом без вызова функций
            final_text = response_message.content
            print(f"\n🤖 Агент: {final_text}")
            messages.append({"role": "assistant", "content": final_text})

if __name__ == "__main__":
    run_agent()
