#!/usr/bin/env python3
"""Консольный агент на YandexGPT API.

Возможности:
- диалог с моделью через OpenAI-совместимый эндпоинт AI Studio;
- Function Calling (модель вызывает локальные Python-функции);
- сохранение/загрузка сессии на диск (JSON).

Запуск: python agent.py [имя_сессии]
Настройки: переменные окружения YANDEX_API_KEY и YANDEX_FOLDER_ID
(или файл .env рядом со скриптом).
"""

import argparse
import json
import math
import os
from datetime import datetime
from pathlib import Path

from openai import OpenAI

try:  # .env не обязателен, но удобен
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

API_KEY = os.getenv("YANDEX_API_KEY")
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID")
BASE_URL = "https://ai.api.cloud.yandex.net/v1"
MODEL_NAME = os.getenv("YANDEX_MODEL", "yandexgpt/latest")  # можно aliceai-llm-flash и др.
SESSIONS_DIR = Path("sessions")

SYSTEM_PROMPT = (
    "Ты — полезный агент. Отвечай кратко и по делу. "
    "Если для ответа нужны данные из инструментов — вызывай их."
)

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


@tool("Прочитать текстовый файл из рабочей папки",
      {"type": "object",
       "properties": {"path": {"type": "string", "description": "Имя или путь файла"}},
       "required": ["path"]})
def read_file(path: str):
    root = Path.cwd().resolve()
    target = (root / path).resolve()
    if root not in target.parents:
        raise ValueError("Доступ только внутри рабочей папки")
    return target.read_text(encoding="utf-8")[:8000]


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


# ------------------- Агент -------------------

class Agent:
    def __init__(self, model: str, messages: list[dict]):
        if not API_KEY or not FOLDER_ID:
            raise SystemExit("Задай YANDEX_API_KEY и YANDEX_FOLDER_ID (переменные окружения или .env)")
        self.client = OpenAI(api_key=API_KEY, project=FOLDER_ID, base_url=BASE_URL)
        self.model = f"gpt://{FOLDER_ID}/{model}"
        self.messages = messages or [{"role": "system", "content": SYSTEM_PROMPT}]

    def respond(self, user_text: str) -> str:
        self.messages.append({"role": "user", "content": user_text})
        while True:  # цикл Function Calling: модель может запросить несколько функций подряд
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                tools=[e["schema"] for e in TOOLS.values()] or None,
                temperature=0.6,
                max_tokens=1000,
            )
            message = response.choices[0].message
            if message.tool_calls:
                self.messages.append({
                    "role": "assistant",
                    "content": message.content or "",
                    "tool_calls": [t.model_dump() for t in message.tool_calls],
                })
                self.messages.extend(run_tool_calls(message.tool_calls))
                continue
            self.messages.append({"role": "assistant", "content": message.content})
            return message.content


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
