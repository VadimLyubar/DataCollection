#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Константы и словари команд.

SPECIALS = ('недоступно', 'отключено')
HEADER = ['Идентификатор', 'Предыдущие', 'Текущие']

WORDS = [
    {'type': 'command', 'text': 'выход', 'command': 'exit'},
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
    {'type': 'command', 'text': 'найти', 'command': 'execute_search'},
]

NUM_WORDS_MAP = {
    'ноль': '0', 'один': '1', 'два': '2', 'три': '3', 'четыре': '4',
    'пять': '5', 'шесть': '6', 'семь': '7', 'восемь': '8', 'девять': '9',
}

for _nw, _dig in NUM_WORDS_MAP.items():
    WORDS.append({'type': 'command', 'text': _nw, 'command': 'digit_' + _dig})
