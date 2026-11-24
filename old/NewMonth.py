#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NewMonth.py — перенос значений из третьей колонки во вторую.

Использование: python NewMonth.py data.csv data2.csv
Значения колонки 3 записываются в колонку 2, колонка 3 становится пустой.
Заголовок сохраняется без изменений. Старые значения колонки 2 теряются.
"""

import csv
import sys


def main():
    if len(sys.argv) != 3:
        print("Использование: python NewMonth.py <входной.csv> <выходной.csv>")
        sys.exit(1)

    in_path, out_path = sys.argv[1], sys.argv[2]

    try:
        with open(in_path, "r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.reader(f, delimiter=";"))
    except FileNotFoundError:
        print("Файл не найден:", in_path)
        sys.exit(1)

    if not rows:
        print("Файл пуст:", in_path)
        sys.exit(1)

    # Заголовок не трогаем, обрабатываем только строки данных
    for row in rows[1:]:
        while len(row) < 3:
            row.append("")
        row[1] = row[2]
        row[2] = ""

    try:
        with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
            csv.writer(f, delimiter=";").writerows(rows)
    except OSError as e:
        print("Ошибка записи:", e)
        sys.exit(1)

    print("Готово:", in_path, "->", out_path)


if __name__ == "__main__":
    main()
