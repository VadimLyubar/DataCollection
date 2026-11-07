import os
import re
import json
import uuid
from types import SimpleNamespace
from openai import OpenAI

# ================= НАСТРОЙКИ =================
API_KEY = os.environ.get("API_KEY", "").strip()
FOLDER_ID = os.environ.get("FOLDER_ID", "").strip()

# Выделенная папка для агента (абсолютный путь)
# ALLOWED_DIRECTORY = os.path.abspath("./sandbox")
ALLOWED_DIRECTORY = r"C:\Users\vadim\Desktop\Yandex_GPT_API\SandBox"

# Максимальное количество автономных шагов за один запрос пользователя
MAX_STEPS = 10

# Создаем папку, если её нет
if not os.path.exists(ALLOWED_DIRECTORY):
    os.makedirs(ALLOWED_DIRECTORY)
# =============================================

# Инициализируем клиент OpenAI, настроенный на Yandex Cloud API
client = OpenAI(
    base_url="https://ai.api.cloud.yandex.net/v1",
    api_key=API_KEY,
    default_headers={"OpenAI-Project": FOLDER_ID}  # Передаем Folder ID в специальном заголовке
)

# Модель (rc — версия с поддержкой function calling / tools в YandexGPT)
MODEL_NAME = f"gpt://{FOLDER_ID}/yandexgpt/rc"


# --- Локальные функции (безопасные инструменты для ПК) ---
def is_safe_path(filename):
    """Проверяет, находится ли файл строго внутри разрешенной папки."""
    base_path = os.path.abspath(ALLOWED_DIRECTORY)
    target_path = os.path.abspath(os.path.join(base_path, filename))
    try:
        return os.path.commonpath([base_path, target_path]) == base_path
    except ValueError:
        return False


def list_directory():
    try:
        files = os.listdir(ALLOWED_DIRECTORY)
        return json.dumps({"status": "success", "files": files}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


def read_file(filename):
    if not is_safe_path(filename):
        return json.dumps({"status": "error", "message": "Доступ запрещен. Файл вне песочницы."}, ensure_ascii=False)
    path = os.path.join(ALLOWED_DIRECTORY, filename)
    if not os.path.exists(path):
        return json.dumps({"status": "error", "message": "Файл не найден."}, ensure_ascii=False)
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(15000)
        return json.dumps({"status": "success", "content": content}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


def write_file(filename, content):
    if not is_safe_path(filename):
        return json.dumps({"status": "error", "message": "Доступ запрещен. Запись невозможна."}, ensure_ascii=False)
    path = os.path.join(ALLOWED_DIRECTORY, filename)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"status": "success", "message": f"Файл {filename} успешно сохранен."}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


def append_file(filename, content):
    if not is_safe_path(filename):
        return json.dumps({"status": "error", "message": "Доступ запрещен."}, ensure_ascii=False)
    path = os.path.join(ALLOWED_DIRECTORY, filename)
    try:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)
        return json.dumps({"status": "success", "message": f"Текст добавлен в {filename}."}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)


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
            "description": "Дозаписывает текстовое содержимое в конец существующего файла в разрешенной папке.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {"type": "string", "description": "Имя существующего файла"},
                    "content": {"type": "string", "description": "Добавляемое текстовое содержимое файла"}
                },
                "required": ["filename", "content"]
            }
        }
    }
]

VALID_TOOL_NAMES = {t["function"]["name"] for t in tools}


def execute_tool(function_name, function_args):
    """Маршрутизатор выполнения локальных инструментов."""
    if function_name == "list_directory":
        return list_directory()
    elif function_name == "read_file":
        return read_file(function_args.get("filename", ""))
    elif function_name == "write_file":
        return write_file(function_args.get("filename", ""), function_args.get("content", ""))
    elif function_name == "append_file":
        return append_file(function_args.get("filename", ""), function_args.get("content", ""))
    else:
        return json.dumps({"status": "error", "message": f"Неизвестная функция: {function_name}"}, ensure_ascii=False)


