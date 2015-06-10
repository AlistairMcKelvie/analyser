import kivy

from myGraph import MyGraph

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget

from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics import Color
from kivy.graphics.fbo import Fbo
from kivy.graphics.instructions import InstructionGroup
from kivy.properties import StringProperty, ListProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock

import os.path
from PIL import Image as PILImage
from PIL.ImageStat import Stat as imageStat

spotCount = 15


class Painter(Widget):
    buttonText = ListProperty(['Sample ' + str(i + 1) for i in range(15)])
    spotConcs = ListProperty([None for __ in range(15)])
    spotVals = ListProperty([None for __ in range(15)])
    imageFile = StringProperty('')
    boxNo = NumericProperty(1)
    spotSizes = ListProperty([15 for __ in range(spotCount)])
    spotXs = ListProperty([None for __ in range(spotCount)])
    spotYs = ListProperty([None for __ in range(spotCount)])
    def __init__(self, **kwargs):
        super(Painter, self).__init__(**kwargs)
        self.instructions = [InstructionGroup() for _ in range(15)]
        for instruction in self.instructions:
            self.canvas.add(instruction)
        self.inSettings = False
        self.boxColor = Color(0, 0, 0, 0.25)


    def initialDraw(self):
        for i in range(spotCount):
            self.instructions[i].clear()
            self.instructions[i].add(self.boxColor)
            self.boxHeight = self.spotSizes[i]
            if self.boxHeight is not None:
                self.instructions[i].add(Rectangle(size=(self.boxHeight, self.boxHeight),
                                                   pos=(self.spotXs[i], self.spotYs[i])))
                self.boxNo = i + 1
                self.readRectangle()
            
        self.boxNo = 1


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos) and not self.inSettings:
            print 'called on_touch_down'
            try:
                self.boxHeight = int(self.parent.ids['boxSizeText'].text)
            except ValueError:
                self.boxHeight = 15
                self.parent.ids['boxSizeText'].text = str(self.boxHeight)
            self.instructions[self.boxNo - 1].clear()
            h = int(self.boxHeight)
            print 'box color object', self.boxColor
            self.instructions[self.boxNo - 1].add(self.boxColor)
            touch.ud['Rectangle'] = Rectangle(pos=(touch.x - h / 2, touch.y  - h / 2),
                                              size=(h, h))
            self.instructions[self.boxNo - 1].add(touch.ud['Rectangle'])


    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos) and not self.inSettings:
            print 'called on_touch_move'
            h = self.boxHeight
            self.instructions[self.boxNo - 1].clear()
            touch.ud['Rectangle'].pos = (touch.x - h / 2, touch.y - h / 2)
            self.instructions[self.boxNo - 1].add(self.boxColor)
            self.instructions[self.boxNo - 1].add(touch.ud['Rectangle'])

    
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos) and not self.inSettings:
            print 'called on_touch_up'
            if self.imageFile != '':
                self.readRectangle()

    
    def startMoveBox(self, horiz, vert):
        self.horiz = horiz
        self.vert = vert
        self.moveBox() 
        Clock.schedule_interval(self.moveBox, 0.1)


    def stopMoveBox(self):
        Clock.unschedule(self.moveBox)


    def moveBox(self, *args):
        horiz = self.horiz
        vert = self.vert
        if len(self.instructions[self.boxNo - 1].children) == 3:
            pos = self.instructions[self.boxNo - 1].children[2].pos
            self.instructions[self.boxNo - 1].children[2].pos = (pos[0] + horiz, pos[1] + vert)
            self.readRectangle()


    def readRectangle(self):
        print 'box no', self.boxNo
        print 'instruction list', self.instructions[self.boxNo - 1].children
        boxX = self.instructions[self.boxNo - 1].children[2].pos[0]
        boxY = self.instructions[self.boxNo - 1].children[2].pos[1]
        image = PILImage.open(self.imageFile)
        image = image.transpose(PILImage.FLIP_TOP_BOTTOM)
        scaled_x = int((boxX - self.x) * (image.size[0] / float(self.width)))
        scaled_y = int((boxY - self.y) * (image.size[1] / float(self.height)))
        scaled_boxWidth = int(self.boxHeight * (image.size[0] / float(self.width)))
        scaled_boxHeight = int(self.boxHeight * (image.size[1] / float(self.height)))
        croppedImage = image.crop((scaled_x, scaled_y,
                                   scaled_x + scaled_boxWidth, scaled_y + scaled_boxHeight))
        color = imageStat(croppedImage).mean
        self.spotVals[self.boxNo - 1] = color

        if image.mode == 'RGB':
            lStr = ('[b]{0}[/b]\nR: {1:03.0f}   G: {2:03.0f}   B: {3:03.0f}')
            self.buttonText[self.boxNo - 1] = lStr.format(self.spotConcs[self.boxNo - 1],
                                                          color[0], color[1], color[2])
        elif image.mode == 'RGBA':
            lStr = ('[b]{0}[/b]\nR: {1:03.0f}   G: {2:03.0f}   B: {3:03.0f}   A: {4:03.0f}')
            self.buttonText[self.boxNo - 1] = lStr.format(self.spotConcs[self.boxNo - 1],
                                                          color[0], color[1], color[2], color[3])
        else:
            print 'WARNING!: Unsupported color mode - {}'.format(image.mode)
            self.buttonText[self.boxNo - 1] = 'WARNING!: Unsupported color mode - {}'.format(image.mode)


