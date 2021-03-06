import math
import os
import copy

import kivy
from kivy.app import App
from kivy.uix.widget import Widget
from PIL import Image as PILImage
from PIL.ImageStat import Stat as imageStat
from kivy.clock import Clock
from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics import Color
from kivy.core.image import Image
import kivy.metrics as metrics
from kivy.properties import StringProperty,\
                            ListProperty,\
                            ReferenceListProperty,\
                            NumericProperty,\
                            ObjectProperty,\
                            BooleanProperty
from kivy.graphics.instructions import InstructionGroup
from analyser_util import channelIndexFromName 
import analyser_math as am

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
        self.alpha = None
        self.exclude = False

    def toCalibSpot(self):
        return CalibSpot(self.conc, self.colorVal, self.blankVal, self.idNo, self.exclude)


    def updateText(self):
        channelIndex = channelIndexFromName(App.get_running_app().measuredChannel)
        assert self.type in ['std', 'sample']
        if self.type == 'std' and self.conc is not None:
            typeText = 'Std ' + str(self.conc)
        elif self.type == 'sample':
            typeText = 'Sample {0}-{1}'.format(self.sampleGrp, self.idNo)
        if self.colorVal and self.blankVal is not None:
            self.alpha = -math.log10(self.colorVal[0] / self.blankVal)
            if self.colorMode == 'RGB':
                print 'spot color type is RGB'
                lStr = ('[b]{0}[/b]\n'
                        'R: {1:03.0f}   G: {2:03.0f}   B: {3:03.0f}\n'
                        u'Blank: {4:03.0f}  \u03b1: {5:05.3f}')
                text = lStr.format(typeText, self.colorVal[0],
                                   self.colorVal[1], self.colorVal[2],
                                   self.blankVal, self.alpha)
            elif self.colorMode == 'RGBA':
                lStr = (u'[b]{0}[/b]\n'
                         'R: {1:03.0f}   G: {2:03.0f}   B: {3:03.0f}   A: {4:03.0f}\n'
                         'Blank: {4:03.0f}  \u03b1: {5:05.3f}')
                text = lStr.format(typeText, self.colorVal[0],
                                   self.colorVal[1], self.colorVal[2],
                                   self.colorVal[3],
                                   self.blankVal, self.alpha)
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

                
    def addBlankSpots(self, size=2.5):
        self.instGrp.children = self.instGrp.children[:3]
        size = metrics.dp(size)
        mainSize = self.instGrp.children[2].size[0]
        x = self.instGrp.children[2].pos[0] + mainSize / 2 - size / 2
        y = self.instGrp.children[2].pos[1] + mainSize / 2 - size / 2
        self.instGrp.add(self.blankSpotColor)
        self.instGrp.add(Rectangle(size=(size, size), pos=(x, y)))
        self.instGrp.add(Rectangle(size=(size, size), pos=(x, y)))
        self.instGrp.add(Rectangle(size=(size, size), pos=(x, y)))
        self.instGrp.add(Rectangle(size=(size, size), pos=(x, y)))


class CalibSpot(object):
    def __init__(self, conc, colorVal, blankVal, idNo, exclude):
        self.conc = conc
        self.colorVal = colorVal
        self.blankVal = blankVal
        self.idNo = idNo
        self.exclude = exclude

