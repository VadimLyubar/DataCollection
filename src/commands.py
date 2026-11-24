#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Диспетчер команд: обработка событий и навигация.

from word_matcher import WordMatcher
from constants import WORDS


class CommandDispatcher:
    def __init__(self, state, matcher):
        self.state = state
        self.matcher = matcher

    def handle_command(self, command, text=None):
        cmd = command.lower()
        
        if cmd == 'exit':
            return False  # флаг продолжения работы
        elif cmd == 'back':
            self.state.active_index = max(0, self.state.active_index - 1)
        elif cmd == 'next':
            self.state.active_index = min(len(self.state.rows) - 1, self.state.active_index + 1)
        elif cmd == 'to_top':
            self.state.active_index = 0
        elif cmd == 'to_bottom':
            self.state.active_index = len(self.state.rows) - 1
        elif cmd == 'clear':
            self.state.clear_current()
        elif cmd == 'backspace':
            self.state.backspace_current()
        elif cmd.startswith('digit_'):
            digit = cmd.split('_')[1]
            self.state.type_digit(digit)
        elif cmd == 'prepare_jump':
            self.state.jump_mode = True
            self.state.search_mode = False
            self.state.jump_buffer = ''
            self.state.status = '[РЕЖИМ ПЕРЕХОДА]: Ожидание числа строк...'
        elif cmd == 'move_up_n':
            steps = int(self.state.jump_buffer) if self.state.jump_buffer else 1
            self.state.active_index = max(0, self.state.active_index - steps)
            self.state.jump_mode = False
            self.state.jump_buffer = ''
        elif cmd == 'move_down_n':
            steps = int(self.state.jump_buffer) if self.state.jump_buffer else 1
            self.state.active_index = min(len(self.state.rows) - 1, self.state.active_index + steps)
            self.state.jump_mode = False
            self.state.jump_buffer = ''
        elif cmd == 'prepare_search':
            self.state.search_mode = True
            self.state.jump_mode = False
            self.state.voice_stream = ''
            self.state.status = '[ПОИСК]: Ожидание ввода текста...'
        elif cmd == 'execute_search':
            self.state.search(self.state.voice_stream)
        elif cmd in ('txt_na', 'txt_off'):
            text_map = {'txt_na': 'недоступно', 'txt_off': 'отключено'}
            self.state.set_special(text_map[cmd])
        else:
            # Неизвестная команда — ничего не делаем
            pass
        return True

    def feed_char(self, char):
        matched_words = self.matcher.feed(char)
        for word in matched_words:
            cmd = word.get('command')
            txt = word.get('text')
            if cmd:
                return self.handle_command(cmd, txt)
        return True
