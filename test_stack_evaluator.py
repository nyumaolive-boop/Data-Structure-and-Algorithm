import tempfile
import unittest
from pathlib import Path
from fractions import Fraction
from stack_evaluator import Stack, evaluate_expression, format_result, process_file


class EvaluatorTests(unittest.TestCase):
    def test_stack(self):
        stack = Stack()
        self.assertTrue(stack.is_empty())
        with self.assertRaises(IndexError):
            stack.pop()
        with self.assertRaises(IndexError):
            stack.peek()
        stack.push(10)
        stack.push(20)
        self.assertEqual(stack.peek(), 20)
        self.assertEqual(len(stack), 2)
        self.assertEqual(stack.pop(), 20)
        self.assertEqual(stack.pop(), 10)
        self.assertTrue(stack.is_empty())

    def test_valid_expressions(self):
        cases = [('3 + 5 * 2', 13), ('(8 / 4) + 7 * 2', 16),
                 ('10 - (2 + 3) * 4', -10), ('20 / 5 / 2', 2),
                 ('10 - 3 - 2', 5), ('2 * (3 + (4 * 5))', 46),
                 ('-3 + 5', 2), ('2 * -3', -6), ('-(2 + 3)', -5),
                 ('--3', 3), ('1--2', 3), ('2/-(-2)', 1),
                 ('0.1+0.2', Fraction(3, 10)), ('.5 * 8', 4),
                 ('7 / 2', Fraction(7, 2)), (' 42 ', 42), ('0', 0)]
        for expression, expected in cases:
            with self.subTest(expression=expression):
                self.assertEqual(evaluate_expression(expression), expected)

    def test_invalid_expressions(self):
        cases = ['', '2 +', '*3', '2 3', '2(3)', '()', '(2+3',
                 '2+3)', '2**3', '2^3', 'abc', '1..2', '1/0', '5/(2-2)']
        for expression in cases:
            with self.subTest(expression=expression):
                with self.assertRaises(ValueError):
                    evaluate_expression(expression)

    def test_format(self):
        self.assertEqual(format_result(Fraction(16)), '16')
        self.assertEqual(format_result(Fraction(7, 2)), '3.5')
        self.assertEqual(format_result(Fraction(1, 3)), '0.333333333333')

    def test_file_structure_and_recovery(self):
        with tempfile.TemporaryDirectory() as directory:
            source, target = Path(directory)/'in.txt', Path(directory)/'out.txt'
            source.write_text('3+5*2\n  -----  \n\n1/0\n---\n7/2\n')
            self.assertEqual(process_file(source, target), (3, 1))
            self.assertEqual(target.read_text(),
                             '13\n  -----  \n\nError: Division by zero\n---\n3.5\n')
            with self.assertRaises(ValueError):
                process_file(source, source)
            with self.assertRaises(FileNotFoundError):
                process_file(Path(directory)/'missing.txt', target)


if __name__ == '__main__':
    unittest.main()
