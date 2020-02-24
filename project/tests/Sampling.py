import unittest
from unittest import mock
from Utilities import DatasetLoader
import numpy as np


class TestSamplingMethods(unittest.TestCase):

    def setUp(self):
        self.col = [['same/horizontal', 0], ['same/vertical', 0], ['diff/horizontal', 0], ['diff/vertical', 0]]
        PSVRT_SAME_H = '../datasets/psvrt/same/horizontal/'
        PSVRT_SAME_V = '../datasets/psvrt/same/vertical/'
        PSVRT_DIFF_H = '../datasets/psvrt/diff/horizontal/'
        PSVRT_DIFF_V = '../datasets/psvrt/diff/vertical/'
        self.PSVRT = {'sd': [[PSVRT_SAME_H, 1], [PSVRT_SAME_V, 1], [PSVRT_DIFF_H, 0], [PSVRT_DIFF_V, 0]],
                      'sr': [[PSVRT_SAME_V, 1], [PSVRT_DIFF_V, 1], [PSVRT_SAME_H, 0], [PSVRT_DIFF_H, 0]]}

    def test_psvrt_sr_multiple_of_four(self):
        with mock.patch.object(DatasetLoader, 'PSVRT', self.PSVRT):
            data = DatasetLoader._load_psvrt('sr', 36).data

        for path, label in data:
            for c in self.col:
                if c[0] in path:
                    c[1] += 1

        self.assertEqual(36, len(data))
        d = np.array(np.array(self.col)[:, 1], dtype=np.int)
        self.assertEqual(4, np.count_nonzero(d == 9))

    def test_psvrt_sr_mod_is_three(self):
        with mock.patch.object(DatasetLoader, 'PSVRT', self.PSVRT):
            data = DatasetLoader._load_psvrt('sr', 35).data

        for path, label in data:
            for c in self.col:
                if c[0] in path:
                    c[1] += 1

        self.assertEqual(35, len(data))
        d = np.array(np.array(self.col)[:, 1], dtype=np.int)
        self.assertEqual(3, np.count_nonzero(d == 9))
        self.assertEqual(1, np.count_nonzero(d == 8))

    def test_psvrt_sr_mod_is_two(self):
        with mock.patch.object(DatasetLoader, 'PSVRT', self.PSVRT):
            data = DatasetLoader._load_psvrt('sr', 34).data

        for path, label in data:
            for c in self.col:
                if c[0] in path:
                    c[1] += 1

        self.assertEqual(34, len(data))
        d = np.array(np.array(self.col)[:, 1], dtype=np.int)
        self.assertEqual(2, np.count_nonzero(d == 9))
        self.assertEqual(2, np.count_nonzero(d == 8))

    def test_psvrt_sr_mod_is_one(self):
        with mock.patch.object(DatasetLoader, 'PSVRT', self.PSVRT):
            data = DatasetLoader._load_psvrt('sr', 33).data

        for path, label in data:
            for c in self.col:
                if c[0] in path:
                    c[1] += 1

        self.assertEqual(33, len(data))
        d = np.array(np.array(self.col)[:, 1], dtype=np.int)
        self.assertEqual(1, np.count_nonzero(d == 9))
        self.assertEqual(3, np.count_nonzero(d == 8))

    def test_psvrt_sd_multiple_of_four(self):
        with mock.patch.object(DatasetLoader, 'PSVRT', self.PSVRT):
            data = DatasetLoader._load_psvrt('sd', 36).data

        for path, label in data:
            for c in self.col:
                if c[0] in path:
                    c[1] += 1

        self.assertEqual(36, len(data))
        d = np.array(np.array(self.col)[:, 1], dtype=np.int)
        self.assertEqual(4, np.count_nonzero(d == 9))

    def test_psvrt_sd_mod_is_three(self):
        with mock.patch.object(DatasetLoader, 'PSVRT', self.PSVRT):
            data = DatasetLoader._load_psvrt('sd', 35).data

        for path, label in data:
            for c in self.col:
                if c[0] in path:
                    c[1] += 1

        self.assertEqual(35, len(data))
        d = np.array(np.array(self.col)[:, 1], dtype=np.int)
        self.assertEqual(3, np.count_nonzero(d == 9))
        self.assertEqual(1, np.count_nonzero(d == 8))

    def test_psvrt_sd_mod_is_two(self):
        with mock.patch.object(DatasetLoader, 'PSVRT', self.PSVRT):
            data = DatasetLoader._load_psvrt('sd', 34).data

        for path, label in data:
            for c in self.col:
                if c[0] in path:
                    c[1] += 1

        self.assertEqual(34, len(data))
        d = np.array(np.array(self.col)[:, 1], dtype=np.int)
        self.assertEqual(2, np.count_nonzero(d == 9))
        self.assertEqual(2, np.count_nonzero(d == 8))

    def test_psvrt_sd_mod_is_one(self):
        with mock.patch.object(DatasetLoader, 'PSVRT', self.PSVRT):
            data = DatasetLoader._load_psvrt('sd', 33).data

        for path, label in data:
            for c in self.col:
                if c[0] in path:
                    c[1] += 1

        self.assertEqual(33, len(data))
        d = np.array(np.array(self.col)[:, 1], dtype=np.int)
        self.assertEqual(1, np.count_nonzero(d == 9))
        self.assertEqual(3, np.count_nonzero(d == 8))