class GraphScreen(Widget):
    pass


class ColorReaderScreen(Widget):
    valTextWasModifiedByToggle = BooleanProperty(False)

    def updateText(self):
        print 'on text was called'
        print self.valTextWasModifiedByToggle
        boxNo = self.ids['painter'].boxNo
        if not self.valTextWasModifiedByToggle:
            print 'toggle state updated'
            text = self.ids['sampleValText'].text
            if text == '':
                self.ids['sampleValText'].text = 0
            print text
            try:
                self.ids['painter'].spotConcs[boxNo - 1] = float(text)
                self.ids['sampleToggle'].state = 'normal'
                self.ids['sampleToggle'].background = 'normal'
            except ValueError:
                print 'excepting'
                self.ids['sampleValText'].text = '-'
                self.ids['painter'].spotConcs[boxNo - 1] = 'Sample ' + str(boxNo + 1) 
        else:
            self.valTextWasModifiedByToggle = False


class FileChooserScreen(Widget):
    pass


class Main(App):
    def build(self):
        self.graphScreen = GraphScreen()
        self.colorReaderScreen = ColorReaderScreen()
        self.fileChooserScreen = FileChooserScreen()
        return self.fileChooserScreen
    
        
    def goto_color_reader(self, imageFile=None):
        colorReader = self.colorReaderScreen.ids['painter']
        Window.remove_widget(self.fileChooserScreen)
        Window.remove_widget(self.graphScreen)
        Window.add_widget(self.colorReaderScreen)

        self.imageFile = imageFile
        if imageFile is not None:
            self.colorReaderScreen.ids['painter'].imageFile = imageFile
            self.imageFile = self.resizeImage(imageFile)
            self.colorReaderScreen.canvas.before.clear()
            with self.colorReaderScreen.canvas.before:
                Rectangle(source=self.imageFile,
                          size=(self.colorReaderScreen.width * 0.8,
                                self.colorReaderScreen.height * 0.85),
                          pos=(self.colorReaderScreen.width * 0.2,
                               self.colorReaderScreen.height * 0.15))
        colorReader.initialDraw()


    def goto_graph(self):
        colorReader = self.colorReaderScreen.ids['painter']
        if colorReader.spotConcs.count('Blank') == 0:
            print 'No blank!'
        else:
            self.graphScreen.ids['graph'].updateGraph(colorReader.spotConcs,
                                                      colorReader.spotVals)
        Window.remove_widget(self.fileChooserScreen)
        Window.remove_widget(self.colorReaderScreen)
        Window.add_widget(self.graphScreen)


    def readSpotsFromConfig(self):
        colorReader = self.colorReaderScreen.ids['painter']
        for i in range(spotCount):
            spotConc = self.config.get('SpotConcentrations', str(i))
            if spotConc == 'None':
                colorReader.spotConcs[i] = None
            else:
                try:
                    colorReader.spotConcs[i] = float(spotConc)
                except ValueError:
                    colorReader.spotConcs[i] = str(spotConc)

            spotVal = self.config.get('SpotValues', str(i))
            if spotVal == 'None':
                colorReader.spotVals[i]== None
            else:
                colorReader.spotVals[i] = [float(j) for j in spotVal[1:-1].split(',')]
            
            spotSize = self.config.get('SpotSizes', str(i))
            if spotSize == 'None':
                colorReader.spotSizes[i] = None
            else:
                colorReader.spotSizes[i] = int(spotSize)

            spotX = self.config.get('SpotX', str(i))
            if spotX == 'None':
                colorReader.spotXs[i] = None
            else:
                colorReader.spotXs[i] = float(spotX)

            spotY = self.config.get('SpotY', str(i))
            if spotY == 'None':
                colorReader.spotYs[i] = None
            else:
                colorReader.spotYs[i] = float(spotY)


    def writeSpotsToConfig(self):
        colorReader = self.colorReaderScreen.ids['painter']
        for i in range(spotCount):
            self.config.set('SpotConcentrations', str(i), colorReader.spotConcs[i])
            self.config.set('SpotValues', str(i), colorReader.spotVals[i])
            graphicsInstucts = colorReader.instructions[i].children
            if len(graphicsInstucts) == 3:
                self.config.set('SpotSizes', str(i), int(graphicsInstucts[2].size[0]))
                self.config.set('SpotX', str(i), int(graphicsInstucts[2].pos[0]))
                self.config.set('SpotY', str(i), int(graphicsInstucts[2].pos[1]))
        self.config.write()


    def resizeImage(self, imageFile):
        print imageFile
        basewidth = 800
        img = PILImage.open(imageFile)
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        img = img.resize((basewidth, hsize), PILImage.ANTIALIAS)
        newFile = os.path.dirname(imageFile) + '/resized_' + os.path.basename(imageFile)
        print newFile
        img.save(newFile)
        return newFile


    def build_config(self, config):
        noneDict = {}
        for i in range(spotCount):
            noneDict[str(i)] = None
        config.setdefaults('SpotConcentrations', noneDict)
        config.setdefaults('SpotValues', noneDict)
        config.setdefaults('SpotSizes', noneDict)
        config.setdefaults('SpotX', noneDict)
        config.setdefaults('SpotY', noneDict)
        

if __name__ == '__main__':
    Main().run()

