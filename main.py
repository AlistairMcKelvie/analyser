import kivy

from myGraph import MyGraph

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.core.image import Image
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from kivy.graphics.vertex_instructions import Line, Rectangle
from kivy.graphics import Color
from kivy.graphics.fbo import Fbo

from intersect import intersects, intersection_pt, points_in_poly
kv_file = 'Main.kv'
imageFile = 'rgb.png'

class Painter(Widget):
    def __init__(self, **kwargs):
        super(Painter, self).__init__(**kwargs)

    def on_touch_down(self, touch):
        self.points_list = [(touch.x, max(touch.y, self.y))]
        self.canvas.clear()
        with self.canvas:
            Color(0, 0, 0, 1)
            touch.ud['line'] = Line(points=(touch.x, touch.y), width=3)


    def on_touch_move(self, touch):
        touch.ud['line'].points += [touch.x, max(touch.y, self.y)]
        self.points_list.append((touch.x, max(touch.y, self.y)))


    def getColor(self):
        intersection_found = False
        self.points_list = deleteDuplicatesFromList(self.points_list)
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
        pointsInPoly = points_in_poly(poly_pts, self.width, self.height + self.y)
        averageColor = self.getAverageColor(pointsInPoly)
        with self.canvas:
            Color(0, 0, 0, 0.5)
            Line(points=[item for pair in pointsInPoly for item in pair])
        return averageColor

    
    def getAverageColor(self, pointsInPoly):
        texture = Image(self.parent.imageFile).texture
        fbo = Fbo(texture=texture, size=texture.size)
        heightRatio = fbo.size[1] / float(self.height)
        widthRatio = fbo.size[0] / float(self.width)
        scaledPointsInPoly = set()
        for point in pointsInPoly:
            scaledPointsInPoly.add((int((point[0] - self.x) * widthRatio),
                                    int((point[1] - self.y) * heightRatio)))

        pixels = [None] * len(scaledPointsInPoly)
        i = 0
        for point in scaledPointsInPoly:
            pixels[i] = fbo.get_pixel_color(point[0], point[1])
            i += 1
        red = sum([x[0] for x in pixels]) / float(len(scaledPointsInPoly))
        green = sum([x[1] for x in pixels]) / float(len(scaledPointsInPoly))
        blue = sum([x[2] for x in pixels]) / float(len(scaledPointsInPoly))
        alpha = sum([x[3] for x in pixels]) / float(len(scaledPointsInPoly))
        return [red, green, blue, alpha]
            

def deleteDuplicatesFromList(l):
    for i in range(len(l)):
        for j in range(len(l) - 1, i, -1):
            if l[i] == l[j]:
                l.pop(j)
    return l


class AnalyserScreen(Widget):
    def __init__(self, **kwargs):
        super(AnalyserScreen, self).__init__(**kwargs)
        self.imageFile = imageFile

    def getColor(self):
        color = self.ids['painter'].getColor()
        lStr = ('R: {0:05.1f}   G: {1:05.1f}   B: {2:05.1f}   A: {3:05.1f}')
        self.ids['rgbLabel'].text = lStr.format(color[0], color[1], color[2], color[3])
        


class GraphScreen(Widget):
    pass


class Main(App):
    def build(self):
        Builder.load_file(kv_file)
        self.graphScreen = GraphScreen()
        self.analyserScreen = AnalyserScreen()
        return self.analyserScreen
    
        
    def goto_analyser(self):
        Window.remove_widget(self.graphScreen)
        Window.add_widget(self.analyserScreen)


    def goto_graph(self):
        Window.remove_widget(self.analyserScreen)
        Window.add_widget(self.graphScreen)
    

if __name__ == '__main__':
    Main().run()