def _extract_balanced_json(text, start_idx):
    """Извлекает сбалансированный JSON-объект {...}, корректно игнорируя скобки внутри кавычек."""
    if start_idx >= len(text) or text[start_idx] != '{':
        return None, start_idx
    depth = 0
    in_string = False
    escape = False
    for i in range(start_idx, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == '\\':
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if not in_string:
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return text[start_idx:i + 1], i + 1
    return None, start_idx


def parse_text_tool_calls(text):
    """
    Парсит текстовый тег [TOOL_CALL_START] от YandexGPT без рекурсивного захвата
    внутренних упоминаний тега внутри строковых аргументов JSON.
    """
    tag = "[TOOL_CALL_START]"
    end_tag = "[TOOL_CALL_START]"
    if not text or tag not in text:
        return [], text

    parsed_calls = []
    clean_parts = []
    pos = 0
    n = len(text)

    while pos < n:
        idx = text.find(tag, pos)
        if idx == -1:
            clean_parts.append(text[pos:])
            break

        clean_parts.append(text[pos:idx])
        cursor = idx + len(tag)
        while cursor < n and text[cursor].isspace():
            cursor += 1

        func_name = None
        args_str = "{}"
        end_pos = cursor

        if cursor < n and text[cursor] == '{':
            raw_json, next_pos = _extract_balanced_json(text, cursor)
            if raw_json:
                end_pos = next_pos
                try:
                    payload = json.loads(raw_json)
                    if isinstance(payload, dict):
                        func_name = payload.get("name") or payload.get("function")
                        raw_args = payload.get("arguments") or payload.get("parameters") or {}
                        args_str = raw_args if isinstance(raw_args, str) else json.dumps(raw_args, ensure_ascii=False)
                except json.JSONDecodeError:
                    pass
        else:
            m = re.match(r"([a-zA-Z0-9_]+)", text[cursor:])
            if m:
                candidate = m.group(1)
                after_name = cursor + m.end()
                while after_name < n and text[after_name].isspace():
                    after_name += 1
                has_paren = after_name < n and text[after_name] == '('
                if has_paren:
                    after_name += 1
                    while after_name < n and text[after_name].isspace():
                        after_name += 1
                if after_name < n and text[after_name] == '{':
                    raw_json, next_pos = _extract_balanced_json(text, after_name)
                    if raw_json:
                        func_name = candidate
                        args_str = raw_json
                        end_pos = next_pos
                        if has_paren:
                            while end_pos < n and text[end_pos].isspace():
                                end_pos += 1
                            if end_pos < n and text[end_pos] == ')':
                                end_pos += 1

        # Пропускаем опциональный закрывающий тег [TOOL_CALL_START]
        temp_pos = end_pos
        while temp_pos < n and text[temp_pos].isspace():
            temp_pos += 1
        if text.startswith(end_tag, temp_pos):
            end_pos = temp_pos + len(end_tag)

        if func_name and func_name in VALID_TOOL_NAMES:
            call_obj = SimpleNamespace(
                id=f"text_call_{uuid.uuid4().hex[:12]}",
                type="function",
                function=SimpleNamespace(
                    name=func_name,
                    arguments=args_str
                )
            )
            parsed_calls.append(call_obj)
            pos = end_pos
        else:
            # Если тег ложный или находится внутри текста, продвигаемся дальше без поломки
            pos = idx + len(tag)

    cleaned_text = "".join(clean_parts).strip()
    return parsed_calls, cleaned_text


# --- Основной цикл Агента ---
def run_agent():
    print(f"🤖 Агент запущен! Доступная папка: {ALLOWED_DIRECTORY}")
    print("Напишите 'exit' для выхода.")

    # Храним историю переписки для удержания контекста
    messages = [
        {
            "role": "system",
            "content": (
                "Ты полезный ИИ-агент. У тебя есть доступ к локальным файлам в выделенной папке. "
                "Используй инструменты для чтения, создания файлов и вывода списков по запросу пользователя. "
                "Если нужно записать большой файл, разбивай запись на части через write_file и append_file."
            )
        }
    ]

    while True:
        user_input = input("\nВы: ").strip()
        if user_input.lower() in ['exit', 'quit']:
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        step = 0
        while step < MAX_STEPS:
            step += 1
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
                break

            response_message = response.choices[0].message
            raw_content = response_message.content or ""

            # Проверяем нативные tool_calls или текстовый тег [TOOL_CALL_START]
            tool_calls = list(response_message.tool_calls) if response_message.tool_calls else []
            cleaned_text = raw_content

            if not tool_calls and "[TOOL_CALL_START]" in raw_content:
                parsed_calls, cleaned_text = parse_text_tool_calls(raw_content)
                if parsed_calls:
                    tool_calls = parsed_calls
                    print(f"ℹ️ [Шаг {step}] Распознан текстовый тег [TOOL_CALL_START] ({len(tool_calls)} шт.)")

            if tool_calls:
                # Сохраняем валидный вызов инструментов в историю в стандартном формате
                assistant_msg = {
                    "role": "assistant",
                    "content": cleaned_text if cleaned_text else None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in tool_calls
                    ]
                }
                messages.append(assistant_msg)

                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    if function_name not in VALID_TOOL_NAMES:
                        print(f"⚠️ [Шаг {step}] Пропущен неизвестный инструмент [{function_name}].")
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps({"status": "error", "message": f"Неизвестный инструмент: {function_name}"}, ensure_ascii=False)
                        })
                        continue

                    try:
                        function_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    except json.JSONDecodeError:
                        print(f"⚠️ [Шаг {step}] Ошибка парсинга аргументов JSON для [{function_name}].")
                        messages.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps({
                                "status": "error",
                                "message": "JSON оборвался из-за слишком длинного текста. Разбей текст на части и запиши через write_file и append_file."
                            }, ensure_ascii=False)
                        })
                        continue

                    print(f"⚙️ [Шаг {step}] Вызов функции [{function_name}] с аргументами: {function_args}")
                    result = execute_tool(function_name, function_args)


