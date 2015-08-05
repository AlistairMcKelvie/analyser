#!/usr/bin/env python
import unittest
from analyser_math import percentile

class test_percentile(unittest.TestCase):
    def test_1(self):
        data = [4, 4,
                5, 5, 5, 5,
                6, 6, 6,
                7, 7, 7,
                8, 8,
                9, 9, 9,
                10, 10, 10]
        p = 25
        self.assertAlmostEqual(5, percentile(p, data))
    
    
    def test_2(self):
        data = [4, 4,
                5, 5, 5, 5,
                6, 6, 6,
                7, 7, 7,
                8, 8,
                9, 9, 9,
                10, 10, 10]
        p = 85
        self.assertAlmostEqual(9.85, percentile(p, data))
    
    
    def test_3(self):
        data = [2, 3, 5, 9]
        p = 50
        self.assertAlmostEqual(4, percentile(p, data))

    
    def test_4(self):
        data = [2, 3, 5, 9, 11]
        p = 50
        self.assertAlmostEqual(5, percentile(p, data))


if __name__ == '__main__':
    unittest.main()
