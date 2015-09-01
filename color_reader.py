import kivy

from kivy.app import App
from kivy.uix.widget import Widget

from kivy.clock import Clock
import os
from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics import Color
from kivy.core.image import Image

from kivy.properties import StringProperty,\
                            ListProperty,\
                            ReferenceListProperty,\
                            NumericProperty,\
                            ObjectProperty,\
                            BooleanProperty

from kivy.graphics.instructions import InstructionGroup
from analyser_util import channelIndexFromName 
from PIL import Image as PILImage
from PIL.ImageStat import Stat as imageStat

class ColorReaderSpot(object):
    def __init__(self, idNo = None, type='std', conc=0.0):
        self.idNo = idNo
        self.sampleGrp = None
        self.type = type
        self.conc = conc
        # canvas instruction group
        self.instGrp = InstructionGroup()
        self.colorVal = None
        self.colorMode = None
        self.A = None
        self.spotColor = Color(1, 0, 0, 0.5)
        self.blankSpotColor = Color(0, 0, 0, 0.25)


    def updateText(self):
        assert self.type in ['std', 'sample']
        if self.type == 'std' and self.conc is not None:
            typeText = 'Std ' + str(self.conc)
        elif self.type == 'sample':
            typeText = 'Sample {0}-{1}'.format(self.sampleGrp, self.idNo)
        if self.colorVal is not None:
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
        else:
            text = typeText
        return text


    def addMainSpot(self, size, X, Y):
        self.instGrp.clear()
        self.instGrp.add(self.spotColor)
        self.instGrp.add(Rectangle(size=(size, size), pos=(X, Y)))

                
    def addBlankSpots(self, offset=60):
        size = self.instGrp.children[2].size[0]
        x = self.instGrp.children[2].pos[0]
        y = self.instGrp.children[2].pos[1]
        self.instGrp.add(self.blankSpotColor)
        self.instGrp.add(Rectangle(size=(size, size), pos=(x + offset, y + offset)))
        self.instGrp.add(Rectangle(size=(size, size), pos=(x + offset, y - offset)))
        self.instGrp.add(Rectangle(size=(size, size), pos=(x - offset, y + offset)))
        self.instGrp.add(Rectangle(size=(size, size), pos=(x - offset, y - offset)))


