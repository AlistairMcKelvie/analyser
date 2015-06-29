import kivy

from kivy.uix.widget import Widget

from kivy.clock import Clock

from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics import Color
from kivy.graphics.fbo import Fbo

from kivy.properties import StringProperty,\
                            ReferenceListProperty,\
                            NumericProperty,\
                            ObjectProperty,\
                            BooleanProperty

from kivy.graphics.instructions import InstructionGroup

from PIL import Image as PILImage
from PIL.ImageStat import Stat as imageStat

class ColorReaderSpot(object):
    def __init__(self, type='Blank', conc=0):
        self.type = type
        self.conc = conc
        # canvas instruction group
        self.instGrp = InstructionGroup()
        self.colorVal = None
        self.colorMode = None
        self.A = None


    def updateText(self):
        if self.colorVal is None:
            print 'No color value, not updating spot text'
            return None
        
        if self.type == 'Std':
            typeText = 'Std ' + str(self.conc)
        else:
            typeText = self.type
        if self.colorMode == 'RGB':
            print 'spot color type is RGB'
            lStr = ('[b]{0}[/b]\nR: {1:03.0f}   G: {2:03.0f}   B: {3:03.0f}')
            text = lStr.format(typeText, self.colorVal[0],
                                    self.colorVal[1], self.colorVal[2])
        elif self.colorMode == 'RGBA':
            print 'spot colr type is RGBA'
            lStr = ('[b]{0}[/b]\nR: {1:03.0f}   '
                    'G: {2:03.0f}   B: {3:03.0f}   A: {4:03.0f}')
            text = lStr.format(typeText, self.colorVal[0],
                               self.colorVal[1], self.colorVal[2],
                               self.colorVal[3])
        elif self.colorMode is None:
            print 'programming error color mode not set'
            text = 'color mode not set'
        else:
            print 'unknown color format'
            text = 'unknown color format'
        return text


