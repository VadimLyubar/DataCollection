#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Точка входа: сборка приложения и запуск curses.

import curses
import os
import sys

from app_state import AppState
from word_matcher import WordMatcher
from constants import WORDS
from commands import CommandDispatcher
from ui import UI


def resolve_input_file():
    if len(sys.argv) > 1:
        return sys.argv[1]
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(base), 'data.csv')


def main_curses_wrapper(stdscr):
    state = AppState(resolve_input_file())
    state.load()
    matcher = WordMatcher(WORDS)
    dispatcher = CommandDispatcher(state, matcher)
    ui = UI(stdscr, state)
    ui.redraw_interface()

    while True:
        ch = stdscr.get_wch()
        if not isinstance(ch, str):
            continue
        if ch == 'q':
            state.save()
            break
        # Матчер получает ВСЕ символы, как в старой версии:
        # только так слова 'искать' и 'выше' срабатывают внутри режимов.
        keep_running = dispatcher.feed_char(ch)
        if not keep_running:
            state.save()
            break
        if ch.isdigit():
            state.type_digit(ch)
        elif state.search_mode and (ch.isalpha() or ch == ' '):
            state.type_search_char(ch)
        ui.redraw_interface()


def main():
    curses.wrapper(main_curses_wrapper)


if __name__ == '__main__':
    main()
