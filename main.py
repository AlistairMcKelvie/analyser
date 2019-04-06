import kivy

from kivy.app import App
from kivy.core.window import Window
from kivy.core.image import Image

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.label import Label

from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics import Color
from kivy.properties import StringProperty, OptionProperty, ListProperty
from kivy.lang import Builder
from kivy import platform
from kivy.clock import Clock
from plyer import camera
import kivy.metrics as metrics

from PIL import Image as PILImage

import os
import csv
from collections import namedtuple

from color_reader import ColorReaderSpot,\
                         ColorReader,\
                         CalibrationScreen,\
                         SampleScreen
from analyser_display import CalibResultsScreen,\
                             SampleResultsScreen
from analyser_util import channelIndexFromName 
from sendGmail import sendMail
from datetime import datetime
import shutil


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

def select_calib(app, calibChooser):
    if os.path.exists(calibChooser.selection[0]) and os.path.isfile(calibChooser.selection[0]):
        app.calib = app.readCalibFile(calibChooser.selection[0])
        app.writeDir = os.path.dirname(calibChooser.selection[0]) + '/'
        app.rawFile = app.writeDir + 'raw.csv'
        app.calibFile = app.writeDir + 'calib.txt'
        app.samplesFile = app.writeDir + 'samples.csv' 
        app.calcLog = app.writeDir + 'calc_log.txt' 
        app.goto_image_menu()


