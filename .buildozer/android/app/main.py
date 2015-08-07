import kivy

from kivy.app import App
from kivy.core.window import Window
from kivy.core.image import Image
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
    calcLog = StringProperty('')
    qConfCSV = StringProperty('')

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
        self.qConfCSV = 'Q_Crit_Vals.csv'
        print 'listing dir'
        self.listall(os.getcwd())
        return self.mainMenuScreen
    
    def listall(self, dir):
        for x in os.listdir(dir):
            if os.path.isfile(dir + '/' + x):
                print dir + '/' + x
            elif os.path.isdir(dir + '/' + x):
                self.listall(dir + '/' + x)


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
        tempDir = self.create_temp_dir()
        reader.imageFile = imageFile
        readerScreen.tex = Image(imageFile).texture
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
        img = img.resize((basewidth, hsize))
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
            if spotConc != 'None':
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
        self.sampleScreen.updateSpotGrps()
        for spot in reader.spots:
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


    def writeSpotsToConfig(self):
        if self.targetReaderScreen == 'sample':
            spots = self.sampleScreen.ids['colorReader'].spots
        else:
            spots = self.calibrationScreen.ids['colorReader'].spots
        for spot in spots:
            if spot.type == 'Std' or spot.type == 'Blank':
                self.config.set('SpotTypes', str(spot.idNo), spot.type)
                self.config.set('SpotConcentrations', str(spot.idNo), spot.conc)
            graphicsInstructs = spot.instGrp.children
            if len(graphicsInstructs) == 3:
                self.config.set('SpotSizes', str(spot.idNo), int(graphicsInstructs[2].size[0]))
                self.config.set('SpotX', str(spot.idNo), int(graphicsInstructs[2].pos[0]))
                self.config.set('SpotY', str(spot.idNo), int(graphicsInstructs[2].pos[1]))
        self.config.write()


    def build_config(self, config):
        config.setdefaults('kivy', {'log_dir': self.user_data_dir})
        config.setdefaults('defaults', {'spotCount': 15, 'spotSize': 10})
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
                 ('Spot analyser files from {}'
                  ).format(self.writeDir.split('/')[-2].split('\\')[-1]),
                 ('Spot analyser files from {}'
                  ).format(self.writeDir.split('/')[-2].split('\\')[-1]),
                 self.writeDir)
    

    def clearAllWidgets(self):
        for widget in Window.children:
            Window.remove_widget(widget)


    def take_photo(self, fileType, sampleGrp=None):
        print 'canvas', self.calibrationScreen.canvas.children
        print 'canvas.before', self.calibrationScreen.canvas.before.children
        assert fileType == 'calib' or fileType == 'sample'
        print 'fileType', fileType
        if fileType == 'calib':
            filepath = self.writeDir + 'calib.jpg'
        else:
            filepath = self.writeDir + 'sample_{}.jpg'.format(sampleGrp)
        self.cameraFile = filepath
        print 'c filePath', filepath
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

