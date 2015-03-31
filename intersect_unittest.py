import unittest
import intersect


class test_intersect(unittest.TestCase):
    def test_general(self):
        seg1 = ((-1, -1), (1, 1))
        seg2 = ((-1, 1), (1, -1))
        pt = intersect.intersection_pt(seg1, seg2)
        self.assertEqual(pt['point'], (0, 0))

    def test_inline_vertical(self):
        seg1 = ((10, 20.5), (10, 43))
        seg2 = ((10, 32), (10, 40))
        seg = intersect.intersection_pt(seg1, seg2)
        self.assertEqual(seg['seg'], ((10, 32), (10, 40)))

    def test_inline_general(self):
        seg1 = ((-10, -10), (10, 0))
        seg2 = ((-20, -15), (0, -5))
        seg = intersect.intersection_pt(seg1, seg2)
        self.assertEqual(seg['seg'], ((-10, -10), (0, -5)))

    def test_1_vertical(self):
        seg1 = ((-1, -1), (-1, 20))
        seg2 = ((0, 0), (-2, 2))
        pt = intersect.intersection_pt(seg1, seg2)
        self.assertEqual(pt['point'], (-1, 1))

    def test_2_vertical(self):
        seg1 = ((4, 0), (5, 2))
        seg2 = ((4.5, 40), (4.5, 2))
        pt = intersect.intersection_pt(seg1, seg2)
        self.assertEqual(pt['point'], (4.5, 1))

    def test_points_in_poly(self):
        poly = [(1, 1), (1, 3), (3, 5), (3, 1)]
        x = 6
        y = 6
        self.assertEqual([(1, 1), (2, 1), (3, 1), (1, 2), (2, 2), (3, 2), 
                          (1, 3), (2, 3), (3, 3), (2, 4), (3, 4), (3, 5)],
                         intersect.points_in_poly(poly, x, y))

if __name__ == '__main__':
    unittest.main()