class ColorReader(Widget):
    spots = ListProperty([])
    imageFile = StringProperty('')
    spotCount = NumericProperty(15)
    currentSpot = ObjectProperty(None)
    currentSpotType = StringProperty('std')
    currentSpotSize = NumericProperty(15)
    currentSpotConc = NumericProperty(0.0)
    
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
        self.spots = [ColorReaderSpot(idNo=i+1) for i in range(self.spotCount)]
        for spot in self.spots:
            self.canvas.add(spot.instGrp)
        self.analysisImage = None
        self.currentSpot = self.spots[0]
        

    def initialDraw(self):
        print 'in initial draw'
        print 'image file is ', self.imageFile
        print 'in dir', os.listdir(os.path.dirname(self.imageFile))
        self.analysisImage = PILImage.open(self.imageFile)
        self.analysisImage = self.analysisImage.transpose(\
            PILImage.FLIP_TOP_BOTTOM)
        print 'opening image file:', self.imageFile
        for spot in self.spots:
            if len(spot.instGrp.children) > 1:
                assert len(spot.instGrp.children) == 3 or len(spot.instGrp.children) == 12
                spot.colorMode = self.analysisImage.mode
                if spot.type is None:
                    spot.type = self.currentSpotType
                    spot.conc = self.currentSpotConc
                self.readSpot(self.analysisImage, spot)
                self.readBlankSpots(self.analysisImage, spot)
                buttonStr = spot.updateText()
                self.spotButtonText[spot.idNo - 1] = buttonStr 

 
    def updateSpotSize(self, spotSize):
        try:
            self.currentSpotSize = int(spotSize)
        except ValueError:
            pass


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_down'
            size = self.currentSpotSize
            self.currentSpot.addMainSpot(size, touch.x - size / 2, touch.y - size / 2)


    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_move'
            size = self.currentSpotSize
            self.currentSpot.addMainSpot(size, touch.x - size / 2, touch.y - size / 2)

 
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_up'
            self.currentSpot.type = self.currentSpotType
            self.currentSpot.conc = self.currentSpotConc
            self.currentSpot.addBlankSpots()
            self.readSpot(self.analysisImage, self.currentSpot)
            self.readSpot(self.analysisImage, self.currentSpot)
            self.readBlankSpots(self.analysisImage, self.currentSpot)
            buttonStr = self.currentSpot.updateText()
            self.spotButtonText[self.currentSpot.idNo - 1] = buttonStr

 
    def startMoveBox(self, horiz, vert):
        self.horiz = horiz
        self.vert = vert
        self.moveBox() 
        Clock.schedule_interval(self.moveBox, 0.1)


    def stopMoveBox(self):
        Clock.unschedule(self.moveBox)
    

    def scanAllSpots(self, channel):
        for spot in self.spots:
            self.scanRegion(spot, channel)

    
    def scanRegion(self, spot, channel):
        scanRangeLow = 60
        scanResLow = 10
        scanRangeHigh = 10
        scanResHigh = 1
        channelIndex = channelIndexFromName(channel)
        checkedSpots = []
        pos = spot.instGrp.children[2].pos
        for x in range(int(pos[0] - scanRangeLow), int(pos[0] + scanRangeLow), scanResLow):
            for y in range(int(pos[1] - scanRangeLow), int(pos[1] + scanRangeLow), scanResLow):
                spot.instGrp.children[2].pos = (x, y)
                self.readSpot(self.analysisImage, spot)
                checkedSpots.append((spot.colorVal[channelIndex], x, y))
        posGrp = min(checkedSpots)
        pos = (posGrp[1], posGrp[2])
        checkedSpots = []
        print 'low', pos
        for x in range(int(pos[0] - scanRangeHigh), int(pos[0] + scanRangeHigh), scanResHigh):
            for y in range(int(pos[1] - scanRangeHigh), int(pos[1] + scanRangeHigh), scanResHigh):
                spot.instGrp.children[2].pos = (x, y)
                self.readSpot(self.analysisImage, spot)
                checkedSpots.append((spot.colorVal[channelIndex], x, y))
        posGrp = min(checkedSpots)
        pos = (posGrp[1], posGrp[2])
        print 'high', pos
        size = spot.instGrp.children[2].size[0]
        spot.addMainSpot(size, pos[0], pos[1])
        spot.addBlankSpots()
        self.readSpot(self.analysisImage, spot)
        self.readBlankSpots(self.analysisImage, spot)


    def moveBox(self, *args):
        horiz = self.horiz
        vert = self.vert
        assert len(self.currentSpot.instGrp.children) == 3 or\
               len(self.currentSpot.instGrp.children) == 12
        for x in self.currentSpot.instGrp.children:
            if str(type(x)) == "<type 'kivy.graphics.vertex_instructions.Rectangle'>":
                x.pos = (x.pos[0] + horiz, x.pos[1] + vert)
        self.readSpot(self.analysisImage, self.currentSpot)
        self.readBlankSpots(self.analysisImage, self.currentSpot)
        buttonStr = self.currentSpot.updateText()
        self.spotButtonText[self.currentSpot.idNo - 1] = buttonStr


    def readSpot(self, image, spot):
        spotSize = spot.instGrp.children[2].size[0]
        spotX = spot.instGrp.children[2].pos[0]
        spotY = spot.instGrp.children[2].pos[1]
        scaled_x = int((spotX - self.x) * (image.size[0] / float(self.width)))
        scaled_y = int((spotY - self.y) * (image.size[1] / float(self.height)))
        scaled_spotWidth = int(spotSize * (image.size[0] / float(self.width)))
        scaled_spotHeight = int(spotSize * (image.size[1] / float(self.height)))
        croppedImage = image.crop((scaled_x, scaled_y,
                                   scaled_x + scaled_spotWidth,
                                   scaled_y + scaled_spotHeight))
        color = imageStat(croppedImage).mean
        spot.colorVal = color
        spot.colorMode = image.mode


    def readBlankSpots(self, image, spot):
        aveBlank = None
        for i in [5, 7, 9, 11]:
            spotSize = spot.instGrp.children[i].size[0]
            spotX = spot.instGrp.children[i].pos[0]
            spotY = spot.instGrp.children[i].pos[1]
            scaled_x = int((spotX - self.x) * (image.size[0] / float(self.width)))
            scaled_y = int((spotY - self.y) * (image.size[1] / float(self.height)))
            scaled_spotWidth = int(spotSize * (image.size[0] / float(self.width)))
            scaled_spotHeight = int(spotSize * (image.size[1] / float(self.height)))
            croppedImage = image.crop((scaled_x, scaled_y,
                                       scaled_x + scaled_spotWidth,
                                       scaled_y + scaled_spotHeight))
            color = imageStat(croppedImage).mean
            if aveBlank is None:
                aveBlank = [0] * len(color)
            for i in range(len(color)):
                aveBlank[i] += color[i] / 4
        spot.blankVal = aveBlank
        print 'ave blank', spot.blankVal


class CalibrationScreen(Widget):
    tex = ObjectProperty(None, allownone=True)


class SampleScreen(Widget):
    tex = ObjectProperty(None, allownone=True)
    sampleGrp = NumericProperty(1)


    def updateSpotGrps(self):
        print 'sample grp is {}'.format(self.sampleGrp)
        for spot in self.ids['colorReader'].spots:
            spot.sampleGrp = self.sampleGrp
