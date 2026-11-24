# -*- coding: utf-8 -*-
# Юнит-тесты. Запуск из папки src: python -m pytest test_app.py -v

import os

from app_state import AppState
from word_matcher import WordMatcher
from commands import CommandDispatcher
from constants import WORDS

CSV_SAMPLE = (
    'Идентификатор;Предыдущие;Текущие\n'
    'Б37У 15;4520;\n'
    'Б37Ж 9Д;12350;\n'
    'Б37Ж 9Н;недоступно;\n'
    'О37Л ОС;8900;\n'
)


def make_state(tmp_path):
    path = tmp_path / 'data.csv'
    path.write_text(CSV_SAMPLE, encoding='utf-8')
    state = AppState(str(path))
    state.load()
    return state


def make_dispatcher(state):
    return CommandDispatcher(state, WordMatcher(WORDS))


def test_load_rows(tmp_path):
    state = make_state(tmp_path)
    assert len(state.rows) == 4
    assert state.rows[0]['id'] == 'Б37У 15'
    assert state.rows[2]['curr'] == 'недоступно'


def test_matcher_full_word_moves_down(tmp_path):
    state = make_state(tmp_path)
    disp = make_dispatcher(state)
    for ch in 'вперёд':
        disp.feed_char(ch)
    assert state.active_index == 1


def test_matcher_prefix_does_not_fire(tmp_path):
    state = make_state(tmp_path)
    matcher = WordMatcher(WORDS)
    matcher.feed('в')
    matcher.feed('ы')
    # Слово не завершено — команда не выполнилась
    assert state.active_index == 0


def test_digit_input_and_backspace(tmp_path):
    state = make_state(tmp_path)
    state.type_digit('1')
    state.type_digit('2')
    assert state.rows[0]['curr'] == '4520' + '12'
    state.backspace_current()
    assert state.rows[0]['curr'] == '45201'


def test_backspace_clears_special(tmp_path):
    state = make_state(tmp_path)
    state.active_index = 2
    state.backspace_current()
    assert state.rows[2]['curr'] == ''


def test_clear_current(tmp_path):
    state = make_state(tmp_path)
    state.clear_current()
    assert state.rows[0]['curr'] == ''


def test_search_finds_by_fragment(tmp_path):
    state = make_state(tmp_path)
    state.search_mode = True
    state.voice_stream = 'искать б37ж 9'
    assert state.search(state.voice_stream)
    assert state.rows[state.active_index]['id'].startswith('Б37Ж')
    assert state.voice_stream == ''
    assert not state.search_mode


def test_search_not_found(tmp_path):
    state = make_state(tmp_path)
    assert not state.search('ХХХ999')
    assert 'Не найдено' in state.status


def test_normalize_query_strips_leading_letter(tmp_path):
    state = make_state(tmp_path)
    assert state.normalize_query('кам') == 'АМ'
    assert state.normalize_query('к9д') == 'К9Д'
    assert state.normalize_query('искать Б37') == 'Б37'


def test_diff_style(tmp_path):
    state = make_state(tmp_path)
    assert state.diff_style({'prev': '12350', 'curr': 'недоступно'}) == 'red'
    assert state.diff_style({'prev': '12350', 'curr': ''}) == 'white'
    assert state.diff_style({'prev': '12350', 'curr': '12400'}) == 'green'
    assert state.diff_style({'prev': '12350', 'curr': '12350'}) == 'yellow'
    assert state.diff_style({'prev': '', 'curr': 'abc'}) == 'yellow'


def test_save_atomic_no_tmp_left(tmp_path):
    state = make_state(tmp_path)
    state.save()
    assert not os.path.exists(str(tmp_path / 'data.csv.tmp'))


def test_dispatcher_exit_stops(tmp_path):
    state = make_state(tmp_path)
    disp = make_dispatcher(state)
    assert disp.handle_command('exit') is False
    assert disp.handle_command('next') is True


def test_jump_mode_buffer(tmp_path):
    state = make_state(tmp_path)
    disp = make_dispatcher(state)
    disp.handle_command('prepare_jump')
    assert state.jump_mode
    state.type_digit('2')
    assert state.jump_buffer == '2'
    disp.handle_command('move_down_n')
    assert state.active_index == 2
    assert not state.jump_mode
    assert state.jump_buffer == ''
