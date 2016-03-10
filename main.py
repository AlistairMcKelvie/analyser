import kivy

from kivy.app import App
from kivy.core.window import Window
from kivy.core.image import Image

from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics import Color
from kivy.properties import StringProperty, OptionProperty, ListProperty
from kivy.lang import Builder
from kivy import platform
import kivy.metrics as metrics


import os
import csv
from collections import namedtuple

from color_reader import ColorReader,\
                         CalibrationScreen,\
                         SampleScreen
from display import CalibResultsScreen, SampleResultsScreen
from sendGmail import sendMail
import shutil
from datetime import datetime

import calc
import util

class MainMenuScreen(BoxLayout):
    pass


class ImageMenuScreen(BoxLayout):
    pass


class GraphScreen(Widget):
    pass


class StockImageScreen(Widget):
    def selectImage(self):
        app = App.get_running_app()
        fileChooser = self.ids['fileChooser']
        if fileChooser.selection:
            selection = fileChooser.selection[0]
            if selection.split('.')[-1] in ['png', 'jpg', 'jpeg', 'bmp']:
                app.goto_color_reader_screen(selection)

from kivy.uix.listview import ListItemButton
from kivy.adapters.listadapter import ListAdapter
class CalibChooserScreen(Widget):
    selectedCalib = StringProperty('')
    def refresh(self):
        self.listView = self.ids['listView']
        app = App.get_running_app()

        drs = os.listdir(app.dataSetDir)
        data = []
        for dr in drs:
            if os.path.isfile(app.dataSetDir + '/' + dr + '/calib.txt'):
                data.append({'text': dr, 'is_selected': False})

        args_converter = lambda row_index, rec: {'text': rec['text'],
                                       'size_hint_y': None,
                                       'height': 25}

        self.listView.adapter = ListAdapter(data=data,
                           args_converter=args_converter,
                           cls=ListItemButton,
                           selection_mode='single',
                           allow_empty_selection=True)


    def deleteDataSet(self):
        selection = self.listView.adapter.selection
        if selection:
            app = App.get_running_app()
            shutil.rmtree(app.dataSetDir + '/' + selection[0].text)
            self.refresh()

    def selectDataSet(self):
        selection = self.listView.adapter.selection
        if selection:
            app = App.get_running_app()
            app.selectDataSet(app.dataSetDir + '/' + selection[0].text)

# Implement simple screen manager, as the kivy
# one seems to be a bit broken
class AnalyserScreenManager(object):
    pastScreens = []
    currentScreen = None
    Screenback = namedtuple('Screenback', ['screen', 'callback'])

    def add(self, screen, backbuttonCallback=None):
        if self.currentScreen:
            self.pastScreens.append(self.currentScreen)
        self.currentScreen = self.Screenback(screen, backbuttonCallback)
        self.__setScreen__(screen)


    def back(self):
        if self.pastScreens:
            self.currentScreen = self.pastScreens.pop()
            if self.currentScreen.callback is not None:
                self.currentScreen.callback()
            self.__setScreen__(self.currentScreen.screen)

    @staticmethod
    def __setScreen__(screen):
        for widget in Window.children:
            Window.remove_widget(widget)
        Window.add_widget(screen)

class Screens(object):
    _mainMenu = None
    _imageMenu = None
    _stockImage = None
    _calibChooser = None
    _calibResults = None
    _calibration = None
    _sample = None
    _sampleResults = None

    def __init__(self, app):
        self.app = app

    #Lazy screen loading to improve startup times
    @property
    def mainMenu(self):
        if self._mainMenu is None:
            self._mainMenu = MainMenuScreen()
        return self._mainMenu

    @property
    def imageMenu(self):
        if self._imageMenu is None:
            self._imageMenu = ImageMenuScreen()
        return self._imageMenu

    @property
    def stockImage(self):
        if self._stockImage is None:
            self._stockImage = StockImageScreen()
        return self._stockImage

    @property
    def calibChooser(self):
        if self._calibChooser is None:
            self._calibChooser = CalibChooserScreen()
        return self._calibChooser

    @property
    def calibResults(self):
        if self._calibResults is None:
            self._calibResults = CalibResultsScreen()
        return self._calibResults

    @property
    def calibration(self):
        if self._calibration is None:
            self._calibration = CalibrationScreen()
        return self._calibration

    @property
    def sample(self):
        if self._sample is None:
            self._sample = SampleScreen()
        return self._sample

    @property
    def sampleResults(self):
        if self._sampleResults is None:
            self._sampleResults = SampleResultsScreen()
        return self._sampleResults


