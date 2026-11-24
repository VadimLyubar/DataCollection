#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Модель данных: загрузка и сохранение CSV, состояние редактора.

import csv
import os

from constants import HEADER, SPECIALS


class AppState:
    def __init__(self, path):
        self.path = path
        self.rows = []
        self.active_index = 0
        self.status = 'Ожидание ввода...'
        self.jump_buffer = ''
        self.voice_stream = ''
        self.jump_mode = False
        self.search_mode = False

    def load(self):
        self.rows = []
        if not os.path.exists(self.path):
            self._create_demo()
            self.status = 'Создан новый файл с демо-данными'
        try:
            with open(self.path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.reader(f, delimiter=';')
                next(reader, None)
                for row in reader:
                    if len(row) < 2:
                        continue
                    self.rows.append({
                        'id': row[0].strip(),
                        'prev': row[1].strip(),
                        'curr': row[2].strip() if len(row) > 2 else '',
                    })
            self.active_index = 0
        except Exception as e:
            self.status = 'Ошибка загрузки CSV: ' + str(e)

    def _create_demo(self):
        demo = [
            ['Б37У 15', '4520', ''],
            ['Б37Ж 9Д', '12350', ''],
            ['Б37Ж 9Н', 'недоступно', ''],
            ['О37Л ОС', '8900', ''],
        ]
        with open(self.path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(HEADER)
            writer.writerows(demo)

    def save(self):
        tmp = self.path + '.tmp'
        with open(tmp, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(HEADER)
            for row in self.rows:
                writer.writerow([row['id'], row['prev'], row['curr']])
        os.replace(tmp, self.path)

    def clear_current(self):
        self.rows[self.active_index]['curr'] = ''
        self.status = 'Значение строки очищено полностью'

    def backspace_current(self):
        curr = self.rows[self.active_index]['curr']
        if curr and curr not in SPECIALS:
            self.rows[self.active_index]['curr'] = curr[:-1]
        else:
            self.rows[self.active_index]['curr'] = ''
        self.status = 'Удалён последний символ ячейки'

    def set_special(self, text):
        self.rows[self.active_index]['curr'] = text
        self.status = 'Статус: ' + text

    def type_digit(self, digit):
        if self.jump_mode:
            self.jump_buffer += digit
            self.status = '[РЕЖИМ ПЕРЕХОДА]: Число строк -> ' + self.jump_buffer
            return
        if self.search_mode:
            self.type_search_char(digit)
            return
        row = self.rows[self.active_index]
        if row['curr'] in SPECIALS:
            row['curr'] = ''
        row['curr'] += digit
        self.status = 'Ввод числа: ' + row['curr']

    def type_search_char(self, char):
        self.voice_stream += char
        self.status = '[ПОИСК]: Идентификатор -> ' + self.voice_stream.strip()

    def normalize_query(self, raw):
        query = raw.upper().replace('ИСКАТЬ', '').replace('НАЙТИ', '')
        query = query.replace(' ', '').strip()
        if len(query) > 2 and query[0] in ('К', 'Х', 'Т'):
            if not query[1].isdigit():
                query = query[1:]
        return query

    def search(self, raw):
        query = self.normalize_query(raw)
        found = False
        current = query
        while current:
            for i, row in enumerate(self.rows):
                clean_id = row['id'].replace(' ', '').upper()
                if current in clean_id:
                    self.active_index = i
                    self.status = 'Найдено близкое (' + current + '): ' + row['id']
                    found = True
                    break
            if found:
                break
            current = current[:-1]
        if not found:
            self.status = 'Не найдено совпадений для: ' + query
        self.voice_stream = ''
        self.search_mode = False
        return found

    def diff_style(self, row):
        curr = row['curr']
        prev = row['prev']
        if curr in SPECIALS:
            return 'red'
        if not curr:
            return 'white'
        try:
            curr_val = float(curr.replace(',', '.'))
        except ValueError:
            return 'yellow'
        try:
            prev_val = float(prev.replace(',', '.')) if prev else 0.0
        except ValueError:
            return 'yellow'
        return 'green' if curr_val != prev_val else 'yellow'
