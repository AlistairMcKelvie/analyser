import kivy

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.lang import Builder
from intersect import intersects, intersection_pt, points_in_poly
from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color
from kivy.graphics.fbo import Fbo


kivy.require('1.9.0')

kv_file = 'get_color.kv'

class Painter(Widget):
    def __init__(self, **kwargs):
        super(Painter, self).__init__(**kwargs)


    def on_touch_down(self, touch):
        self.canvas.clear()
        self.points_list = [(touch.x, touch.y)]
        with self.canvas.before:
            touch.ud['line'] = Line(points=(touch.x, touch.y), width=3)


    def on_touch_move(self, touch):
        touch.ud['line'].points += [touch.x, touch.y]
        self.points_list.append((touch.x, touch.y))


    def return_points(self):
        intersection_found = False
        for a in xrange(len(self.points_list)-2):
            for c in xrange(a + 2, len(self.points_list)-1):
                b = a + 1
                d = c + 1
                seg1 = (self.points_list[a], self.points_list[b])
                seg2 = (self.points_list[c], self.points_list[d])

                if intersects(seg1, seg2):
                    intersection_found = True
                    intersection = intersection_pt(seg1, seg2)
                    if intersection['point']:
                        poly_pts = self.points_list[b:c]
                        print "intersection['point']", intersection['point']
                        poly_pts.append(intersection['point'])
                    else:
                        poly_pts = self.points_list[b:c]
                        poly_pts.append(intersection['seg'][0])
                        poly_pts.append(intersection['seg'][1])

        if not intersection_found:
            poly_pts = self.points_list
        
        # make list of tuples in to list as Line() requires
        poly_pts_list = [item for pair in poly_pts for item in pair]

        # draw shape
        self.canvas.clear()
        with self.canvas:
            Line(points=poly_pts_list, width=3, close=True)
        width = self.parent.parent.width
        height = self.parent.pa:rent.height
        print self.width
        print sorted(poly_pts, key=lambda x: x[1])
        pointsInPoly = points_in_poly(poly_pts, width, height)
        #pointsInPoly.sort(
        print len(pointsInPoly)
        pointsInPolyList = [item for pair in pointsInPoly for item in pair]
        i = 0
        red = 0
        green = 0
        blue = 0
        alpha = 0

        for point in pointsInPoly:
            pixel = self.get_pixel_color(point[0], point[1])
            red += pixel[0]
            green += pixel[1]
            blue += pixel[2]
            alpha += pixel[3]
            i += 1
        i = float(i)
        avePixel = [red / i, green / i, blue / i, alpha / i]
        print avePixel
        with self.canvas:
            Line(points=pointsInPolyList)


    def wipe_line(self):
        self.canvas.clear()


    def get_pixel_color(self, x, y):
        image = self.parent.parent.parent.ids['image']
        fbo = Fbo(texture=image.texture, size=image.texture.size)
        scaled_x = x * (image.texture.width / float(image.width - image.x))
        scaled_y = image.texture.height - y * (image.texture.height / float(image.height + image.y))
        return fbo.get_pixel_color(scaled_x, scaled_y)


    def DEBUGTestGetPixel(self):
        image = self.parent.parent.parent.ids['image']
        fbo = Fbo(texture=image.texture, size=image.texture.size)
        for y in range(int(image.height)):
            for x in range(int(image.width)):
                print 'x', x
                print 'y', y
                scaled_x = x * (image.texture.width / float(image.width - image.x))
                scaled_y = image.texture.height - 1 - y * (image.texture.height / float(image.height + image.y))
                print 'scaled x', scaled_x
                print 'scaled y', scaled_y
                gpc = fbo.get_pixel_color(scaled_x, scaled_y)
                print 'get pixel color', gpc
                firstPixelVal = (image.texture.width * int(scaled_y) + int(scaled_x)) * 4
                arrayVal = [ord(i) for i in fbo.pixels[firstPixelVal:firstPixelVal+4]]
                print 'array pixel', arrayVal
                print '~~~~~~~~~~~~~~~~~~~~~~~~~~~'
                if arrayVal != gpc:
                    import ipdb; ipdb.set_trace()


class Main(App):
    def build(self):
        return Builder.load_file(kv_file)


if __name__ == '__main__':
    Main().run()