class ColorReader(Widget):
    imageFile = StringProperty('')
    spotCount = NumericProperty(15)
    currentSpot = NumericProperty(1)
    currentSpotType = StringProperty('Blank')
    currentSpotSize = NumericProperty(15)
    currentSpotConc = ObjectProperty(0)
    
    text1 = StringProperty('1')
    text2 = StringProperty('2')
    text3 = StringProperty('3')
    text4 = StringProperty('4')
    text5 = StringProperty('5')
    text6 = StringProperty('6')
    text7 = StringProperty('7')
    text8 = StringProperty('8')
    text9 = StringProperty('9')
    text10 = StringProperty('10')
    text11 = StringProperty('11')
    text12 = StringProperty('12')
    text13 = StringProperty('13')
    text14 = StringProperty('14')
    text15 = StringProperty('15')
    spotButtonText = ReferenceListProperty(text1,
                                           text2,
                                           text3,
                                           text4,
                                           text5,
                                           text6,
                                           text7,
                                           text8,
                                           text9,
                                           text10,
                                           text11,
                                           text12,
                                           text13,
                                           text14,
                                           text15)


    def __init__(self, **kwargs):
        super(ColorReader, self).__init__(**kwargs)
        self.spotColor = Color(0, 0, 0, 0.25)
        self.spots = [ColorReaderSpot() for i in range(self.spotCount)]
        for spot in self.spots:
            spot.instGrp.add(self.spotColor)
            self.canvas.add(spot.instGrp)
        self.initialImageAndDrawDone = False
        self.analysisImage = None
        

    def initialDraw(self):
        self.analysisImage = PILImage.open(self.imageFile)
        self.analysisImage = self.analysisImage.transpose(\
            PILImage.FLIP_TOP_BOTTOM)
        
        for i in range(self.spotCount):
            self.spots[i].colorMode = self.analysisImage.mode
            buttonStr = self.spots[i].updateText()
            if buttonStr is not None:
                self.spotButtonText[i] = buttonStr

 
    def updateSpotSize(self, boxSize):
        try:
            self.currentBoxSize = int(boxSize)
        except ValueError:
            pass
        return str(self.currentBoxSize)


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_down'
            self.spots[self.currentSpot - 1].instGrp.clear()
            size = self.currentSpotSize
            self.spots[self.currentSpot - 1].instGrp.add(self.spotColor)
            touch.ud['Rectangle'] = Rectangle(pos=(touch.x - size / 2,
                                                   touch.y - size / 2),
                                              size=(size, size))
            self.spots[self.currentSpot - 1].instGrp.add(touch.ud['Rectangle'])


    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_move'
            size = self.currentSpotSize
            self.spots[self.currentSpot - 1].instGrp.clear()
            touch.ud['Rectangle'].pos = (touch.x - size / 2, touch.y - size / 2)
            self.spots[self.currentSpot - 1].instGrp.add(self.spotColor)
            self.spots[self.currentSpot - 1].instGrp.add(touch.ud['Rectangle'])

    
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
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
        if len(self.instructions[self.currentSpot - 1].children) == 3:
            pos = self.instructions[self.currentSpot - 1].children[2].pos
            self.instructions[self.currentSpot - 1].children[2].pos = (pos[0] + horiz,
                                                                       pos[1] + vert)
            self.readRectangle()


    def readRectangle(self):
        image = self.analysisImage
        self.spots[self.currentSpot - 1].type = self.currentSpotType
        self.spots[self.currentSpot - 1].conc = self.currentSpotConc
        spotSize = self.spots[self.currentSpot - 1].instGrp.children[2].size[0]
        print 'spot no', self.currentSpot
        print 'instruction list', self.spots[self.currentSpot - 1].instGrp.children
        spotX = self.spots[self.currentSpot - 1].instGrp.children[2].pos[0]
        spotY = self.spots[self.currentSpot - 1].instGrp.children[2].pos[1]
        scaled_x = int((spotX - self.x) * (image.size[0] / float(self.width)))
        scaled_y = int((spotY - self.y) * (image.size[1] / float(self.height)))
        scaled_spotWidth = int(spotSize * (image.size[0] / float(self.width)))
        scaled_spotHeight = int(spotSize * (image.size[1] / float(self.height)))
        croppedImage = image.crop((scaled_x, scaled_y,
                                   scaled_x + scaled_spotWidth,
                                   scaled_y + scaled_spotHeight))
        color = imageStat(croppedImage).mean
        self.spots[self.currentSpot - 1].colorVal = color
        self.spots[self.currentSpot - 1].colorMode = image.mode
        buttonStr = self.spots[self.currentSpot - 1].updateText()

        if buttonStr is not None:
            self.spotButtonText[self.currentSpot - 1] = buttonStr
            
        
class ColorReaderScreen(Widget):
    valTextWasModifiedByToggle = BooleanProperty(False)


    def updateConcText(self):
        print 'on text was called'
        print self.valTextWasModifiedByToggle
        currentSpot = self.ids['colorReader'].currentSpot
        if not self.valTextWasModifiedByToggle:
            print 'toggle state updated'
            text = self.ids['sampleValText'].text
            if text == '':
                self.ids['sampleValText'].text = 0
            print text
            try:
                self.ids['colorReader'].spots[currentSpot - 1].conc = float(text)
                self.ids['colorReader'].currentSpotConc = float(text)
                print self.ids['colorReader'].currentSpotConc
                self.ids['sampleToggle'].state = 'normal'
                self.ids['sampleToggle'].background = 'normal'
                self.ids['blankToggle'].state = 'normal'
                self.ids['blankToggle'].background = 'normal'
                self.ids['colorReader'].currentSpotType = 'Std'
            except ValueError:
                print 'excepting'
                self.ids['sampleValText'].text = '-'
        else:
            self.valTextWasModifiedByToggle = False


