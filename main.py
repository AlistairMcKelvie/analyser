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
from color_reader import ColorReaderSpot, ColorReader, ColorReaderScreen
from sendGmail import sendMail

class MainMenuScreen(BoxLayout):
    pass


class ImageMenuScreen(BoxLayout):
    pass


class GraphScreen(Widget):
    pass


class FileChooserScreen(Widget):
    pass


class Main(App):
    currentSampleSet = StringProperty('')
    measuredChannel = StringProperty('red')
    def build(self):
        self.mainMenuScreen = MainMenuScreen()
        self.imageMenuScreen = ImageMenuScreen()
        self.graphScreen = GraphScreen()
        Builder.load_file('color_reader.kv')
        self.colorReaderScreen = ColorReaderScreen()
        self.fileChooserScreen = FileChooserScreen()
        return self.mainMenuScreen
    
    
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


    def goto_color_reader(self, imageFile=None):
        colorReader = self.colorReaderScreen.ids['colorReader']
        self.clearAllWidgets()
        Window.add_widget(self.colorReaderScreen)
        # color reader initialization
        self.imageFile = imageFile
        if imageFile is not None:
            self.colorReaderScreen.ids['colorReader'].imageFile = imageFile
            self.colorReaderScreen.canvas.before.clear()
            with self.colorReaderScreen.canvas.before:
                Rectangle(source=self.imageFile,
                          size=(self.colorReaderScreen.width * 0.8,
                                self.colorReaderScreen.height * 0.85),
                          pos=(self.colorReaderScreen.width * 0.2,
                               self.colorReaderScreen.height * 0.15))
        colorReader.initialDraw()
        colorReader.initialImageAndDrawDone = True


    def goto_graph(self):
        colorReader = self.colorReaderScreen.ids['colorReader']
        if [i.type for i in colorReader.spots].count('Blank') == 0:
            print 'No blank!'
        else:
            self.graphScreen.ids['graph'].updateGraph(
                    [spot.conc for spot in colorReader.spots],
                    [spot.colorVal for spot in colorReader.spots] )
        self.clearAllWidgets()
        Window.add_widget(self.graphScreen)


    def readSpotsFromConfig(self):
        colorReader = self.colorReaderScreen.ids['colorReader']
        for i in range(self.spotCount):
            spotType = self.config.get('SpotTypes', str(i))
            if spotType != 'None':
                colorReader.spots[i].type = spotType

            spotConc = self.config.get('SpotConcentrations', str(i))
            if spotConc != 'None' and spotConc != 'Blank':
                    colorReader.spots[i].conc = float(spotConc)

            spotVal = self.config.get('SpotValues', str(i))
            if spotVal != 'None':
                colorReader.spots[i].colorVal = [float(j) for j in \
                                                 spotVal[1:-1].split(',')]
            
            spotSize = self.config.get('SpotSizes', str(i))
            spotX = self.config.get('SpotX', str(i))
            spotY = self.config.get('SpotY', str(i))
            print 'spot size', spotSize
            print 'spot x', spotX
            print 'spot y', spotY
            if spotSize != 'None':
                colorReader.spots[i].instGrp.add(
                        Rectangle(size=(float(spotSize), float(spotSize)),
                                                           pos=(float(spotX),
                                                               float(spotY))))


    def writeSpotsToConfig(self):
        colorReader = self.colorReaderScreen.ids['colorReader']
        for i in range(self.spotCount):
            self.config.set('SpotTypes', str(i), colorReader.spots[i].type)
            self.config.set('SpotConcentrations', str(i), colorReader.spots[i].conc)
            self.config.set('SpotValues', str(i), colorReader.spots[i].colorVal)
            graphicsInstructs = colorReader.spots[i].instGrp.children
            if len(graphicsInstructs) == 3:
                self.config.set('SpotSizes', str(i), int(graphicsInstructs[2].size[0]))
                self.config.set('SpotX', str(i), int(graphicsInstructs[2].pos[0]))
                self.config.set('SpotY', str(i), int(graphicsInstructs[2].pos[1]))
        self.config.write()


    def build_config(self, config):
        config.setdefaults('SpotCount', {'spotCount': 15})
        self.spotCount = int(config.get('SpotCount', 'spotCount'))
        noneDict = {}
        for i in range(self.spotCount):
            noneDict[str(i)] = None
        config.setdefaults('SpotTypes', noneDict)
        config.setdefaults('SpotConcentrations', noneDict)
        config.setdefaults('SpotValues', noneDict)
        config.setdefaults('SpotSizes', noneDict)
        config.setdefaults('SpotX', noneDict)
        config.setdefaults('SpotY', noneDict)
 

    def sendEmail(self):
        sendMail(['alistair.mckelvie@gmail.com'], 'test', 'test')
    

    def clearAllWidgets(self):
        for widget in Window.children:
            Window.remove_widget(widget)


    def take_photo(self):
        try:
            filepath = self.user_data_dir + '/test.jpg'
            fp=filepath
            camera.take_picture(filename=filepath, 
                                on_complete=self.camera_callback())
        except NotImplementedError:
            popup = MsgPopup(msg="This feature has not yet been "
                                 "implemented for this platform.")
            popup.open()


    def camera_callback(self):
        print 'got to camera callback'


    def writeStdsAndGetNewImage(self):
        if self.currentSampleSet == 'calibration':
            self.calib = self.calculateACalibCurve()
            openMode = 'w'
        else:
            openMode = 'a'
        channelIndex = self.channelIndexFromName()
        spots = self.colorReaderScreen.ids['colorReader'].spots
        stdsFile = self.user_data_dir + '/stds.csv'
        print stdsFile
        fieldNames = ['sample_set', 'known_concentration', 'red', 'green', 'blue',
                      'measured_channel', 'A', 'calculated_concentration']
        with open(stdsFile, openMode) as sFile:
            csvWriter = csv.DictWriter(sFile, fieldnames=fieldNames)
            if self.currentSampleSet == 'calibration':
                csvWriter.writeheader()
            for i in range(self.spotCount):
                alpha = -math.log10(spots[i].colorVal[channelIndex] /
                                    self.calib.blank)
                calculatedConc = (alpha - self.calib.C) / self.calib.M
                if self.currentSampleSet == 'calibration':
                    conc = spots[i].conc
                else:
                    conc = ''
                csvWriter.writerow(
                    {'sample_set': self.currentSampleSet, 
                     'known_concentration': conc,
                     'red': '{:.3f}'.format(spots[i].colorVal[0]),
                     'green': '{:.3f}'.format(spots[i].colorVal[1]),
                     'blue': '{:.3f}'.format(spots[i].colorVal[2]),
                     'measured_channel': self.measuredChannel,
                     'A': '{:.3f}'.format(alpha),
                     'calculated_concentration': '{:.3f}'.format(calculatedConc)})
        if self.currentSampleSet == 'calibration':
            self.currentSampleSet = '1'
        else:
            self.currentSampleSet = str(int(self.currentSampleSet) + 1)
        self.goto_image_menu()
       

    def calculateACalibCurve(self):
        self.writeSpotsToConfig()
        spots = self.colorReaderScreen.ids['colorReader'].spots
        calibPoints = []
        channelIndex = self.channelIndexFromName()
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
            Calib = namedtuple('CalibCurve', ['M', 'C', 'R2', 'blank'])
            return Calib(M=M, C=C, R2=R2, blank=blankVal)
            
        
    def channelIndexFromName(self):
        if self.measuredChannel == 'red':
            return 0
        if self.measuredChannel == 'green':
            return 1
        if self.measuredChannel == 'blue':
            return 2
        raise RuntimeError('{} is not a valid channel name.'.format(self.measuredChannel))


class MsgPopup(Popup):
    def __init__(self, msg):
        super(MsgPopup, self).__init__()

        self.ids.message_label.text = msg


if __name__ == '__main__':
    Main().run()

