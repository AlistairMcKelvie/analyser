import kivy

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics import Color
from kivy.properties import StringProperty
from kivy.lang import Builder
from kivy import platform
from plyer import camera

from PIL import Image as PILImage

import os
import os.path
import csv
import math
from collections import namedtuple

from myGraph import MyGraph
from color_reader import ColorReaderSpot,\
                         ColorReader,\
                         CalibrationScreen,\
                         SampleScreen
from sendGmail import sendMail
from datetime import datetime


class MainMenuScreen(BoxLayout):
    pass


class ImageMenuScreen(BoxLayout):
    pass


class GraphScreen(Widget):
    pass


class FileChooserScreen(Widget):
    pass


class CalibChooserScreen(Widget):
    pass


class Main(App):
    measuredChannel = StringProperty('red')
    targetReaderScreen = StringProperty('')
    stdsFile = StringProperty('')
    calibFile = StringProperty('')

    def build(self):
        '''Runs when app starts'''
        self.mainMenuScreen = MainMenuScreen()
        self.imageMenuScreen = ImageMenuScreen()
        self.graphScreen = GraphScreen()
        Builder.load_file('color_reader.kv')
        self.calibrationScreen = CalibrationScreen()
        self.sampleScreen = SampleScreen()
        self.fileChooserScreen = FileChooserScreen()
        self.calibChooserScreen = CalibChooserScreen()

        self.initializeCalibSpots()
        self.initializeSampleSpots()
        self.firstSample = True
        return self.mainMenuScreen
    

    def goto_main_menu(self):
        self.clearAllWidgets()
        Window.add_widget(self.mainMenuScreen)


    def goto_image_menu(self):
        print 'self.directory', self.directory
        print 'self.user_data_dir', self.user_data_dir
        print 'os.getcwd', os.getcwd()
        self.clearAllWidgets()
        Window.add_widget(self.imageMenuScreen)


    def goto_get_stock_image(self):
        self.fileChooserScreen.ids['fileChooser'].path =\
            os.getcwd() + '/stock_images'
        self.clearAllWidgets()
        Window.add_widget(self.fileChooserScreen)


    def goto_get_old_calib(self):
        self.calibChooserScreen.ids['calibChooser'].path =\
            self.user_data_dir
        print self.calibChooserScreen.ids['calibChooser'].path
        self.clearAllWidgets()
        Window.add_widget(self.calibChooserScreen)


    def goto_color_reader_screen(self, imageFile):
        print 'in color reader'
        assert '.jpg' in imageFile or '.png' in imageFile,\
            imageFile + ' not a valid image file, must be jpg or png'
        assert (self.targetReaderScreen == 'calib' or
                self.targetReaderScreen == 'sample'),\
            'targetReaderScreen is set to {}, this is not valid option.'\
            .format(self.targetReaderScreen)
        if self.targetReaderScreen == 'calib':
            readerScreen = self.calibrationScreen
        elif self.targetReaderScreen == 'sample':
            readerScreen = self.sampleScreen
        reader = readerScreen.ids['colorReader']
        
        self.clearAllWidgets()
        Window.add_widget(readerScreen)

        # color reader initialization
        readerScreen.canvas.before.clear()
        #reader.imageFile = imageFile
        print 'canvas', readerScreen.canvas.children
        print 'canvas.before', readerScreen.canvas.before.children
        #resize image file so it can be displayed
        tempDir = self.create_temp_dir()
        print 'resizing image'
        print 'window size:', Window.size
        print 'drawing image to screen:', imageFile
        reader.imageFile = imageFile
        #imageFile = os.getcwd() + '/stock_images/rgb.png'
        #import ipdb;ipdb.set_trace()
        print 'window width', Window.width
        print 'window height', Window.height
        #readerScreen.width = Window.width
        #readerScreen.height = Window.height
        print 'reader width', readerScreen.width
        print 'reader height', readerScreen.height
        readerScreen.canvas.before.clear()
        print 'before draw', readerScreen.canvas.before.children
        #print resizedImage
        # try just adding instruction here?
        print os.listdir(os.getcwd())
        from kivy.core.image import Image
        self.calibrationScreen.tex = Image(imageFile).texture
        '''
        readerScreen.canvas.before.add(Rectangle(#source=resizedImage,
                      texture=tex,
                      size=(readerScreen.width * 0.8,
                            readerScreen.height * 0.85),
                      pos=(readerScreen.width * 0.2,
                           readerScreen.height * 0.15)))
        '''
        print 'after draw', readerScreen.canvas.before.children
        print 'canvas info:'
        #rect = readerScreen.canvas.before.children[-1]
        #print 'pos', rect.pos
        #print 'source', rect.source
        #print 'tex', rect.texture
        #print 'needs redraw', rect.needs_redraw
        reader.initialDraw()

    
    def create_temp_dir(self):
        tempDir = os.getcwd() + '/temp'
        try:
            os.mkdir(tempDir)
        except Exception:
            pass
        return tempDir


    def resize_image(self, imageFile, writeDir):
        basewidth = 800
        img = PILImage.open(imageFile)
        print 'original image size', img.size
        wpercent = basewidth / float(img.size[0])
        hsize = int(float(img.size[1]) * float(wpercent))
        img = img.resize((basewidth, hsize), PILImage.ANTIALIAS)
        savedFile = writeDir + 'resized_' + os.path.basename(imageFile)
        img.save(savedFile)
        print 'resize image size', img.size
        del img
        return savedFile


    def goto_graph(self):
        colorReader = self.colorReaderScreen.ids['colorReader']
        if [i.type for i in colorReader.spots].count('Blank') == 0:
            print 'No blank!'
        else:
            self.graphScreen.ids['graph'].updateGraph(
                    [spot.conc for spot in colorReader.spots],
                    [spot.colorVal for spot in colorReader.spots])
        self.clearAllWidgets()
        Window.add_widget(self.graphScreen)


    def initializeCalibSpots(self):
        reader = self.calibrationScreen.ids['colorReader']
        for spot in reader.spots:
            spotType = self.config.get('SpotTypes', str(spot.idNo))
            if spotType != 'None':
                spot.type = spotType
            spotConc = self.config.get('SpotConcentrations', str(spot.idNo))
            if spotConc != 'None' and spotConc != 'Blank':
                spot.conc = float(spotConc)
            spotSize = self.config.get('SpotSizes', str(spot.idNo))
            spotX = self.config.get('SpotX', str(spot.idNo))
            spotY = self.config.get('SpotY', str(spot.idNo))
            print 'spot size', spotSize
            print 'spot x', spotX
            print 'spot y', spotY
            if spotSize != 'None':
                spot.instGrp.add(Rectangle(size=(float(spotSize),
                                                 float(spotSize)),
                                           pos=(float(spotX),
                                                float(spotY))))


    def initializeSampleSpots(self):
        reader = self.sampleScreen.ids['colorReader']
        reader.currentSpotType = 'Sample'
        for spot in reader.spots:
            spot.sampleGrp = 1
            spot.type = 'Sample'
            spot.conc = None
            spot.colorVal = None
            spotSize = self.config.get('SpotSizes', str(spot.idNo))
            spotX = self.config.get('SpotX', str(spot.idNo))
            spotY = self.config.get('SpotY', str(spot.idNo))
            if spotSize != 'None':
                spot.instGrp.add(Rectangle(size=(float(spotSize),
                                                  float(spotSize)),
                                            pos=(float(spotX),
                                                 float(spotY))))


    def clearSampleSpots(self):
        sampleGrp = self.sampleScreen.ids['colorReader'].spots[0].sampleGrp + 1
        for spot in self.sampleScreen.ids['colorReader'].spots:
            spot.sampleGrp = sampleGrp


    def writeSpotsToConfig(self):
        colorReader = self.colorReaderScreen.ids['colorReader']
        for i in range(self.spotCount):
            self.config.set('SpotTypes', str(i), colorReader.spots[i].type)
            self.config.set('SpotConcentrations', str(i), colorReader.spots[i].conc)
            graphicsInstructs = colorReader.spots[i].instGrp.children
            if len(graphicsInstructs) == 3:
                self.config.set('SpotSizes', str(i), int(graphicsInstructs[2].size[0]))
                self.config.set('SpotX', str(i), int(graphicsInstructs[2].pos[0]))
                self.config.set('SpotY', str(i), int(graphicsInstructs[2].pos[1]))
        self.config.write()


    def build_config(self, config):
        config.setdefaults('defaults', {'spotCount': 15})
        config.setdefaults('defaults', {'spotSize': 10})
        self.spotCount = int(config.get('defaults', 'spotCount'))
        self.defaultSpotSize = int(config.get('defaults', 'spotSize')) 
        noneDict = {}
        for i in range(1, self.spotCount + 1):
            noneDict[str(i)] = None
        config.setdefaults('SpotTypes', noneDict)
        config.setdefaults('SpotConcentrations', noneDict)
        config.setdefaults('SpotSizes', noneDict)
        config.setdefaults('SpotX', noneDict)
        config.setdefaults('SpotY', noneDict)
 

    def sendEmail(self):
        self.calibrationScreen.canvas.ask_update()
        sendMail(['alistair.mckelvie@gmail.com'],
                 'Spot analyser files from {}'.format(self.writeDir.split('/')[-2].split('\\')[-1]),
                 'Spot analyser files from {}'.format(self.writeDir.split('/')[-2].split('\\')[-1]),
                 self.writeDir)
    

    def clearAllWidgets(self):
        for widget in Window.children:
            Window.remove_widget(widget)


    def take_photo(self, fileType, sampleGrp=None):
        print 'canvas', self.calibrationScreen.canvas.children
        print 'canvas.before', self.calibrationScreen.canvas.before.children
        assert fileType == 'calib' or fileType == 'sample'
        if fileType == 'calib':
            filepath = self.writeDir + 'calib.jpg'
        else:
            t
            filepath = self.writeDir + 'sample_{}.jpg'.format(sampleGrp)
        self.cameraFile = filepath
        try:
            print 'taking picture'
            camera.take_picture(filepath, self.camera_callback)
        except NotImplementedError:
            popup = MsgPopup(msg="This feature has not yet been "
                                 "implemented for this platform.")
            popup.open()

    def camera_callback(self, imageFile):
        print 'imagefile:', imageFile
        print 'got camera callback'
        print 'writedir:', self.writeDir
        resizedImage = self.resize_image(imageFile, self.writeDir)
        print 'resized image', resizedImage
        self.clearAllWidgets()
        #self.goto_color_reader_screen(resizedImage)
        self.fileChooserScreen.ids['fileChooser'].path = self.writeDir
        Window.add_widget(self.fileChooserScreen)


    def on_pause(self):
        print 'pausing'
        return True


    def on_resume(self):
        print 'on resume called'
   

    def writeRawData(self, calib, rawFile, spots, firstWrite=False):
        fieldNames = ['type', 'sample_group', 'sample_no',
                      'known_concentration', 'calculated_concentration',
                      'red','green', 'blue', 'alpha', 'measured_channel']
        if firstWrite:
            with open(rawFile, 'wb') as sFile:
                csvWriter = csv.DictWriter(sFile, fieldnames=fieldNames)
                csvWriter.writeheader()
        with open(rawFile, 'ab') as sFile:
            csvWriter = csv.DictWriter(sFile, fieldnames=fieldNames)
            for spot in spots:
                if spot.type == 'Blank' or spot.type == 'Std':
                    type = 'Standard'
                    conc = spot.conc
                    sample_group = ''
                    sample_no = ''
                elif spot.type == 'Sample':
                    type = 'Sample'
                    conc = ''
                    sample_group = spot.sampleGrp
                    sample_no = spot.idNo
                calculatedConc = self.calculateConc(calib, spot.colorVal)
                if spot.colorMode == 'RGBA':
                    alpha = '{:.3f}'.format(spot.colorVal[3])
                else:
                    alpha = ''
                csvWriter.writerow(
                    {'type': type,
                     'sample_group': sample_group,
                     'sample_no': sample_no,
                     'known_concentration': conc,
                     'red': '{:.3f}'.format(spot.colorVal[0]),
                     'green': '{:.3f}'.format(spot.colorVal[1]),
                     'blue': '{:.3f}'.format(spot.colorVal[2]),
                     'alpha': alpha,
                     'measured_channel': self.measuredChannel,
                     'calculated_concentration': '{:.3f}'.format(calculatedConc)})


    def calculateConc(self, calib, colorVal):
       val = colorVal[self.channelIndexFromName(calib.channel)]
       A = math.log10(val) / calib.blank
       return (A - calib.C) / calib.M


    def writeSamplesFile(self, calib, samplesFile, spots, firstWrite=False):
        fieldNames = ['sample_group', 'calculated_concentration']
        if firstWrite:
            with open(samplesFile, 'wb') as f:
                csvWriter = csv.DictWriter(f, fieldNames)
                csvWriter.writeheader()
        concSum = 0
        sampleGrp = None
        for spot in spots:
            assert sampleGrp is None or spot.sampleGrp == sampleGrp
            concSum += self.calculateConc(calib, spot.colorVal)
            sampleGrp = spot.sampleGrp
        concMean = concSum / float(len(spots))
        with open(samplesFile, 'ab') as f:
            csvWriter = csv.DictWriter(f, fieldNames)
            csvWriter.writerow({'sample_group': sampleGrp,
                                'calculated_concentration': concMean})


    def writeCalibFile(self, calibFile, calib):
        with open(calibFile, 'wb') as f:
            f.write('M: {}\n'.format(calib.M))
            f.write('C: {}\n'.format(calib.C))
            f.write('R2: {}\n'.format(calib.R2))
            f.write('Blank: {}\n'.format(calib.blank))
            f.write('Measured Channel: {}\n'.format(calib.channel))            


    def readCalibFile(self, calibFile):
        with open(calibFile, 'r') as f:
            M = f.next().split()[1]
            C = f.next().split()[1]
            R2 = f.next().split()[1]
            blank = f.next().split()[1]
            measuredChannel = f.next().split()[1]
        Calib = namedtuple('CalibCurve', ['M', 'C', 'R2', 'blank', 'channel'])
        return Calib(M=M, C=C, R2=R2, blank=blank, channel=measuredChannel)


    def calculateACalibCurve(self, spots):
        calibPoints = []
        channelIndex = self.channelIndexFromName(self.measuredChannel)
        colorValSumDict = {}
        colorValCountDict = {}
        colorValAverageDict = {}
        print '============'
        for i in range(self.spotCount):
            print spots[i].conc
            print spots[i].colorVal[channelIndex]
            try:
                colorValSumDict[spots[i].conc] += spots[i].colorVal[channelIndex]
            except KeyError:
                colorValSumDict[spots[i].conc] = spots[i].colorVal[channelIndex]
            try:
                colorValCountDict[spots[i].conc] += 1
            except KeyError:
                colorValCountDict[spots[i].conc] = 1
        for x in colorValSumDict:
            colorValAverageDict[x] = colorValSumDict[x] / colorValCountDict[x]
        print colorValSumDict
        print colorValCountDict
        print colorValAverageDict

        blankVal = colorValAverageDict.pop(0)
        calibPoints.append((0, 0))
        for key in colorValAverageDict:
            calibPoints.append((key, -math.log10(colorValAverageDict[key] / blankVal)))
        print calibPoints

        # Make calibration curve
        N = len(calibPoints)
        if N >= 2:
            # Calculate least squareds reg
            print 'N', N
            sumX = sum([x for x, y in calibPoints])
            print 'sumX', sumX
            sumY = sum([y for x, y in calibPoints])
            print 'sumY', sumY
            sumXY = sum([x * y for x, y in calibPoints])
            print 'sumXY', sumXY
            sumXX = sum([x * x for x, y in calibPoints])
            print 'sumXX', sumXX

            M = (N * sumXY - sumX * sumY) / (N * sumXX - sumX**2)
            print 'M', M
 
            C = (sumY - M * sumX) / N
            print 'C', C
            print 'y = {M}x + {C}'.format(M=M, C=C)

            # Calculate R2
            SSres = sum([(y - (x * M + C))**2 for x, y in calibPoints])
            print 'SSres', SSres
            meanY = sum([y for x, y in calibPoints]) / len(calibPoints)
            print 'meanY', meanY
            SStot = sum([(y - meanY)**2 for x, y in calibPoints])
            print 'SStot', SStot
            R2 = 1 - SSres / SStot
            print 'R2 = {:.5f}'.format(R2)
            Calib = namedtuple('CalibCurve', ['M', 'C', 'R2',
                               'blank', 'channel'])
            return Calib(M=M, C=C, R2=R2, blank=blankVal,
                         channel=self.measuredChannel)


    def channelIndexFromName(self, measuredChannel):
        if measuredChannel == 'red':
            return 0
        if measuredChannel == 'green':
            return 1
        if measuredChannel == 'blue':
            return 2
        raise RuntimeError('{} is not a valid channel '
                           'name.'.format(measuredChannel))


    def create_new_data_set(self):
        setDataDir = '{0}/{1:%Y%m%d_%H%M}/'.format(self.user_data_dir,
                                                  datetime.now())
        # TODO handle data error if dir already exists
        try:
            os.mkdir(setDataDir)
        except OSError:
            setDataDir = setDataDir[:-1] + '_2/'
            os.mkdir(setDataDir)
        return setDataDir


class MsgPopup(Popup):
    def __init__(self, msg):
        super(MsgPopup, self).__init__()

        self.ids.message_label.text = msg


if __name__ == '__main__':
    Main().run()

