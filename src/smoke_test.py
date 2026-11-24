from app_state import AppState
from word_matcher import WordMatcher
from commands import CommandDispatcher
from constants import WORDS

state = AppState('data_test.csv')
state.load()
matcher = WordMatcher(WORDS)
disp = CommandDispatcher(state, matcher)

# Матчер: слово целиком, посимвольно
for ch in 'вперёд':
    disp.feed_char(ch)
assert state.status == 'Шаг вниз' or state.active_index == 1, state.status

# Цифры напрямую в ячейку
state.type_digit('4')
state.type_digit('5')
assert state.rows[state.active_index]['curr'].endswith('45')

# Спецзначение затем стирание
disp.handle_command('txt_na')
assert state.rows[state.active_index]['curr'] == 'недоступно'
disp.handle_command('backspace')
assert state.rows[state.active_index]['curr'] == ''

# Поиск с нормализацией
state.search('Б37Ж')
assert state.active_index >= 0
assert state.voice_stream == '' and not state.search_mode

# Сохранение атомарно и без .tmp-мусора
state.save()
import os
assert not os.path.exists('data_test.csv.tmp')
print('Смоук-тест пройден')
