import numpy
import unittest
import wordle_solve


class TestWordleSolver(unittest.TestCase):
    @unittest.skip("does not work yet")
    def test_gen_clue(self):
        correct = numpy.array(wordle_solve.word_to_list("bgggg"))
        result = wordle_solve.gen_clue("slump", "plump")
        self.assertTrue(numpy.array_equal(correct, result))

    @unittest.skip("does not work yet")
    def test_blank_g(self):
        words = words_to_lists(["plump", "slump"])
        words_b = blank_g(words, "bgbgb")
        correct = numpy.array([[15, 11, 20, 12, 15],
                               [18, 11, 20, 12, 15]])
        self.assertTrue(numpy.array_equal(words, correct))
        correct_b = numpy.array([[15, -1, 20, -1, 15],
                                 [18, -1, 20, -1, 15]])
        self.assertTrue(numpy.array_equal(words_b, correct_b))

    @unittest.skip("does not work yet")
    def test_incorrect(self):
        words = numpy.array(wordle_solve.words_to_lists(["plump", "slump"]))
        sel = wordle_solve.incorrect_sel(words, words[0][0], 0)
        correct = numpy.array([False, True])
        self.assertTrue(numpy.array_equal(sel, correct))

    @unittest.skip("skip this")
    def test_solutions_bg(self):
        solutions = wordle_solve.words_to_lists(["plump", "slump"])
        clue = numpy.array(wordle_solve.word_to_list("bgggg"))
        result = wordle_solve.filter_solutions(solutions, solutions[0], clue)
        correct = solutions[1].reshape(1, 5)
        self.assertTrue(numpy.array_equal(result, correct))

    @unittest.skip("skip this")
    def test_solutions_by(self):
        solutions = wordle_solve.words_to_lists(
            ["aaaaa",
             "aaaac",
             "caaaa"])
        guess = numpy.array(wordle_solve.word_to_list("aaaac"))
        clue = numpy.array(wordle_solve.word_to_list("bbbby"))
        result = wordle_solve.filter_solutions(solutions, guess, clue)
        correct = solutions[2].reshape(1, 5)
        self.assertTrue(numpy.array_equal(result, correct))

    @unittest.skip("does not work yet")
    def test_solutions_uniform(self):
        solutions = wordle_solve.words_to_lists(
            ["abcde",
             "edcba",
             "debac"])
        guess = numpy.array(wordle_solve.word_to_list("abcde"))
        clue = numpy.array(wordle_solve.word_to_list("yyyyy"))
        result = wordle_solve.filter_solutions(solutions, guess, clue)
        correct = solutions[2].reshape(1, 5)
        self.assertTrue(numpy.array_equal(result, correct))

        clue = numpy.array(wordle_solve.word_to_list("ggggg"))
        result = wordle_solve.filter_solutions(solutions, guess, clue)
        correct = solutions[0].reshape(1, 5)
        self.assertTrue(numpy.array_equal(result, correct))

    def test_solutions_roate(self):
        solutions = wordle_solve.words_to_lists(
            ["roate",
             "abase",
             "abide",
             "snbue"])
        guess = numpy.array(wordle_solve.word_to_list("roate"))
        clue = numpy.array(wordle_solve.word_to_list("bbbbg"))
        result = wordle_solve.filter_solutions(solutions, guess, clue)
        print(wordle_solve.lists_to_words(result))
        correct = solutions[-1].reshape(1, 5)
        self.assertTrue(numpy.array_equal(result, correct))

if __name__ == "__main__":
    unittest.main()