class AnalyserApp(App):
    measuredChannel = OptionProperty('Red', options=['Red', 'Green', 'Blue'])
    calibSpots = ListProperty([])
    targetReaderScreen = StringProperty('')
    stdsFile = StringProperty('')
    calibFile = StringProperty('')
    calcLog = StringProperty('')
    qConfCSV = StringProperty('')

    def build(self):
        '''Runs when app starts'''
        self.mainMenuScreen = MainMenuScreen()
        self.imageMenuScreen = ImageMenuScreen()
        self.fileChooserScreen = FileChooserScreen()
        self.calibChooserScreen = CalibChooserScreen()
        
        Builder.load_file('color_reader.kv')
        self.calibrationScreen = CalibrationScreen()
        self.sampleScreen = SampleScreen()
        
        Builder.load_file('analyser_display.kv')
        self.calibResultsScreen = CalibResultsScreen()
        self.sampleResultsScreen = SampleResultsScreen()

        self.initializeCalib()
        self.initializeSample()
        self.firstSample = True
        self.firstRaw = True
        self.calibNo = 0
        self.qConfCSV = 'Q_Crit_Vals.csv'
        self.measuredChannel = self.config.get('technical', 'measuredChannel')
        return self.mainMenuScreen
    

    def goto_main_menu(self):
        self.clearAllWidgets()
        Window.add_widget(self.mainMenuScreen)


    def goto_calib_results(self):
        valuesTable = self.calibResultsScreen.ids['valuesTable']
        calibGraph = self.calibResultsScreen.ids['calibGraph']
        calibGraph.drawSpots(self.calibSpots)
        if self.calib is not None:
            calibGraph.drawCurve(self.calib)
        colorIndex = channelIndexFromName(self.measuredChannel) 
        valuesTable.clear_widgets()
        for spot in self.calibSpots:
            row = BoxLayout()
            valuesTable.add_widget(row)
            row.add_widget(Label(text=str(spot.idNo), font_size=metrics.dp(15)))
            row.add_widget(Label(text=str(spot.conc), font_size=metrics.dp(15)))
            row.add_widget(Label(text=str(int(round(spot.colorVal[colorIndex]))),
                                font_size=metrics.dp(15)))
            row.add_widget(Label(text=str(int(round(spot.blankVal))),
                                font_size=metrics.dp(15)))
            row.add_widget(Label(text='{:.3f}'.format(spot.alpha),
                                 font_size=metrics.dp(15)))
        valuesTable.height = len(self.calibSpots) * metrics.dp(20)
        
        if self.calib is None:
            calibEqn = u'Not enough calibration points to calculate equation.'
        else:
            calibEqn = (u'Concentration = {0:.3f}\u03b1 + {1:.3f}      R\u00b2 = {2:.4f}'
                        ).format(self.calib.M, self.calib.C, self.calib.R2)
        self.calibResultsScreen.ids['calibEqn'].text = calibEqn 

        self.clearAllWidgets()
        Window.add_widget(self.calibResultsScreen)


    def goto_sample_results(self, spots, conc):
        valuesTable = self.sampleResultsScreen.ids['valuesTable']
        colorIndex  = channelIndexFromName(self.measuredChannel)
        valuesTable.clear_widgets()
        for spot in spots:
            row = BoxLayout()
            valuesTable.add_widget(row)
            row.add_widget(Label(text=str(spot.idNo), font_size=metrics.dp(15)))
            row.add_widget(Label(text=str(int(round(spot.colorVal[colorIndex]))),
                                 font_size=metrics.dp(15)))
            row.add_widget(Label(text='{:.3f}'.format(spot.alpha),
                                 font_size=metrics.dp(15)))
        valuesTable.height = len(spots) * metrics.dp(20)
        
        self.sampleResultsScreen.ids['calcConc'].text =\
            'Calculated Concentration: {:.3f}'.format(conc)
        self.clearAllWidgets()
        Window.add_widget(self.sampleResultsScreen)


    def goto_image_menu(self):
        if self.targetReaderScreen == 'calib':
            self.calibNo += 1
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

        # color reader initialization
        reader.imageFile = imageFile
        tex = Image(imageFile).texture
        self.addTextureAndResizeColorReader(tex, readerScreen)
        self.clearAllWidgets()
        Window.add_widget(readerScreen)
        reader.initialDraw()


    def addTextureAndResizeColorReader(self, tex, readerScreen):
        windowSize = Window.size
        print 'windowSize', windowSize
        windowRatio = windowSize[0] / float(windowSize[1])
        print 'windowRatio', windowRatio
        texSize = tex.size
        print 'texSize', tex.size
        texRatio = texSize[0] / float(texSize[1])
        print 'texRatio', texRatio
        
        if texRatio > windowRatio:
            #texture is width constrained
            width = windowSize[0] * 0.8
            height = width / texRatio
            x = windowSize[0] * 0.2
            y = windowSize[1] * 0.2 + (windowSize[1] * 0.8 - height) / 2 
        else:
            #texture is height constrained
            height = windowSize[1] * 0.8
            width = height * texRatio
            x = windowSize[0] * 0.2 + (windowSize[0] * 0.8 - width) / 2
            y = windowSize[1] * 0.2

        #size and position texture
        for inst in readerScreen.canvas.children:
            if str(type(inst)) == "<type 'kivy.graphics.vertex_instructions.Rectangle'>":
                inst.size = (width, height)
                inst.pos = (x,y)
                inst.texture = tex

        #size and position color reader
        colorReader = readerScreen.ids['colorReader']
        colorReader.width = width
        colorReader.height = height
        colorReader.x = x
        colorReader.y = y
        

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


    def initializeCalib(self):
        reader = self.calibrationScreen.ids['colorReader']
        reader.currentSpotSize = int(self.config.get('technical', 'spotSize'))
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
            if spotSize != 'None':
                spot.addMainSpot(float(spotSize), float(spotX), float(spotY))
                spot.addBlankSpots()


    def initializeSample(self):
        reader = self.sampleScreen.ids['colorReader']
        reader.currentSpotSize = int(self.config.get('technical', 'spotSize'))
        self.sampleScreen.updateSpotGrps()
        for spot in reader.spots:
            spot.type = 'sample'
            spot.conc = None
            spot.colorVal = None
            spotSize = self.config.get('SpotSizes', str(spot.idNo))
            spotX = self.config.get('SpotX', str(spot.idNo))
            spotY = self.config.get('SpotY', str(spot.idNo))
            if spotSize != 'None':
                spot.addMainSpot(float(spotSize), float(spotX), float(spotY))
                spot.addBlankSpots()


    def writeSpotsToConfig(self):
        print 'writing to config'
        if self.targetReaderScreen == 'sample':
            spots = self.sampleScreen.ids['colorReader'].spots
        else:
            spots = self.calibrationScreen.ids['colorReader'].spots
        for spot in spots:
            if spot.type == 'std':
                self.config.set('SpotTypes',
                                str(spot.idNo), spot.type)
                self.config.set('SpotConcentrations',
                                str(spot.idNo), spot.conc)
            graphicsInstructs = spot.instGrp.children
            if len(graphicsInstructs) == 3 or 11:
                self.config.set('SpotSizes', str(spot.idNo),
                                int(graphicsInstructs[2].size[0]))
                self.config.set('SpotX', str(spot.idNo),
                                int(graphicsInstructs[2].pos[0]))
                self.config.set('SpotY', str(spot.idNo),
                                int(graphicsInstructs[2].pos[1]))
        self.config.write()


    def build_config(self, config):
        config.setdefaults('kivy', {'log_dir': self.user_data_dir})
        config.setdefaults('technical', {'spotCount': 15,
                                         'spotSize': 10,
                                         'measuredChannel': 'red'})
        config.setdefaults('email', {'address': 'example@company.com'})
        self.spotCount = int(config.get('technical', 'spotCount'))
        
        noneDict = {}
        for i in range(1, self.spotCount + 1):
            noneDict[str(i)] = None
        config.setdefaults('SpotTypes', noneDict)
        config.setdefaults('SpotConcentrations', noneDict)
        config.setdefaults('SpotSizes', noneDict)
        config.setdefaults('SpotX', noneDict)
        config.setdefaults('SpotY', noneDict)
 

    def sendEmail(self):
        sendMail([self.config.get('email', 'address')],
                 ('Spot analyser files from {}'
                  ).format(self.writeDir.split('/')[-2].split('\\')[-1]),
                 ('Spot analyser files from {}'
                  ).format(self.writeDir.split('/')[-2].split('\\')[-1]),
                 self.writeDir)
    

    def clearAllWidgets(self):
        for widget in Window.children:
            Window.remove_widget(widget)


    def take_photo(self, fileType, calibNo=1, sampleGrp=1):
        assert fileType == 'calib' or fileType == 'sample'
        print 'fileType', fileType
        if fileType == 'calib':
            filepath = self.writeDir + 'calib_{}.jpg'.format(calibNo)
        else:
            filepath = self.writeDir + 'sample_{}.jpg'.format(sampleGrp)
        self.cameraFile = filepath
        print 'filePath', filepath
        try:
            print 'taking picture'
            self.takenPhoto = filepath
            camera.take_picture(filepath, self.camera_callback)
        except NotImplementedError:
            popup = MsgPopup(msg="This feature has not yet been "
                                 "implemented for this platform.")
            popup.open()


    def camera_callback(self, imageFile, **kwargs):
        print 'got camera callback'
        PILImage.open(imageFile).resize((800,600)).save(imageFile)
        Clock.schedule_once(self.new_photo_callback, 0.3)
        return False


    def new_photo_callback(self, dt):
        self.goto_color_reader_screen(self.cameraFile)


    def build_settings(self, settings):
        settings.add_json_panel('Settings', self.config, 'settings.json')


    def on_config_change(self, config, section, key, value):
        print config, section, key, value
        if section == 'technical':
            if key == 'measuredChannel':
                self.measuredChannel = value
            elif key == 'spotSize':
                self.calibrationScreen.ids['colorReader'].currentSpotSize =\
                    int(self.config.get('technical', 'spotSize'))
                self.sampleScreen.ids['colorReader'].currentSpotSize =\
                    int(self.config.get('technical', 'spotSize'))


    def writeCalibFile(self, calibFile, calib):
        if calib is not None:
            with open(calibFile, 'wb') as f:
                f.write('M: {}\n'.format(calib.M))
                f.write('C: {}\n'.format(calib.C))
                f.write('R2: {}\n'.format(calib.R2))
                f.write('Channel: {}\n'.format(calib.channel))            


    def readCalibFile(self, calibFile):
        with open(calibFile, 'r') as f:
            M = f.next().split()[1]
            C = f.next().split()[1]
            R2 = f.next().split()[1]
            measuredChannel = f.next().split()[1]
        Calib = namedtuple('CalibCurve', ['M', 'C', 'R2', 'channel'])
        return Calib(M=M, C=C, R2=R2, channel=measuredChannel)


    def create_new_data_set(self):
        setDataDir = os.path.join(self.user_data_dir,
                                  '{0:%Y%m%d_%H%M}'.format(datetime.now()),
                                  '')
        # TODO handle data error if dir already exists
        try:
            os.makedirs(setDataDir)
        except OSError:
            setDataDir = os.path.join(self.user_data_dir,
                                      '{0:%Y%m%d_%H%M%S}'.format(datetime.now()),
                                      '')
            os.makedirs(setDataDir)
        return setDataDir

    
    def delete_data_set(self):
        fileChooser = self.calibChooserScreen.ids['calibChooser']
        try:
            shutil.rmtree(fileChooser.selection[0])
            fileChooser._update_files()
        except Exception as e:
            pass


    def on_pause(self):
        return True


    def on_resume(self):
        pass 


class MsgPopup(Popup):
    def __init__(self, msg):
        super(MsgPopup, self).__init__()
        self.ids.message_label.text = msg


if __name__ == '__main__':
    AnalyserApp().run()

