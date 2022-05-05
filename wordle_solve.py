#!/usr/bin/env python3

import numpy
import multiprocessing
import sys
import platform
import argparse
import time

GUESSES = "wordle_guesses.txt"
SOLUTIONS = "wordle_solutions.txt"
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


def get_words(word_path):
    words = []
    with open(word_path) as fd:
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


def filter_solutions(solutions, guess, result):
    for i, result in enumerate(result.lower()):
        ci = guess[i]
        if result == 'g':
            solutions = filter_correct(solutions, ci, i)
        elif result == 'y':
            solutions = filter_wrong_place(solutions, ci, i)
        elif result == 'b':
            solutions = filter_incorrect(solutions, ci)
        else:
            assert(False)
        if 0 == solutions.shape[0]:
            break
    return solutions


def gen_clue(answer, guess):
    """Generate the clue for a given answer."""
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
    def __init__(self, guesses=GUESSES, solutions=SOLUTIONS):
        self.reset(guesses, solutions)

    def reset(self, guesses=GUESSES, solutions=SOLUTIONS):
        """Reset the state of the GuessFinder for another game."""
        self._guesses = get_words(guesses)
        self._solutions = get_words(solutions)

    def num_solutions(self):
        """Number of solutions we're currently considering."""
        return self._solutions.shape[0]

    def num_guesses(self):
        """Number of guesses available."""
        return self._guesses.shape[0]

    def solutions(self):
        return list_to_words(self._solutions)

    def filter_solutions(self, guess, result):
        self._solutions = filter_solutions(self._solutions, guess, result)
        return self._solutions

    def guess_power(self, guess):
        """Evaluate the 'power' of a specific guess. Smaller is better."""
        rv = 0
        for answer_i in range(self._solutions.shape[0]):
            clue = gen_clue(self._solutions[answer_i], guess)
            solutions_remain = filter_solutions(self._solutions, guess, clue)
            rv += solutions_remain.shape[0]
        return rv

    def guess_power_i(self, guess_i):
        return (guess_i, self.guess_power(self._guesses[guess_i]))

    def min_guess(self, guess_i, result):
        """Maintain a list of the minimum (best) guesses."""
        if self._min_rank is None or (result > 0 and self._min_rank > result):
            self._min_guesses_i = [guess_i]
            self._min_rank = result
        elif self._min_rank == result:
            self._min_guesses_i.append(guess_i)
        min_words = [list_to_word(self._guesses[i]) for i in self._min_guesses_i]
        min_words = " ".join(min_words)
        cur_word = list_to_word(self._guesses[guess_i])
        ns = self._solutions.shape[0]
        print("{} {:0.1f} < {} {:0.1f}".format(min_words, self._min_rank / ns,
                                               cur_word, result / ns))

    def best_guess(self, threads: int):
        """Pick the best guess (from self._guesses) given the possible words."""
        self._min_guesses_i = []
        self._min_rank = None
        # for each guess...
        guesses_i_it = range(self._guesses.shape[0])
        if threads == 1:
            for guess_i in guesses_i_it:
                result = self.guess_power(self._guesses[guess_i])
                self.min_guess(guess_i, result)
        else:
            # Windows can't use more than 64 handles
            if "Windows" == platform.system():
                threads = min(61, threads)
            print("Starting", threads, "threads.")
            with multiprocessing.Pool(threads) as pool:
                for p in pool.imap_unordered(self.guess_power_i, guesses_i_it):
                    guess_i, result = p
                    self.min_guess(guess_i, result)
        return self._guesses[self._min_guesses_i[0]]


def wordle(args):
    guess_finder = GuessFinder(args.guesses, args.solutions)

    if args.power:
        guess = word_to_list(args.power.strip())
        power_whole = guess_finder.guess_power(guess)
        power = power_whole / guess_finder.num_solutions()
        pct = 1 - power / guess_finder.num_solutions()
        print("{:,} {:0.1f} {:0.1f}%".format(power_whole, power, pct * 100))
        sys.exit(-1)

    if args.first_principles:
        guess = None
    else:
        guess = word_to_list("roate")

    while True:
        if guess is not None:
            print(list_to_word(guess))
            clue = input("> ")
            guess_finder.filter_solutions(guess, clue)
            print(guess_finder.solutions())
        if 1 == guess_finder.num_solutions():
            return guess_finder.solutions()[0]
        print(guess_finder.num_solutions(), "solutions")
        input("press return to continue")
        t = time.time()
        guess = guess_finder.best_guess(threads=args.threads[0])
        print(time.time() - t, "seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Compute the next optimal Wordle guess.')
    parser.add_argument('-t', dest='threads', type=int, nargs=1,
                        metavar='THREADS', default=[multiprocessing.cpu_count()],
                        help='threads')
    parser.add_argument('--first-principles', dest="first_principles",
                        action="store_true", help="Recompute the first guess from scratch.")
    parser.add_argument('--power', dest="power", help="Compute the expected power of this guess.")
    parser.add_argument('--guesses', dest="guesses", default=GUESSES, help="Valid guess list.")
    parser.add_argument('--solutions', dest="solutions", default=SOLUTIONS, help="Solution list.")
    wordle(parser.parse_args())