class AnalyserApp(App):
    measuredChannel = OptionProperty('red', options=['red', 'green', 'blue'])
    calibSpots = ListProperty([])
    targetReaderScreen = StringProperty('')
    stdsFile = StringProperty('')
    calibFile = StringProperty('')
    calcLog = StringProperty('')
    qConfCSV = StringProperty('')
    analysisMode = StringProperty('')

    def __init__(self, **kwargs):
        super(AnalyserApp, self).__init__(**kwargs)
        Window.bind(on_keyboard=self.onKeyboard)
        self.screens = Screens(self)

    def build(self):
        '''Runs when app starts'''
        self.dataSetDir = self.user_data_dir

        Builder.load_file('color_reader.kv')
        Builder.load_file('display.kv')

        self.firstSample = True
        self.firstRaw = True
        self.calibNo = 0
        self.qConfCSV = 'Q_Crit_Vals.csv'
        self.measuredChannel = self.config.get('technical', 'measuredChannel')
        self.analysisMode = self.config.get('technical', 'analysisMode')

        self.screenManager = AnalyserScreenManager()
        self.goto_main_menu()

    @property
    def rawFile(self):
        return self.writeDir + '/raw.csv'

    @property
    def calibFile(self):
        return self.writeDir + '/calib.txt'

    @property
    def samplesFile(self):
        return self.writeDir + '/samples.csv'

    @property
    def calcLog(self):
        return self.writeDir + '/calc_log.txt'

    @property
    def stockImageDir(self):
        return os.getcwd() + '/stock_images'

    def onKeyboard(self, window, key, *args):
        # If back/esc
        if key == 27:
            print('Back pressed')
            self.screenManager.back()
            return True
        return False

    def goto_calib_results(self):
        self.screens.calibResults.refresh(self.calibSpots, self.calib,
                                          self.blankVal, self.analysisMode,
                                          self.measuredChannel)
        self.screenManager.add(self.screens.calibResults)

    def goto_sample_results(self, spots, conc):
        self.screens.sampleResults.refresh(spots, conc, self.measuredChannel)
        self.screenManager.add(self.screens.sampleResults)

    def goto_image_menu(self):
        if self.targetReaderScreen == 'calib':
            self.calibNo += 1
        self.screenManager.add(self.screens.imageMenu)

    def goto_color_reader_screen(self, imageFile, *args):
        assert (self.targetReaderScreen == 'calib' or
                self.targetReaderScreen == 'sample'),\
            'targetReaderScreen is set to {}, this is not valid option.'\
            .format(self.targetReaderScreen)
        if self.targetReaderScreen == 'calib':
            readerScreen = self.screens.calibration
        elif self.targetReaderScreen == 'sample':
            readerScreen = self.screens.sample

        readerScreen.updateImage(imageFile)
        self.screenManager.add(readerScreen, readerScreen.rollbackSpots)

    def goto_main_menu(self):
        self.screenManager.add(self.screens.mainMenu)

    def cleanUpDirs(self):
        for dr in os.listdir(self.dataSetDir):
            if not os.path.isfile(self.dataSetDir + '/' + dr + '/calib.txt'):
                shutil.rmtree(self.dataSetDir + '/' + dr)



    def writeSpotsToConfig(self):
        print 'writing to config'
        if self.targetReaderScreen == 'sample':
            spots = self.screens.sample.ids['colorReader'].spots
        else:
            spots = self.screens.calibration.ids['colorReader'].spots
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
                                         'measuredChannel': 'red',
                                         'analysisMode': 'Blank Normalize'})
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

    def build_settings(self, settings):
        settings.add_json_panel('Settings', self.config, 'settings.json')

    def on_config_change(self, config, section, key, value):
        print config, section, key, value
        if section == 'technical':
            if key == 'measuredChannel':
                self.measuredChannel = value
            elif key == 'spotSize':
                self.screens.calibration.ids['colorReader'].currentSpotSize =\
                    int(self.config.get('technical', 'spotSize'))
                self.screens.sample.ids['colorReader'].currentSpotSize =\
                    int(self.config.get('technical', 'spotSize'))
            elif key == 'analysisMode':
                self.analysisMode = self.config.get('technical',
                                                    'analysisMode')

    def createDataSet(self):
        setDataDir = '{0}/{1:%Y%m%d_%H:%M}/'.format(self.dataSetDir,
                                                    datetime.now())
        try:
            os.mkdir(setDataDir)
        except OSError:
            setDataDir = '{0}/{1:%Y%m%d_%H:%M:%S}/'.format(self.dataSetDir,
                                                           datetime.now())
            os.mkdir(setDataDir)
        return setDataDir

    def selectDataSet(self, dataDir):
        self.writeDir = dataDir
        self.calib = util.CalibrationCurve(file=self.calibFile)
        self.logger = calc.CalcLogger('log', self.calcLog)
        self.goto_image_menu()

    def on_pause(self):
        return True

    def on_resume(self):
        pass

if __name__ == '__main__':
    AnalyserApp().run()
