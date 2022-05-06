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


def lists_to_words(words):
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


def remove_word(words, word):
    sel = numpy.not_equal(words, word).any(axis=1)
    return words[sel]


def filter_solutions(solutions, guess, clue):
    for i, clue_c in enumerate(clue.lower()):
        ci = guess[i]
        if clue_c == 'g':
            solutions = filter_correct(solutions, ci, i)
        elif clue_c == 'y':
            solutions = filter_wrong_place(solutions, ci, i)
        elif clue_c == 'b':
            solutions = filter_incorrect(solutions, ci)
        else:
            assert(False)
        if 0 == solutions.shape[0]:
            break
    return solutions


def gen_clue(solution, guess):
    """Generate the clue for a given answer."""
    rv = []
    for ac, gc in zip(solution, guess):
        if ac == gc:
            rv.append('g')
        elif gc in solution:
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
        return lists_to_words(self._solutions)

    def guesses(self):
        return lists_to_words(self._guesses)

    def filter_solutions(self, guess, clue):
        self._solutions = filter_solutions(self._solutions, guess, clue)
        return self._solutions

    def filter_guesses(self, guess, clue):
        for i, clue_c in enumerate(clue.lower()):
            ci = guess[i]
            if clue_c == 'g':
                self._guesses = filter_correct(self._guesses, ci, i)
            elif clue_c == 'y':
                self._guesses = filter_wrong_place(self._guesses, ci, i)
            if 0 == self._guesses.shape[0]:
                break
        print(lists_to_words(self._guesses))
        print(self.num_guesses(), "guesses")

    def remove_solution(self, word):
        self._solutions = remove_word(self._solutions, word)

    def remove_guess(self, word):
        self._guesses = remove_word(self._guesses, word)

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
        p = False
        if self._min_rank is None or (result > 0 and self._min_rank > result):
            self._min_guesses_i = [guess_i]
            self._min_rank = result
            p = True
        elif self._min_rank == result:
            self._min_guesses_i.append(guess_i)
            p = True
        min_words = [list_to_word(self._guesses[i]) for i in self._min_guesses_i]
        min_words = " ".join(min_words)
        cur_word = list_to_word(self._guesses[guess_i])
        ns = self._solutions.shape[0]
        if p:
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
            chunksize = int(self.num_guesses() / (2 * threads))
            with multiprocessing.Pool(threads) as pool:
                for p in pool.imap_unordered(self.guess_power_i, guesses_i_it, chunksize=chunksize):
                    guess_i, result = p
                    self.min_guess(guess_i, result)

        guesses = {tuple(x) for x in self._guesses[self._min_guesses_i]}
        solutions = {tuple(x) for x in self._solutions}
        subset = list(sorted(solutions.intersection(guesses)))
        if subset:
            print("CLOSE", lists_to_words(subset))
            guess = subset[0]
        else:
            guess = self._guesses[self._min_guesses_i[0]]
        return guess

    def best_guess_solution(self, solution):
        self._guesses = remove_word(self._guesses, solution)
        min_power = None
        min_guess = []
        for guess in self._guesses:
            clue = gen_clue(solution, guess)
            power = filter_solutions(self._solutions, guess, clue).shape[0]
            if min_power is None or power < min_power:
                min_power = power
                min_guess = [guess]
            elif power == min_power:
                min_guess.append(guess)

        for guess in min_guess:
            clue = gen_clue(solution, guess)
            solutions = filter_solutions(self._solutions, guess, clue)
            print(list_to_word(guess), lists_to_words(solutions))

        guesses = lists_to_words(min_guess)

        if False:
            solutions = set(lists_to_words(self._solutions))
            guesses = set(guesses)
            guesses = list(sorted(guesses.intersection(solutions)))

        print(", ".join(guesses))

        sys.exit(0)


def wordle(args):
    guess_finder = GuessFinder(args.guesses, args.solutions)

    if args.solution:
        solution = word_to_list(args.solution)
        guess_finder.best_guess_solution(solution)

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
            if args.hard:
                sys.stdout.write("{:,} guesses, ".format(guess_finder.num_guesses()))
            sys.stdout.write("{:,} solutions\n".format(guess_finder.num_solutions()))
            print(list_to_word(guess))
            clue = input("> ")
            if ' ' in clue:
                guess, clue = clue.split()
                guess = word_to_list(guess)
            guess_finder.filter_solutions(guess, clue)
            guess_finder.remove_guess(guess)
            guess_finder.remove_solution(guess)
            if args.hard:
                guess_finder.filter_guesses(guess, clue)
        if 1 == guess_finder.num_solutions():
            return guess_finder.solutions()[0]
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
    parser.add_argument('--hard', dest="hard", action="store_true", help="Hard mode.")
    parser.add_argument('--power', dest="power", help="Compute the expected power of this guess.")
    parser.add_argument('--guesses', dest="guesses", default=GUESSES, help="Valid guess list.")
    parser.add_argument('--solutions', dest="solutions", default=SOLUTIONS, help="Solution list.")
    parser.add_argument('--solution', dest="solution", help="Provide the answer for insanely lucky guesses.")
    print("The word is", wordle(parser.parse_args()))
