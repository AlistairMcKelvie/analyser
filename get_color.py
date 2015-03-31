import kivy

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from intersect import intersects, intersection_pt, points_in_poly
from kivy.graphics.vertex_instructions import Line
from kivy.graphics import Color
from kivy.graphics.fbo import Fbo

kivy.require('1.8.0')

kv_file = 'get_color.kv'

class Painter(BoxLayout):
    def __init__(self, **kwargs):
        super(Painter, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        self.canvas.clear()
        self.points_list = []
        with self.canvas:
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
        print points_in_poly(poly_pts, 400, 700)

    def wipe_line(self):
        self.canvas.clear()

    def get_pixel_color(self, x, y):
        image = self.parent.ids['image']
        fbo = Fbo(texture=image.texture, size=image.texture.size)
        offset_x = (image.width - image.norm_image_size[0]) / 2
        offset_y = (image.height - image.norm_image_size[1]) / 2
        scaled_x = x * (image.texture.width / image.norm_image_size[0])
        scaled_y = y * (image.texture.height / image.norm_image_size[1])
        return fbo.get_pixel_color(scaled_x - offset_x, scaled_y - offset_y)


class Main(App):
    def build(self):
        return Builder.load_file(kv_file)


if __name__ == '__main__':
    Main().run()
