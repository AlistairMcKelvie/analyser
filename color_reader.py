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
    def __init__(self, idNo = None, type='Blank', conc=0):
        self.idNo = idNo
        self.sampleGrp = None
        self.type = type
        self.conc = conc
        # canvas instruction group
        self.instGrp = InstructionGroup()
        self.colorVal = None
        self.colorMode = None
        self.A = None


    def updateText(self):
        if self.type == 'Std' and self.conc is not None:
            typeText = 'Std ' + str(self.conc)
        elif self.type == 'Sample':
            typeText = 'Sample {0}-{1}'.format(self.sampleGrp, self.idNo)
        else:
            typeText = self.type
        if self.conc is not None:
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


class ColorReader(Widget):
    imageFile = StringProperty('')
    spotCount = NumericProperty(15)
    currentSpot = ObjectProperty(None)
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
        self.spots = [ColorReaderSpot(idNo=i+1) for i in range(self.spotCount)]
        for spot in self.spots:
            spot.instGrp.add(self.spotColor)
            self.canvas.add(spot.instGrp)
        self.analysisImage = None
        self.currentSpot = self.spots[0]
        

    def initialDraw(self):
        self.analysisImage = PILImage.open(self.imageFile)
        self.analysisImage = self.analysisImage.transpose(\
            PILImage.FLIP_TOP_BOTTOM)
        
        for spot in self.spots:
            spot.colorMode = self.analysisImage.mode
            self.readSpot(self.analysisImage, 
                          self.currentSpot,
                          self.currentSpotType,
                          self.currentSpotConc)
            buttonStr = spot.updateText()
            if buttonStr is not None:
                self.spotButtonText[spot.idNo] = buttonStr

 
    def updateSpotSize(self, spotSize):
        try:
            self.currentSpotSize = int(spotSize)
        except ValueError:
            pass


    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_down'
            self.currentSpot.instGrp.clear()
            size = self.currentSpotSize
            print size
            self.currentSpot.instGrp.add(self.spotColor)
            touch.ud['Rectangle'] = Rectangle(pos=(touch.x - size / 2,
                                                   touch.y - size / 2),
                                              size=(size, size))
            self.currentSpot.instGrp.add(touch.ud['Rectangle'])


    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_move'
            size = self.currentSpotSize
            self.currentSpot.instGrp.clear()
            touch.ud['Rectangle'].pos = (touch.x - size / 2, touch.y - size / 2)
            self.currentSpot.instGrp.add(self.spotColor)
            self.currentSpot.instGrp.add(touch.ud['Rectangle'])

 
    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            print 'called on_touch_up'
            self.readSpot(self.analysisImage, 
                          self.currentSpot,
                          self.currentSpotType,
                          self.currentSpotConc)
            buttonStr = self.currentSpot.updateText()

            if buttonStr is not None:
                self.spotButtonText[self.currentSpot.idNo - 1] = buttonStr

 
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
        assert (self.currentSpot.instGrp.childern) == 3
        pos = self.currentSpot.instGrp.children[2].pos
        self.currentSpot.instGrp.children[2].pos = (pos[0] + horiz,
                                                    pos[1] + vert)
        self.readSpot(self.analysisImage, 
                      self.currentSpot,
                      self.currentSpotType,
                      self.currentSpotConc)


    def readSpot(self, image, spot, currentSpotType, currentSpotConc):
        image = self.analysisImage
        spot.type = currentSpotType
        spot.conc = currentSpotConc
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
 

class CalibrationScreen(Widget):
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
                self.ids['colorReader'].currentSpot.conc = float(text)
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


class SampleScreen(Widget):
    pass
