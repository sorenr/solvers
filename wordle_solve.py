#!/usr/bin/env python3

import numpy
import multiprocessing
import sys
import platform
import argparse
import time

WORDS = "wordle_words.txt"
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
    rv = numpy.array(words)
    print("Loaded {0} {1}-letter words".format(rv.shape[0], rv.shape[1]))
    return rv


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
        ci = guess[i]
        if result == 'g':
            words = filter_correct(words, ci, i)
        elif result == 'y':
            words = filter_wrong_place(words, ci, i)
        elif result == 'b':
            words = filter_incorrect(words, ci)
        else:
            print("NOPE")
            sys.exit(-1)
        if 0 == words.shape[0]:
            return words
    return words


def gen_result(answer, guess):
    rv = []
    for ac, gc in zip(answer, guess):
        if ac == gc:
            rv.append('g')
        elif gc in answer:
            rv.append('y')
        else:
            rv.append('b')
    return "".join(rv)


class GuessFinder:
    def __init__(self, guesses):
        self.guesses = guesses  # available guesses (all valid words)

    def guess_power(self, guess_i):
        rv = 0
        guess = self.guesses[guess_i]
        for possibility_i in range(self.possibilities.shape[0]):
            result = gen_result(self.possibilities[possibility_i], guess)
            possibilities_other = numpy.delete(self.possibilities, possibility_i, 0)
            possibilities_remain = filter_words(possibilities_other, guess, result)
            rv += possibilities_remain.shape[0]
        return (guess_i, rv)

    def promote_guess(self, guess_i, result):
        if self.min_rank is None or (result > 0 and self.min_rank > result):
            self.min_guesses_i = [guess_i]
            self.min_rank = result
        elif self.min_rank == result:
            self.min_guesses_i.append(guess_i)
        min_words = [list_to_word(self.guesses[i]) for i in self.min_guesses_i]
        min_words = " ".join(min_words)
        cur_word = list_to_word(self.guesses[guess_i])
        print("{} {} {:,} < {} {:,}".format(self.possibilities.shape[0], min_words, self.min_rank, cur_word, result))

    def best_guess(self, possibilities, threads=None):
        """Pick the best guess (from self.guesses) given the possible words."""
        self.possibilities = possibilities
        self.min_guesses_i = []
        self.min_rank = None
        # for each guess...
        guesses_i_it = range(self.guesses.shape[0])
        if threads == 1:
            for guess_i in guesses_i_it:
                guess_i, result = self.guess_power(guess_i)
                self.promote_guess(guess_i, result)
        else:
            # Windows can't use more than 64 handles
            if "Windows" == platform.system():
                threads = min(61, threads)
            print("Starting", threads, "threads.")
            with multiprocessing.Pool(threads) as pool:
                for p in pool.imap_unordered(self.guess_power, guesses_i_it):
                    guess_i, result = p
                    self.promote_guess(guess_i, result)
        del self.possibilities
        return self.guesses[self.min_guesses_i[0]]


def wordle(threads=multiprocessing.cpu_count(), first_principles=False):
    possibilities = get_words()
    assert(possibilities.shape[0])
    guess_finder = GuessFinder(possibilities)
    if first_principles:
        guess = None
    else:
        guess = word_to_list("lares")
    while True:
        if guess is not None:
            print(list_to_word(guess))
            result = input("> ")
            possibilities = filter_words(possibilities, guess, result)
            print(list_to_words(possibilities))
        print(possibilities.shape[0], "possibilities")
        if 1 == possibilities.shape[0]:
            return list_to_word(possibilities[0])
        input("press return to continue")
        t = time.time()
        guess = guess_finder.best_guess(possibilities, threads=threads)
        print(time.time() - t, "seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compute the next optimal Wordle guess.')
    parser.add_argument('-t', dest='threads', type=int, nargs=1,
                        metavar='THREADS', default=[multiprocessing.cpu_count()],
                        help='threads')
    parser.add_argument('--first-principles', dest="first_principles",
                        action="store_true", help="Recompute the first guess from scratch.")
    args = parser.parse_args()
    wordle(args.threads[0], args.first_principles)
