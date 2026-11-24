#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Отрисовка интерфейса: таблица, стили, статусная строка с индикатором режима.

import curses

from constants import HEADER

STYLE_PAIRS = {'red': 1, 'yellow': 2, 'green': 3, 'white': 4}


class UI:
    def __init__(self, stdscr, state):
        self.stdscr = stdscr
        self.state = state
        self.screen_height, self.screen_width = stdscr.getmaxyx()
        self.pad = curses.newpad(len(state.rows) + 1, self.screen_width)
        curses.start_color()
        curses.noecho()
        curses.curs_set(0)
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)

    def redraw_interface(self):
        state = self.state
        self.pad.erase()
        header = f'{HEADER[0]:<12} | {HEADER[1]:<11} | {HEADER[2]}'
        try:
            self.pad.addstr(0, 0, header[:self.screen_width - 1],
                            curses.A_BOLD | curses.color_pair(4))
        except curses.error:
            pass
        for i, row in enumerate(state.rows):
            text = f" {row['id'].ljust(12)} | {row['prev'].ljust(11)} | {row['curr']}"
            attr = curses.color_pair(STYLE_PAIRS[state.diff_style(row)])
            if i == state.active_index:
                attr |= curses.A_REVERSE
            try:
                self.pad.addstr(i + 1, 0, text[:self.screen_width - 1], attr)
            except curses.error:
                pass
        view_height = max(1, self.screen_height - 1)
        offset = max(0, min(len(state.rows) + 1 - view_height,
                            state.active_index - view_height // 2))
        self.pad.refresh(offset, 0, 0, 0, view_height - 1, self.screen_width - 1)
        self._draw_status_bar()

    def _draw_status_bar(self):
        state = self.state
        if state.search_mode:
            mode = '[ПОИСК]'
        elif state.jump_mode:
            mode = '[ПЕРЕХОД]'
        else:
            mode = '[ВВОД]'
        line = mode + ' ' + state.status
        try:
            self.stdscr.move(self.screen_height - 1, 0)
            self.stdscr.clrtoeol()
            self.stdscr.addstr(self.screen_height - 1, 0,
                               line[:self.screen_width - 1], curses.color_pair(4))
            self.stdscr.refresh()
        except curses.error:
            pass
