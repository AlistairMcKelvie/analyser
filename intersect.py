from __future__ import division

def point_on_segment(seg=(), pt=()):
    pt_x_between = (pt[0] <= max(seg[0][0], seg[1][0]) and
                    pt[0] >= min(seg[0][0], seg[1][0]))
    pt_y_between = (pt[1] <= max(seg[0][1], seg[1][1]) and
                    pt[1] >= min(seg[0][1], seg[1][1]))
    if pt_x_between and pt_y_between:
        return True
    else:
        return False


def orientation(p1=(), p2=(), p3=()):
    # Get orientation of p3 in relation to vector
    # p1 -> p2
    val = ((p2[1] - p1[1]) * (p3[0] - p2[0]) -
           (p2[0] - p1[0]) * (p3[1] - p2[1]))
    if val == 0:
        return 'colinear'
    elif val > 0:
        return 'clock'
    else:
        return 'anticlock'


def intersects(seg1=(), seg2=()):
    # Get orientations for required for all cases.
    o1 = orientation(seg1[0], seg1[1], seg2[0])
    o2 = orientation(seg1[0], seg1[1], seg2[1])
    o3 = orientation(seg2[0], seg2[1], seg1[0])
    o4 = orientation(seg2[0], seg2[1], seg1[1])

    # General case, segments cross
    if o1 != o2 and o3 != o4:
        return True

    # If general case is not true, segments do not cross,
    # but one point may lie on on the line/
    elif o1 == 'colinear' and point_on_segment(seg1, seg2[0]):
        return True
    elif o2 == 'colinear' and point_on_segment(seg1, seg2[1]):
        return True
    elif o3 == 'colinear' and point_on_segment(seg2, seg1[0]):
        return True
    elif o4 == 'colinear' and point_on_segment(seg2, seg1[1]):
        return True
    else:
        return False


def intersection_pt(seg1=(), seg2=()):
    '''This function finds the intersection point of two lines
    segments, it assumes they intersect and does not check for 
    intersection. Returns a point unless the segments lie on
    to of each other, in which case it returns a segment
    corresponding to their intersection.'''
    # seg1 is vertical
    if seg1[0][0] == seg1[1][0]:
        x = seg1[0][0]
        # seg2 is also vertical; line are on top each other
        if seg2[0][0] == seg2[1][0]:
            # so return a line where they intersect
            pt_1_y = max(min(seg1[0][1], seg1[1][1]),
                         min(seg2[0][1], seg2[1][1]))
            pt_2_y = min(max(seg1[0][1], seg1[1][1]),
                         max(seg2[0][1], seg2[1][1]))
            return {'point': None, 'seg': ((x, pt_1_y), (x, pt_2_y))}
        # seg2 not vertical, so intersect pt exists
        else:
            # get equation (y = ax + c) for seg2 and return point
            # where it crosses seg1
            a = (seg2[1][1] - seg2[0][1]) / (seg2[1][0] - seg2[0][0])
            c = seg2[0][1] - a * seg2[0][0]
            y = a * x + c
            return {'point': (x, y), 'seg': None}
    # seg2 is vertical
    elif seg2[0][0] == seg2[1][0]:
        x = seg2[0][0]
        # get equation (y = ax + c) for seg1 and return point
        # where it crosses seg1
        a = (seg1[1][1] - seg1[0][1]) / (seg1[1][0] - seg1[0][0])
        c = seg1[0][1] - a * seg1[0][0]
        y = a * x + c
        return {'point': (x, y), 'seg': None}
    else:
        # get equations (y = ax + c) for both segs
        a1 = (seg1[1][1] - seg1[0][1]) / (seg1[1][0] - seg1[0][0])
        a2 = (seg2[1][1] - seg2[0][1]) / (seg2[1][0] - seg2[0][0])
        # If gradients are the same lines lie on top of each other
        if a1 == a2:
            # so return a line where they intersect
            pt_1_x = max(min(seg1[0][0], seg1[1][0]),
                         min(seg2[0][0], seg2[1][0]))
            pt_2_x = min(max(seg1[0][0], seg1[1][0]),
                         max(seg2[0][0], seg2[1][0]))
            pt_1_y = max(min(seg1[0][1], seg1[1][1]),
                         min(seg2[0][1], seg2[1][1]))
            pt_2_y = min(max(seg1[0][1], seg1[1][1]),
                         max(seg2[0][1], seg2[1][1]))
            return {'point': None, 'seg': ((pt_1_x, pt_1_y), (pt_2_x, pt_2_y))}
        # lines intersect (general case)
        else:
            c1 = seg1[0][1] - a1 * seg1[0][0]
            c2 = seg2[0][1] - a2 * seg2[0][0]
            x = (c2 - c1) / (a1 - a2)
            y = a1 * x + c1
            return {'point': (x, y), 'seg': None}

def points_in_poly(poly, width, height, interval=1.0):
    '''returns all the points that lie inside a polygon, including those which lie
    on the boundary. Points are a resolution of one unit, starting from the left 
    of the polygon.'''
    # add first point to end to close path
    poly.append(poly[0])
    pointsInside = []
    for y in range(height):
        intersection_points = []
        for i in range(len(poly) - 1):
            # Make seg with two points from the poly, sorted by y value
            # We need the seg sorted as we need to know if the upper point
            # lies on a y line but ignore lower points to aviod double 
            # counting
            seg = sorted([poly[i], poly[i + 1]], key=lambda tup: tup[1])
            seg = tuple(seg)
            print 'seg', seg
            # Check if higher point lies on y line, and add that point as an
            # intersection point if it does.
            if intersects(((0, y), (width, y)), seg):
                intersect = intersection_pt(((0, y), (width, y)), seg)
                if intersect['seg'] is not None:
                    print 'on line'
                    print intersect['seg']
                    intersection_points.append(intersect['seg'][0])
                    intersection_points.append(intersect['seg'][1])
                elif seg[1][1] == y:
                    print 'on upper point'
                    intersection_points.append(seg[1])
                elif seg[0][1] == y:
                    print 'on lower point'
                    pass
                else:
                    print 'normal intersection'
                    intersection_points.append(intersect['point'])
            print '--------'
        print 'intersection_points', intersection_points
        rowPoints = __addInsidePoints__(intersection_points, interval)
        if rowPoints is not None:
            pointsInside.extend(rowPoints)
    print pointsInside
    return pointsInside


def __addInsidePoints__(intersectionPoints, interval=1.0):
    '''Takes a list of points from the point_in_poly function,
    sorts it by x value, and returns it with points add between
    pairs of points at the specified interval, representing the 
    points inside the poly in that line.'''
    if len(intersectionPoints) % 2 != 0:
        raise RuntimeError('intersectionPoints list must be an even length,'
                           'there is a problem with the list produced by '
                           'points in poly')
    intersectionPoints.sort(key=lambda x: x[0])
    filledPoints = []
    while intersectionPoints:
        filledPoints.append(intersectionPoints.pop(0))
        rightPt = intersectionPoints.pop(0)
        if rightPt == filledPoints[-1]:
            # if right point equals left point, this is a double
            # point at top vertex, only want to include on one of 
            # this pair, so go to next loop
            continue
        while filledPoints[-1][0] + interval <  rightPt[0]:
            filledPoints.append((filledPoints[-1][0] + interval, filledPoints[-1][1]))
        filledPoints.append(rightPt)
    return filledPoints
