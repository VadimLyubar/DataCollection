class StreamComparator:
    def __init__(self, list_reference: list, func_event_equals):
        self.reference = list_reference
        self.event_equals = func_event_equals
        self.comparators = []

    # Принимает один символ и вызывает событие полного совпадения слова из эталона, если это действительно произошло.
    def input(self, char):
        # блок сравнения последующих символов начиная со второго
        # перечисляем имеющиеся сравниватели в списке сравнивателей
        # перечисление по индексам в обратном порядке с возможностью удаления сравнивателя
        for i in range(len(self.comparators) - 1, -1, -1):
            # выгружаем в переменные рабочие данные из сравнивателя начиная с самого сравнивателя
            comparator = self.comparators[i]
            # выгружаем индекс текущего эталона в списке эталонов
            comparator_source_index = comparator[0]
            # выгружаем позицию символа для текущего эталона
            comparator_source_char_position = comparator[1]
            # получаем текущий эталон целоком, он нам понадобится трижды
            reference = self.reference[comparator_source_index]
            # получаем проверяемый символ эталона
            reference_char = reference[comparator_source_char_position]
            # сравниваем символ эталона с поступившим на вход без учёта регистра
            if reference_char.upper() == char.upper():
                # символы совпали - эталон пока проходит по совпадениям
                # вычисляем позицию следующего символа в эталоне
                index_next_char = comparator_source_char_position + 1
                # возможно это был последний символ эталона и тагда должно быть полное совпадение
                # проверяем это, берём длину эталона и сравниваем со следующей позицией символа
                if len(reference) == index_next_char:
                    # полное совпадение эталона - бросаем событие
                    self.event_equals(reference)
                    # удаляем сравниватель из плавающего списка сравнивателей
                    del self.comparators[i]
                else:
                    # вносим изменения в текущий сравниватель переключая символ на следующий
                    self.comparators[i] = (comparator_source_index, index_next_char)
            else:
                # символ на входе потока не совпал с символом эталона - сравниватель провальный - удаляем
                del self.comparators[i]

        # блок сравнения первых символов в эталонах
        # перечисляем каждый эталон из списка эталонов с учётом его индекса
        for index, source in enumerate(self.reference):
            # берём первый символ из текущего эталона
            source_first = source[0]
            # сравниваем этот символ с потоковым без учёта регистра
            if source_first.upper() == char.upper():
                # если символы совпали - возможно два варианта
                # 1. эталон состоит из одного символа
                # 2. эталон состоит из множества символов
                # по первому пункту проверяем что эталон односимвольный
                if len(source) == 1:
                    # тогда генерируем событие и цикл пускаем на следующую итерацию
                    self.event_equals(source)
                    continue
                # вариант второй - создаём сравниватель для дальнейшей обработки
                comparator = (index, 1)
                self.comparators.append(comparator)
