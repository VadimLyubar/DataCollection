import curses
import csv
import os
import re

INPUT_FILE = "data.csv"
curses_no_exit = True
std_screen = None
pad = None
pad_height = 0
pad_width = 0
screen_height = 0
screen_width = 0

words = [
    {'type': 'command', 'text': 'выход', 'command': 'exit'},
    {'type': 'command', 'text': 'сохранить', 'command': 'save'},
    {'type': 'command', 'text': 'назад', 'command': 'back'},
    {'type': 'command', 'text': 'вперёд', 'command': 'next'},
    {'type': 'command', 'text': 'вперед', 'command': 'next'},
    {'type': 'command', 'text': 'дальше', 'command': 'next'},
    {'type': 'command', 'text': 'далее', 'command': 'next'},
    {'type': 'command', 'text': 'исправить', 'command': 'clear'},
    {'type': 'command', 'text': 'очистить', 'command': 'clear'},
    {'type': 'command', 'text': 'стереть', 'command': 'backspace'},
    {'type': 'command', 'text': 'недоступно', 'command': 'txt_na'},
    {'type': 'command', 'text': 'отключено', 'command': 'txt_off'},
    {'type': 'command', 'text': 'начало', 'command': 'to_top'},
    {'type': 'command', 'text': 'конец', 'command': 'to_bottom'},
    {'type': 'command', 'text': 'выше', 'command': 'move_up_n'},
    {'type': 'command', 'text': 'ниже', 'command': 'move_down_n'},
    {'type': 'command', 'text': 'перейти на', 'command': 'prepare_jump'},
    {'type': 'command', 'text': 'переход на', 'command': 'prepare_jump'},
    {'type': 'command', 'text': 'перейти', 'command': 'prepare_jump'},
    {'type': 'command', 'text': 'переход', 'command': 'prepare_jump'},
    {'type': 'command', 'text': 'поиск', 'command': 'prepare_search'},
    {'type': 'command', 'text': 'искать', 'command': 'execute_search'},
    {'type': 'command', 'text': 'найти', 'command': 'execute_search'}
]

num_words_map = {
    'ноль': '0', 'один': '1', 'два': '2', 'три': '3', 'четыре': '4',
    'пять': '5', 'шесть': '6', 'семь': '7', 'восемь': '8', 'девять': '9'
}

for nw, dig in num_words_map.items():
    words.append({'type': 'command', 'text': nw, 'command': f'digit_{dig}'})

comparators = []
table_data = []
active_index = 0
current_row = 0
status_message = "Ожидание ввода..."
jump_buffer = ""
raw_voice_stream = ""
is_jump_mode = False
is_search_mode = False
ignore_current_char_in_search = False