# ------------------- Реестр инструментов -------------------

TOOLS = {}


def tool(description: str, parameters: dict):
    """Регистрирует функцию как инструмент для Function Calling."""
    def decorator(func):
        TOOLS[func.__name__] = {
            "func": func,
            "schema": {
                "type": "function",
                "function": {
                    "name": func.__name__,
                    "description": description,
                    "parameters": parameters,
                },
            },
        }
        return func
    return decorator


@tool("Получить текущую дату и время компьютера пользователя",
      {"type": "object", "properties": {}, "required": []})
def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool("Вычислить математическое выражение, например '2*(3+4)/5'",
      {"type": "object",
       "properties": {"expression": {"type": "string",
                                     "description": "Математическое выражение"}},
       "required": ["expression"]})
def calculate(expression: str):
    allowed = {name: getattr(math, name) for name in
               ["sqrt", "sin", "cos", "tan", "log", "log10", "exp", "pi", "e", "floor", "ceil"]}
    if not set(expression) <= set("0123456789+-*/(). ,^%abcdeilnorstqx"):
        raise ValueError("Недопустимые символы в выражении")
    return eval(expression, {"__builtins__": {}, **allowed})


# ------------------- Вызов инструментов -------------------

def run_tool_calls(tool_calls) -> list[dict]:
    """Выполняет функции, которые запросила модель, и возвращает результаты."""
    messages = []
    for call in tool_calls:
        name = call.function.name
        try:
            args = json.loads(call.function.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        entry = TOOLS.get(name)
        if entry is None:
            result = f"Ошибка: неизвестный инструмент '{name}'"
        else:
            try:
                result = entry["func"](**args)
            except Exception as e:
                result = f"Ошибка выполнения: {e}"
        print(f"  [инструмент] {name}({args}) -> {str(result)[:120]}")
        messages.append({"role": "tool", "tool_call_id": call.id,
                         "content": str(result)})
    return messages


# ------------------- Сессии -------------------

def load_session(name: str) -> list[dict] | None:
    path = SESSIONS_DIR / f"{name}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def save_session(name: str, messages: list[dict]) -> None:
    SESSIONS_DIR.mkdir(exist_ok=True)
    path = SESSIONS_DIR / f"{name}.json"
    path.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")


# ------------------- Консольный цикл -------------------

def main():
    parser = argparse.ArgumentParser(description="Консольный агент YandexGPT")
    parser.add_argument("session", nargs="?", default="default",
                        help="имя сессии (файл sessions/<имя>.json)")
    args = parser.parse_args()

    existing = load_session(args.session)
    agent = Agent(MODEL_NAME, existing)
    if existing:
        print(f"Сессия '{args.session}' загружена ({len(existing)} сообщений).")
    else:
        print(f"Новая сессия '{args.session}'. Команды: /new, /sessions, /load <имя>, /exit")
    save_session(args.session, agent.messages)

    while True:
        try:
            user_text = input("Вы: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nВыход.")
            return
        if not user_text:
            continue
        if user_text == "/exit":
            print("Выход.")
            return
        if user_text == "/new":
            args.session = f"auto_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            agent = Agent(MODEL_NAME, None)
            print(f"Начата новая сессия '{args.session}'.")
        elif user_text.startswith("/load"):
            name = user_text.split(maxsplit=1)[1].strip() if len(user_text.split()) > 1 else ""
            if not name:
                print("Укажи имя: /load имя_сессии")
                continue
            data = load_session(name)
            if data is None:
                print("Сессия не найдена.")
                continue
            args.session, agent = name, Agent(MODEL_NAME, data)
            print(f"Сессия '{name}' загружена.")
        elif user_text == "/sessions":
            if SESSIONS_DIR.exists():
                for p in sorted(SESSIONS_DIR.glob("*.json")):
                    print(" -", p.stem)
            else:
                print("Сессий пока нет.")
        else:
            answer = agent.respond(user_text)
            print(f"Агент: {answer}\n")
        save_session(args.session, agent.messages)  # сохраняем после каждого хода


if __name__ == "__main__":
    main()
