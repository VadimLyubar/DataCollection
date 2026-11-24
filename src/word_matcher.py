#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Посимвольный матчер командных слов.


class WordMatcher:
    def __init__(self, words):
        self.words = words
        self.active = []

    def reset(self):
        self.active = []

    def feed(self, char):
        matched = []
        for i in range(len(self.active) - 1, -1, -1):
            index_word, position = self.active[i]
            text = self.words[index_word]['text']
            if char.upper() == text[position].upper():
                if position + 1 == len(text):
                    del self.active[i]
                    matched.append(self.words[index_word])
                else:
                    self.active[i] = (index_word, position + 1)
            else:
                del self.active[i]
        for index_word, word in enumerate(self.words):
            if char.upper() == word['text'][0].upper():
                if len(word['text']) == 1:
                    if word not in matched:
                        matched.append(word)
                    continue
                self.active.append((index_word, 1))
        return matched