def load_csv_data():
    global table_data
    table_data = []
    if not os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Идентификатор", "Предыдущие", "Текущие"])
            writer.writerow(["Б37У 15", "4520", ""])
            writer.writerow(["Б37Ж 9Д", "12350", ""])
            writer.writerow(["Б37Ж 9Н", "недоступно", ""])
            writer.writerow(["О37Л ОС", "8900", ""])
    try:
        with open(INPUT_FILE, "r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter=";")
            next(reader, None)
            for row in reader:
                if len(row) >= 2:
                    id_val = str(row.__getitem__(0)).strip()
                    prev_val = str(row.__getitem__(1)).strip()
                    curr_val = str(row.__getitem__(2)).strip() if len(row) > 2 else ""
                    table_data.append({"id": id_val, "prev": prev_val, "curr": curr_val})
    except Exception as e:
        global status_message
        status_message = f"Ошибка загрузки CSV: {str(e)}"


def save_csv_data():
    try:
        with open(INPUT_FILE, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Идентификатор", "Предыдущие", "Текущие"])
            for row in table_data:
                writer.writerow([row["id"], row["prev"], row["curr"]])
    except Exception:
        pass


def get_validation_style(prev_str, curr_str, is_active):
    base_bg = curses.A_REVERSE if is_active else curses.A_NORMAL
    if not curr_str:
        return base_bg | curses.A_BOLD if is_active else curses.A_NORMAL
    specials = ["недоступно", "отключено"]
    if curr_str in specials or prev_str in specials:
        return base_bg | curses.color_pair(4)
    try:
        prev_num = int(prev_str)
        curr_num = int(curr_str)
        diff = curr_num - prev_num
        if curr_num < prev_num or diff > 1000:
            return base_bg | curses.color_pair(1)
        elif 500 <= diff <= 1000:
            return base_bg | curses.color_pair(2)
        elif 0 <= diff < 500:
            return base_bg | curses.color_pair(3)
    except ValueError:
        pass
    return base_bg


def redraw_interface():
    global active_index, current_row, screen_height, screen_width, status_message
    if pad is None or std_screen is None: return
    try:
        pad.erase()
        for i, row in enumerate(table_data):
            text = f" {row['id'].ljust(12)} | Пред: {row['prev'].ljust(11)} | Тек: {row['curr']}"
            text = text.ljust(pad_width - 1)[:pad_width - 1]
            style = get_validation_style(row['prev'], row['curr'], i == active_index)
            pad.addstr(i, 0, text, style)
        view_height = screen_height - 1
        pad.refresh(current_row, 0, 0, 0, view_height - 1, screen_width - 1)
        std_screen.move(screen_height - 1, 0)
        std_screen.clrtoeol()
        clean_status = status_message.ljust(screen_width - 1)[:screen_width - 1]
        std_screen.addstr(screen_height - 1, 0, clean_status, curses.color_pair(4))
        std_screen.refresh()
    except curses.error:
        pass


def move_focus(direction, steps=1):
    global active_index, current_row, screen_height
    view_height = screen_height - 1
    mid_point = view_height // 2
    for _ in range(steps):
        if direction == 1 and active_index < len(table_data) - 1:
            active_index += 1
            if (active_index - current_row) > mid_point:
                current_row = min(max(0, len(table_data) - view_height), current_row + 1)
        elif direction == -1 and active_index > 0:
            active_index -= 1
            if (active_index - current_row) < mid_point:
                current_row = max(0, current_row - 1)


def jump_focus(position):
    global active_index, current_row, screen_height
    view_height = screen_height - 1
    if position == "top":
        active_index = 0
        current_row = 0
    elif position == "bottom":
        active_index = len(table_data) - 1
        current_row = max(0, len(table_data) - view_height)


def build_search_query(stream_text, is_final=False):
    full_text = stream_text.upper()
    parts = full_text.split("ПОИСК")
    query_raw = parts[-1] if len(parts) > 0 else full_text

    tokens = re.findall(r'[А-ЯЁA-Z]+|\d+', query_raw)
    result_parts = []
    stop_words = {"ПОИСК", "ИСКАТЬ", "НАЙТИ"}

    for idx, token in enumerate(tokens):
        if token in stop_words:
            continue
        if not is_final and idx == len(tokens) - 1 and not stream_text.endswith(" "):
            if len(token) >= 2 and ("ИСКАТЬ".startswith(token) or "НАЙТИ".startswith(token)):
                continue
        if token.isdigit():
            result_parts.append(token)
        elif token.lower() in num_words_map:
            result_parts.append(num_words_map[token.lower()])
        else:
            result_parts.append(token[0])

    return "".join(result_parts)


def perform_search_action():
    global raw_voice_stream, is_search_mode, active_index, current_row, screen_height, status_message
    query = build_search_query(raw_voice_stream, is_final=True)

    found = False
    if query:
        current_query = query
        while len(current_query) > 0:
            for i, row in enumerate(table_data):
                clean_id = row["id"].replace(" ", "").upper()
                if current_query in clean_id:
                    active_index = i
                    view_height = screen_height - 1
                    current_row = max(0, min(len(table_data) - view_height, i - (view_height // 2)))
                    status_message = f"Найдено близкое ({current_query}): {row['id']}"
                    found = True
                    break
            if found: break
            current_query = current_query[:-1]
    if not found:
        status_message = f"Не найдено совпадений для: {query}"
    raw_voice_stream = ""
    is_search_mode = False


def perform_jump_action(direction):
    global jump_buffer, is_jump_mode, status_message, screen_height
    if jump_buffer:
        try:
            steps = int(jump_buffer)
            move_focus(direction, steps)
            status_message = f"Прыжок на {steps} строк"
        except ValueError:
            status_message = "Ошибка: неверный числовой формат"
    else:
        view_height = screen_height - 1
        move_focus(direction, view_height)
        status_message = "Прокрутка экрана целиком"
    jump_buffer = ""
    is_jump_mode = False


def stream_comparator_event_word_equals(word):
    global status_message, is_jump_mode, is_search_mode, jump_buffer, raw_voice_stream
    if word['command'] == 'exit':
        global curses_no_exit
        save_csv_data()
        curses_no_exit = False
    elif word['command'] == 'save':
        save_csv_data()
        status_message = "Данные сохранены в data.csv"
    elif word['command'] == 'prepare_jump':
        is_jump_mode = True
        is_search_mode = False
        jump_buffer = ""
        status_message = "[РЕЖИМ ПЕРЕХОДА]: Ожидание числа строк..."
    elif word['command'] == 'prepare_search':
        global ignore_current_char_in_search
        is_search_mode = True
        is_jump_mode = False
        ignore_current_char_in_search = True
        raw_voice_stream = ""
        status_message = "[ПОИСК]: Ожидание ввода текста..."
    elif word['command'] == 'execute_search':
        perform_search_action()
    elif word['command'] == 'move_up_n':
        perform_jump_action(-1)
    elif word['command'] == 'move_down_n':
        perform_jump_action(1)
    elif word['command'] == 'next':
        move_focus(1)
        status_message = "Шаг вниз"
    elif word['command'] == 'back':
        move_focus(-1)
        status_message = "Шаг вверх"
    elif word['command'] == 'clear':
        table_data[active_index]["curr"] = ""
        status_message = "Значение строки очищено полностью"
    elif word['command'] == 'backspace':
        curr_val = str(table_data[active_index]["curr"])
        if curr_val and curr_val not in ["недоступно", "отключено"]:
            table_data[active_index]["curr"] = curr_val[:-1]
        else:
            table_data[active_index]["curr"] = ""
        status_message = "Удалён последний символ ячейки"
    elif word['command'] in ['txt_na', 'txt_off']:
        if not is_search_mode:
            table_data[active_index]["curr"] = word['text']
            status_message = f"Статус: {word['text']}"
    elif word['command'] == 'to_top':
        jump_focus("top")
        status_message = "Переход в начало списка"
    elif word['command'] == 'to_bottom':
        jump_focus("bottom")
        status_message = "Переход в конец списка"
    elif word['command'].startswith('digit_'):
        digit = word['command'].split('_')[-1]
        handle_digit_input(digit)


def handle_digit_input(digit):
    global is_jump_mode, is_search_mode, jump_buffer, raw_voice_stream, status_message
    if is_jump_mode:
        jump_buffer += digit
        status_message = f"[РЕЖИМ ПЕРЕХОДА]: Число строк -> {jump_buffer}"
    elif is_search_mode:
        for word_num, dig in num_words_map.items():
            if dig == digit and raw_voice_stream.lower().endswith(word_num):
                raw_voice_stream = raw_voice_stream[:-len(word_num)]
                break
        raw_voice_stream += f" {digit} "
        display_query = build_search_query(raw_voice_stream)
        status_message = f"[ПОИСК]: Идентификатор -> {display_query}"
    else:
        if table_data[active_index]["curr"] in ["недоступно", "отключено"]:
            table_data[active_index]["curr"] = ""
        table_data[active_index]["curr"] += digit
        status_message = f"Ввод числа: {table_data[active_index]['curr']}"


def stream_comparator_input(input_char):
    global words, comparators
    for index in range(len(comparators) - 1, -1, -1):
        comparator = comparators[index]
        index_word, position = comparator
        word = words[index_word]
        text = word['text']
        char = text[position]
        if input_char.upper() == char.upper():
            next_char_position = position + 1
            if next_char_position == len(text):
                del comparators[index]
                stream_comparator_event_word_equals(word)
            else:
                comparators[index] = (index_word, next_char_position)
        else:
            del comparators[index]
    for index_word, word in enumerate(words):
        text = word['text']
        char = text[0]
        if input_char.upper() == char.upper():
            if len(text) == 1:
                stream_comparator_event_word_equals(word)
                continue
            comparator = (index_word, 1)
            comparators.append(comparator)


def input_char_performer(char):
    global is_search_mode, raw_voice_stream, status_message, ignore_current_char_in_search
    if char == 'q':
        save_csv_data()
        global curses_no_exit
        curses_no_exit = False
        return
    stream_comparator_input(char)
    if ignore_current_char_in_search:
        ignore_current_char_in_search = False
        redraw_interface()
        return
    if '0' <= char <= '9':
        handle_digit_input(char)
    elif is_search_mode:
        if char.isalpha():
            if raw_voice_stream and raw_voice_stream[-1].islower() and char.isupper():
                raw_voice_stream += " "
            raw_voice_stream += char
        else:
            if not raw_voice_stream.endswith(" "):
                raw_voice_stream += " "
        display_query = build_search_query(raw_voice_stream)
        if display_query:
            status_message = f"[ПОИСК]: Идентификатор -> {display_query}"
        else:
            status_message = "[ПОИСК]: Ожидание ввода текста..."
    redraw_interface()


def main_curses_wrapper_performer(stdscr):
    global curses_no_exit, std_screen, screen_height, screen_width, pad, pad_height, pad_width
    std_screen = stdscr
    last_key_char = 0
    curses.start_color()
    curses.noecho()
    curses.curs_set(0)
    curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.cbreak()
    stdscr.keypad(True)
    load_csv_data()
    screen_height, screen_width = stdscr.getmaxyx()
    pad_height = len(table_data) + 2
    pad_width = screen_width
    pad = curses.newpad(pad_height, pad_width)

    stdscr.refresh()
    redraw_interface()

    while curses_no_exit:
        key_char = stdscr.getch()
        if key_char == 208 or key_char == 209:
            last_key_char = key_char
            continue
        result_char = chr(key_char)
        if last_key_char == 208: result_char = chr(key_char + 896)
        if last_key_char == 209: result_char = chr(key_char + 960)
        last_key_char = 0
        input_char_performer(result_char)


def main():
    curses.wrapper(main_curses_wrapper_performer)


if __name__ == '__main__':
    main()
