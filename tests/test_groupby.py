import unittest
from unittest.mock import Mock

from actionflow.tools import group_by


class TestGroupby(unittest.TestCase):
    def test_1(self):
        inputs = [
            Mock(wait=False),
            Mock(wait=False),
            Mock(wait=False),
            Mock(wait=True),
        ]
        expected = [
            [inputs[0], inputs[1], inputs[2], inputs[3]],
        ]
        self.assertEqual(group_by(inputs, "wait"), expected)

    def test_2(self):
        inputs = [
            Mock(wait=False),
            Mock(wait=False),
            Mock(wait=False),
            Mock(wait=True),
            Mock(wait=False),
        ]
        expected = [
            [inputs[0], inputs[1], inputs[2], inputs[3]],
            [inputs[4]],
        ]
        self.assertEqual(group_by(inputs, "wait"), expected)

    def test_3(self):
        inputs = [
            Mock(wait=True),
            Mock(wait=True),
            Mock(wait=False),
            Mock(wait=False),
        ]
        expected = [
            [inputs[0]],
            [inputs[1]],
            [inputs[2], inputs[3]],
        ]
        self.assertEqual(group_by(inputs, "wait"), expected)

    def test_4(self):
        inputs = [
            Mock(wait=False),
            Mock(wait=True),
            Mock(wait=True),
        ]
        expected = [
            [inputs[0], inputs[1]],
            [inputs[2]],
        ]
        self.assertEqual(group_by(inputs, "wait"), expected)


if __name__ == "__main__":
    unittest.main()
