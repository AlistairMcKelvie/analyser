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
from kivy.graphics.instructions import InstructionGroup

from intersect import intersects, intersection_pt, points_in_poly
import os.path
from PIL import Image as PILImage
from PIL.ImageStat import Stat as imageStat
kv_file = 'Main.kv'


class Painter(Widget):
    def __init__(self, **kwargs):
        super(Painter, self).__init__(**kwargs)
        self.boxHeight = 20
        self.boxNo = 1
        self.instructions = [InstructionGroup() for _ in range(15)]
        self.xList = [None] * 15
        self.yList = [None] * 15


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            #self.points_list = [(touch.x, max(touch.y, self.y))]
            self.instructions[self.boxNo - 1].clear()
            self.parent.refToPainterCanvas = self.canvas.proxy_ref
            '''
            with self.canvas:
                Color(0, 0, 0, 1)
                touch.ud['line'] = Line(points=(touch.x, touch.y), width=3)
            '''
            h = self.boxHeight
            self.instructions[self.boxNo - 1].add(Color(0, 0, 0, 0.25))
            touch.ud['Rectangle'] = Rectangle(pos=(touch.x - h / 2, touch.y  - h / 2),
                                              size=(h, h))
            self.instructions[self.boxNo - 1].add(touch.ud['Rectangle'])
            self.canvas.add(self.instructions[self.boxNo - 1])


    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            #touch.ud['line'].points += [touch.x, max(touch.y, self.y)]
            #self.points_list.append((touch.x, max(touch.y, self.y)))
            h = self.boxHeight
            touch.ud['Rectangle'].pos = (touch.x - h / 2, touch.y - h / 2)


    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            self.xList[self.boxNo - 1] = touch.x
            self.yList[self.boxNo - 1] = touch.y


    def readRectangle(self, imageFile):
        x = self.xList[self.boxNo - 1]
        y = self.yList[self.boxNo - 1]
        image = PILImage.open(imageFile)
        image = image.transpose(PILImage.FLIP_TOP_BOTTOM)
        #fbo = Fbo(texture=image.textur size=image..size)
        scaled_x = int(x * (image.size[0] / float(self.width)))
        scaled_y = int((y - self.y) * (image.size[1] / float(self.height)))
        scaled_boxWidth = int(self.boxHeight * (image.size[0] / float(self.width)))
        scaled_boxHeight = int(self.boxHeight * (image.size[1] / float(self.height)))
        #print fbo.get_pixel_color(scaled_x, scaled_y)
        croppedImage = image.crop((scaled_x, scaled_y,
                                   scaled_x + scaled_boxWidth, scaled_y + scaled_boxHeight))
        rgba = imageStat(croppedImage).mean
        return [rgba[0], rgba[1], rgba[2], rgba[3]]



    def getColor(self, imageFile):
        intersection_found = False
        self.points_list = deleteDuplicatesFromList(self.points_list)
        for a in xrange(len(self.points_list)-2):
            for c in xrange(a + 2, len(self.points_list) - 1):
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
        self.canvas.clear()
        self.parent.refToPainterCanvas.clear()
        with self.canvas:
            Color(0, 0, 0, 1)
            Line(points=poly_pts_list, width=3, close=True)

        pointsInPoly = points_in_poly(poly_pts, self.width, self.height + self.y, 4)
        averageColor = self.getAverageColor(pointsInPoly, imageFile)
        with self.canvas:
            Color(0, 0, 0, 0.5)
            Line(points=[item for pair in pointsInPoly for item in pair], width=3 )
        return averageColor

    
    def getAverageColor(self, pointsInPoly, imageFile):
        texture = Image(imageFile).texture
        fbo = Fbo(texture=texture, size=texture.size)
        heightRatio = fbo.size[1] / float(self.height)
        widthRatio = fbo.size[0] / float(self.width)
        scaledPointsInPoly = set()
        for point in pointsInPoly:
            scaledPointsInPoly.add((int((point[0] - self.x) * widthRatio),
                                    int((self.height-(point[1] - self.y)) * heightRatio)))

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


    def readRectangle(self, imageFile):
        color = self.ids['painter'].readRectangle(imageFile)
        lStr = ('R: {0:05.1f}   G: {1:05.1f}   B: {2:05.1f}   A: {3:05.1f}')
        self.ids['rgbLabel'].text = lStr.format(color[0], color[1], color[2], color[3])

        
class GraphScreen(Widget):
    pass


class FileChooserScreen(Widget):
    pass


class Main(App):
    def build(self):
        Builder.load_file(kv_file)
        self.graphScreen = GraphScreen()
        self.analyserScreen = AnalyserScreen()
        self.fileChooserScreen = FileChooserScreen()
        return self.fileChooserScreen
    
        
    def goto_analyser(self, imageFile=None):
        Window.remove_widget(self.fileChooserScreen)
        Window.remove_widget(self.graphScreen)
        Window.add_widget(self.analyserScreen)
        if imageFile is not None:
            self.imageFile = self.resizeImage(imageFile)
            self.analyserScreen.canvas.before.clear()
            with self.analyserScreen.canvas.before:
                print self.analyserScreen.height
                Rectangle(source=self.imageFile,
                          size=(self.analyserScreen.width, self.analyserScreen.height*0.75),
                          pos=(self.analyserScreen.x, self.analyserScreen.height*0.25))


    def goto_graph(self):
        Window.remove_widget(self.analyserScreen)
        Window.add_widget(self.graphScreen)

    def resizeImage(self, imageFile):
        basewidth = 300
        img = PILImage.open(imageFile)
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), PILImage.ANTIALIAS)
        nFile = os.path.dirname(imageFile) + '/resized_' + os.path.basename(imageFile)
        img.save(nFile)
        return nFile


if __name__ == '__main__':
    Main().run()
