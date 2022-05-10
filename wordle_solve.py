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
GREEN = ord('g') - ord('a')
YELLOW = ord('y') - ord('a')
BLACK = ord('b') - ord('a')


def char_to_int(c):
    return ord(c) - ord('a')


def int_to_char(i):
    return chr(i + ord('a'))


def word_to_list(word):
    return [char_to_int(c) for c in word.lower()]


def words_to_lists(words):
    return numpy.array([word_to_list(w) for w in words])


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


def remove_word(words, word):
    return words[numpy.not_equal(words, word).any(axis=1)]


def blank_g(words, clue):
    clue = numpy.array(word_to_list(clue))
    rv = words.copy()
    rv[:, clue == GREEN] = -1
    return rv


def correct_sel(words, ci, pos):
    column = words[:, pos]
    sel = numpy.equal(column, ci)
    return sel


def wrong_place_sel(words, ci, pos):
    words_in = numpy.isin(words, ci)
    words_in_pos = numpy.invert(words_in[:, pos])
    words_out_pos = numpy.delete(words_in, pos, axis=1).any(axis=1)
    return numpy.logical_and(words_in_pos, words_out_pos).nonzero()[0]


def incorrect_sel(words, ci, pos):
    sel = numpy.isin(words, ci)
    sel = sel.any(axis=1)
    sel = numpy.invert(sel)
    return sel


def filter_solutions(solutions, guess, clue):
    sel_g = numpy.equal(clue, GREEN)
    if sel_g.any():
        words_is = numpy.equal(solutions, guess)
        words_is_pos = words_is[:, sel_g].all(axis=1)
        words_not_pos = words_is[:, numpy.invert(sel_g)].any(axis=1)
        sel = numpy.logical_and(words_is_pos, numpy.invert(words_not_pos))
        solutions = solutions[sel]
        sel_gi = numpy.invert(sel_g)
        solutions_t = solutions[:, sel_gi]
        clue_t = clue[sel_gi]
    else:
        solutions_t = solutions
        clue_t = clue

    for i, ci in enumerate(clue_t):
        if ci == YELLOW:
            sel = wrong_place_sel(solutions_t, guess[i], i)
        elif ci == BLACK:
            sel = incorrect_sel(solutions_t, guess[i], i)
        solutions = solutions[sel]
        if solutions_t is not solutions:
            solutions_t = solutions_t[sel]

    return solutions


def gen_clue(solution, guess):
    """Generate the clue for a given answer."""
    rv = numpy.full(WORD_LEN, -1)
    solution = list(solution)
    non_g = []
    for i in range(len(solution)):
        if solution[i] == guess[i]:
            rv[i] = GREEN
            solution[i] = None
        else:
            non_g.append(i)
    for i in non_g:
        if guess[i] in solution:
            rv[i] = YELLOW
        else:
            rv[i] = BLACK
    return rv


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
            if clue_c == GREEN:
                sel = correct_sel(self._guesses, ci, i)
                self._guesses = self._guesses[sel]
            elif clue_c == YELLOW:
                sel = wrong_place_sel(self._guesses, ci, i)
                self._guesses = self._guesses[sel]
            if 0 == self._guesses.shape[0]:
                break
        print(lists_to_words(self._guesses))
        print(self.num_guesses(), "guesses")

    def remove_solution(self, word):
        self._solutions = remove_word(self._solutions, word)
        assert(self._solutions.shape[0])

    def remove_guess(self, word):
        self._guesses = remove_word(self._guesses, word)
        assert(self._guesses.shape[0])

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
        last_words = None
        last_rank = 0
        if self._min_rank is None or (result > 0 and self._min_rank > result):
            tag = ""
            if self._min_guesses_i:
                last_words = lists_to_words(self._guesses[self._min_guesses_i])
                last_words = " ".join(last_words)
                last_rank = self._min_rank / self._solutions.shape[0]
            self._min_guesses_i = [guess_i]
            self._min_rank = result
        elif self._min_rank == result:
            self._min_guesses_i.append(guess_i)
            tag = "+"
        else:
            return  # leave without printing

        this_word = self._guesses[self._min_guesses_i[-1]]
        sol = numpy.equal(self._solutions, this_word).all(axis=1)
        sol = sol.any() and "*" or ""
        this_word = list_to_word(this_word)
        this_rank = self._min_rank / self._solutions.shape[0]
        if last_words:
            print(f"{this_word}{sol} {this_rank:0.1f} <",
                  f"{last_words} {last_rank:0.1f}")
        else:
            print(f"{this_word}{sol} {this_rank:0.1f}{tag}")
        sys.stdout.flush()

    def best_guess(self, threads: int):
        """Pick the best guess (from self._guesses) given the possible words"""
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
            chunksize = max(1, int(self.num_guesses() / (2 * threads)))
            with multiprocessing.Pool(threads) as pool:
                for p in pool.imap_unordered(self.guess_power_i, guesses_i_it,
                                             chunksize=chunksize):
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
        assert(self._guesses[0])
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
            assert(solutions.shape[0])

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
        guess = numpy.array(word_to_list("roate"))

    while True:
        if guess is not None:
            if args.hard:
                guess_s = guess_finder.num_guesses()
                sys.stdout.write(f"{guess_s:,} guesses\n")
            sol_s = guess_finder.num_solutions()
            sol_l = sol_s <= 10 and guess_finder.solutions() or ""
            sys.stdout.write(f"{sol_s:,} solutions {sol_l}\n")
            print(list_to_word(guess))
            clue = input("> ")
            if ' ' in clue:
                guess, clue = clue.split()
                guess = numpy.array(word_to_list(guess))
            clue = numpy.array(word_to_list(clue))
            guess_finder.filter_solutions(guess, clue)
            guess_finder.remove_guess(guess)
            guess_finder.remove_solution(guess)
            print(guess_finder.num_solutions(), "solutions")
            print(" ".join(guess_finder.solutions()))
            if args.hard:
                guess_finder.filter_guesses(guess, clue)
                print(guess_finder.num_guesses(), "guesses")
        if 1 == guess_finder.num_solutions():
            return guess_finder.solutions()[0]
        t = time.time()
        guess = guess_finder.best_guess(threads=args.threads[0])
        t = time.time() - t
        print(f"{t:0.2f} seconds")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Compute the next optimal Wordle guess.')
    parser.add_argument('-t', dest='threads', type=int, nargs=1,
                        metavar='THREADS',
                        default=[multiprocessing.cpu_count()],
                        help='threads')
    parser.add_argument('--first-principles', dest="first_principles",
                        action="store_true",
                        help="Recompute the first guess from scratch.")
    parser.add_argument('--hard', dest="hard", action="store_true",
                        help="Hard mode.")
    parser.add_argument('--power', dest="power",
                        help="Compute the expected power of this guess.")
    parser.add_argument('--guesses', dest="guesses", default=GUESSES,
                        help="Valid guess list.")
    parser.add_argument('--solutions', dest="solutions", default=SOLUTIONS,
                        help="Solution list.")
    parser.add_argument('--solution', dest="solution",
                        help="Provide the answer for insanely lucky guesses.")

    args = parser.parse_args()
    print("The word is", wordle(args))
