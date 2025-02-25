import unittest
from unittest.mock import Mock

from actionflow.tools import group_by


class TestGroupby(unittest.TestCase):
    def test_1(self):
        inputs = [
            Mock(concurrency=False),
            Mock(concurrency=False),
            Mock(concurrency=False),
            Mock(concurrency=True),
        ]
        expected = [
            [inputs[0]],
            [inputs[1]],
            [inputs[2]],
            [inputs[3]],
        ]
        self.assertEqual(group_by(inputs, "concurrency"), expected)

    def test_2(self):
        inputs = [
            Mock(concurrency=False),
            Mock(concurrency=False),
            Mock(concurrency=False),
            Mock(concurrency=True),
            Mock(concurrency=False),
        ]
        expected = [
            [inputs[0]],
            [inputs[1]],
            [inputs[2]],
            [inputs[3]],
            [inputs[4]],
        ]
        self.assertEqual(group_by(inputs, "concurrency"), expected)

    def test_3(self):
        inputs = [
            Mock(concurrency=True),
            Mock(concurrency=True),
            Mock(concurrency=False),
            Mock(concurrency=False),
        ]
        expected = [
            [inputs[0], inputs[1]],
            [inputs[2]],
            [inputs[3]],
        ]
        self.assertEqual(group_by(inputs, "concurrency"), expected)

    def test_4(self):
        inputs = [
            Mock(concurrency=False),
            Mock(concurrency=True),
            Mock(concurrency=True),
        ]
        expected = [
            [inputs[0]],
            [inputs[1], inputs[2]],
        ]
        self.assertEqual(group_by(inputs, "concurrency"), expected)

    def test_5(self):
        inputs = [
            Mock(concurrency=True),
            Mock(concurrency=True),
            Mock(concurrency=True),
            Mock(concurrency=False),
        ]
        expected = [
            [inputs[0], inputs[1], inputs[2]],
            [inputs[3]],
        ]
        self.assertEqual(group_by(inputs, "concurrency"), expected)


if __name__ == "__main__":
    unittest.main()