def use_calibration_set(app, colorReader):
    app.writeSpotsToConfig()
    print 'len(app.calibSpots)', len(app.calibSpots)
    for spot in colorReader.spots:
        app.calibSpots.append(spot.toCalibSpot())
    print 'len(app.calibSpots)', len(app.calibSpots)
    app.calib = am.calculateACalibCurve(app.calibSpots, app.calcLog, app.measuredChannel, app.qConfCSV)
    app.writeCalibFile(app.calibFile, app.calib)
    am.writeRawData(app.calib, app.rawFile, app.calibrationScreen.ids['colorReader'].spots, app.measuredChannel, app.firstRaw)
    app.firstRaw = False
    app.goto_calib_results() 

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
        self.app = App.get_running_app()
        

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
                spot.addBlankSpots()
                self.scanBlankSpots(self.analysisImage, spot)
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
            size = metrics.dp(self.currentSpotSize)
            self.currentSpot.addMainSpot(size,
                                         touch.x - size / 2,
                                         touch.y - size / 2)


    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_move'
            size = metrics.dp(self.currentSpotSize)
            self.currentSpot.addMainSpot(size,
                                         touch.x - size / 2,
                                         touch.y - size / 2)

 
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_up'
            self.currentSpot.type = self.currentSpotType
            self.currentSpot.conc = self.currentSpotConc
            self.currentSpot.addBlankSpots()
            self.readSpot(self.analysisImage, self.currentSpot)
            self.readSpot(self.analysisImage, self.currentSpot)
            self.scanBlankSpots(self.analysisImage, self.currentSpot)
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
        scanRangeLow = int(metrics.dp(15))
        scanResLow = int(metrics.dp(5))
        scanRangeHigh = int(metrics.dp(2.5))
        scanResHigh = int(metrics.dp(1))
        channelIndex = channelIndexFromName(channel)
        checkedSpots = []
        pos = spot.instGrp.children[2].pos
        for x in range(int(pos[0] - scanRangeLow),
                       int(pos[0] + scanRangeLow), scanResLow):
            for y in range(int(pos[1] - scanRangeLow),
                           int(pos[1] + scanRangeLow), scanResLow):
                spot.instGrp.children[2].pos = (x, y)
                self.readSpot(self.analysisImage, spot)
                checkedSpots.append((spot.colorVal[channelIndex], x, y))
        posGrp = min(checkedSpots)
        pos = (posGrp[1], posGrp[2])
        checkedSpots = []
        print 'low', pos
        for x in range(int(pos[0] - scanRangeHigh),
                       int(pos[0] + scanRangeHigh), scanResHigh):
            for y in range(int(pos[1] - scanRangeHigh),
                           int(pos[1] + scanRangeHigh), scanResHigh):
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
        self.scanBlankSpots(self.analysisImage, spot)
        buttonStr = spot.updateText()
        self.spotButtonText[spot.idNo - 1] = buttonStr 


    def moveBox(self, *args):
        horiz = self.horiz
        vert = self.vert
        assert len(self.currentSpot.instGrp.children) == 3 or\
               len(self.currentSpot.instGrp.children) == 12
        for x in self.currentSpot.instGrp.children:
            if str(type(x)) == "<type 'kivy.graphics.vertex_instructions.Rectangle'>":
                x.pos = (x.pos[0] + horiz, x.pos[1] + vert)
        self.readSpot(self.analysisImage, self.currentSpot)
        self.scanBlankSpots(self.analysisImage, self.currentSpot)
        buttonStr = self.currentSpot.updateText()
        self.spotButtonText[self.currentSpot.idNo - 1] = buttonStr


    def readSpot(self, image, spot):
        spotSize = spot.instGrp.children[2].size[0]
        spotX = spot.instGrp.children[2].pos[0]
        spotY = spot.instGrp.children[2].pos[1]
        scaled_x = int((spotX - self.x) * (image.size[0] / float(self.width)))
        scaled_y = int((spotY - self.y) * (image.size[1] / float(self.height)))
        scaled_spotWidth = max(int(spotSize * (image.size[0] / float(self.width))), 1)
        scaled_spotHeight = max(int(spotSize * (image.size[1] / float(self.height))), 1)
        croppedImage = image.crop((scaled_x, scaled_y,
                                   scaled_x + scaled_spotWidth,
                                   scaled_y + scaled_spotHeight))
        color = imageStat(croppedImage).mean
        spot.colorVal = color
        spot.colorMode = image.mode


    def scanBlankSpots(self, image, spot, scanRange=30):
        scanRange = int(metrics.dp(scanRange))
        channelIndex = channelIndexFromName(self.app.measuredChannel)
        maxValList = []
        for i in [(5, -1, 0), (7, 0, 1), (9, 1, 0), (11, 0, -1)]:
            colorValsList = []
            spotSize = spot.instGrp.children[i[0]].size[0]
            scaled_spotWidth = max(int(spotSize * (image.size[0] / float(self.width))), 1)
            scaled_spotHeight = max(int(spotSize * (image.size[1] / float(self.height))), 1)
            # low res scan
            for j in range(0, scanRange, int(scanRange / 5)):
                spotX = spot.instGrp.children[i[0]].pos[0] + j * i[1]
                spotY = spot.instGrp.children[i[0]].pos[1] + j * i[2]
                scaled_x = int((spotX - self.x) * (image.size[0] / float(self.width)))
                scaled_y = int((spotY - self.y) * (image.size[1] / float(self.height)))
                croppedImage = image.crop((scaled_x, scaled_y,
                                           scaled_x + scaled_spotWidth,
                                           scaled_y + scaled_spotHeight))
                colorValsList.append((imageStat(croppedImage).mean[channelIndex], spotX, spotY))
            maxVal = max(colorValsList)
            print maxVal
            maxValList.append(maxVal[0])
            spot.instGrp.children[i[0]].pos = (maxVal[1], maxVal[2])

            # high res scan
            for j in range(6):
                spotX = spot.instGrp.children[i[0]].pos[0] - 3+ j * i[1]
                spotY = spot.instGrp.children[i[0]].pos[1] -3 + j * i[2]
                scaled_x = int((spotX - self.x) * (image.size[0] / float(self.width)))
                scaled_y = int((spotY - self.y) * (image.size[1] / float(self.height)))
                croppedImage = image.crop((scaled_x, scaled_y,
                                           scaled_x + scaled_spotWidth,
                                           scaled_y + scaled_spotHeight))
                colorValsList.append((imageStat(croppedImage).mean[channelIndex], spotX, spotY))
            maxVal = max(colorValsList)
            print maxVal
            maxValList.append(maxVal[0])
            spot.instGrp.children[i[0]].pos = (maxVal[1], maxVal[2])
        spot.blankVal = sum(maxValList) / len(maxValList)
        print 'ave blank', spot.blankVal


    def updateSpotConc(self, spot, conc):
        spot.conc = conc
        buttonStr = spot.updateText()
        self.spotButtonText[spot.idNo - 1] = buttonStr 


class CalibrationScreen(Widget):
    tex = ObjectProperty(None, allownone=True)


class SampleScreen(Widget):
    tex = ObjectProperty(None, allownone=True)
    sampleGrp = NumericProperty(1)


    def updateSpotGrps(self):
        print 'sample grp is {}'.format(self.sampleGrp)
        for spot in self.ids['colorReader'].spots:
            spot.sampleGrp = self.sampleGrp
