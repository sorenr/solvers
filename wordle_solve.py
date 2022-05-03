#!/usr/bin/env python3

import numpy
import sys

WORDS = "/usr/share/dict/words"
WORD_LEN = 5


def char_to_int(c):
    return ord(c) - ord('a')


def int_to_char(i):
    return chr(i + ord('a'))


def word_to_list(word):
    return [char_to_int(c) for c in word.lower()]


def list_to_word(word):
    return "".join([int_to_char(i) for i in word])


def list_to_words(words):
    return [list_to_word(word) for word in words]


def get_words():
    words = []
    with open(WORDS) as fd:
        for line in fd.readlines():
            line = line.strip()
            if len(line) != WORD_LEN:
                continue
            words.append(word_to_list(line))
    return numpy.array(words)


def make_guess(words):
    guess = numpy.full(words.shape[1], 255)
    # letters [a ... z]
    letters = numpy.arange(26)
    # positions [0 ... 4]
    positions = numpy.arange(words.shape[1])

    counts = []

    # make counts for each letter...
    for row in words.transpose():
        # count letter frequency
        count = numpy.bincount(row)
        # pad the array to 26
        count = numpy.pad(count, (0, 26 - count.shape[0]), mode='constant', constant_values=0)
        counts.append(count)

    counts = numpy.array(counts)
    print("counts")
    print(counts)
    print()

    while True:
        print("#" * 80)
        print()

        # letter frequency in sorted order
        counts_sort = numpy.argsort(counts)[:, ::-1]
        print("counts_sort")
        print(counts_sort)
        print()

        counts_sorted = counts_sort.copy()
        for i, row in enumerate(counts_sort):
            row_sorted = counts[i][row]
            counts_sorted[i, :] = row_sorted
        print("counts_sorted")
        print(counts_sorted)
        print()

        # first column
        first = counts_sorted[:, 0].transpose()
        remainders = numpy.sum(counts_sorted[:, 1:], axis=1)
        discriminant = numpy.abs(first - remainders)
        print("discriminant")
        print(discriminant)
        print()

        # find the most valuable position
        discriminant_idx = numpy.argmin(discriminant)
        guess_idx = positions[discriminant_idx]
        letter_idx = counts_sort[discriminant_idx][0]
        guess_letter = letters[letter_idx]
        # pick the most valuable guess
        guess[guess_idx] = guess_letter

        if len(positions) <= 1:
            return guess

        counts = numpy.delete(counts, discriminant_idx, 0)
        counts = numpy.delete(counts, letter_idx, 1)
        print("counts")
        print(counts)
        print()

        positions = numpy.delete(positions, discriminant_idx, 0)
        print("positions")
        print(positions)
        print()

        letters = numpy.delete(letters, letter_idx, 0)
        print("letters")
        print(letters)
        print()

        print("guess")
        print(guess)
        print()


def filter_correct(words, ci, pos):
    column = words[:, pos]
    res = numpy.equal(column, ci)
    return words[res]


def filter_wrong_place(words, ci, pos):
    # the char is not in this column
    column = words[:, pos]
    sel = numpy.not_equal(column, ci)
    words = words[sel]
    # ...but it does appear in other columns
    searchme = numpy.delete(words, pos, 1)
    sel = numpy.any(numpy.equal(searchme, ci), axis=1)
    return words[sel]


def filter_incorrect(words, ci):
    res = numpy.all(numpy.not_equal(words, ci), axis=1)
    return words[res]


def filter_words(words, guess, result):
    for i, result in enumerate(result.lower()):
        ci = char_to_int(guess[i])
        if result == 'g':
            words = filter_correct(words, ci, i)
        elif result == 'y':
            words = filter_wrong_place(words, ci, i)
        elif result == 'b':
            words = filter_incorrect(words, ci)
        else:
            print("NOPE")
            sys.exit(-1)


def wordle():
    words = get_words()
    while True:
        print(words.shape[0])
        guess = make_guess(words)
        print(guess)
        result = input("{0} > ".format(list_to_word(guess)))
        words = filter_words(words, guess, result)


if __name__ == "__main__":
    wordle()
