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
    pass


class CalibChooserScreen(Widget):

    def delete_data_set(self, selection):
        try:
            shutil.rmtree(selection)
            self.ids['fileChooser']._update_files()
        except Exception as e:
            pass


class AnalyserApp(App):
    measuredChannel = OptionProperty('red', options=['red', 'green', 'blue'])
    calibSpots = ListProperty([])
    targetReaderScreen = StringProperty('')
    stdsFile = StringProperty('')
    calibFile = StringProperty('')
    calcLog = StringProperty('')
    qConfCSV = StringProperty('')
    analysisMode = StringProperty('')

    def build(self):
        '''Runs when app starts'''
        self.dataSetDir = self.user_data_dir

        self.mainMenuScreen = MainMenuScreen()
        self.imageMenuScreen = ImageMenuScreen()
        self.stockImageScreen = StockImageScreen()
        self.calibChooserScreen = CalibChooserScreen()

        Builder.load_file('color_reader.kv')
        self.calibrationScreen = CalibrationScreen()
        self.sampleScreen = SampleScreen()

        Builder.load_file('display.kv')
        self.calibResultsScreen = CalibResultsScreen()
        self.sampleResultsScreen = SampleResultsScreen()

        self.firstSample = True
        self.firstRaw = True
        self.calibNo = 0
        self.qConfCSV = 'Q_Crit_Vals.csv'
        self.measuredChannel = self.config.get('technical', 'measuredChannel')
        self.analysisMode = self.config.get('technical', 'analysisMode')

        return self.mainMenuScreen

    @property
    def rawFile(self):
        return self.writeDir + 'raw.csv'

    @property
    def calibFile(self):
        return self.writeDir + 'calib.txt'

    @property
    def samplesFile(self):
        return self.writeDir + 'samples.csv'

    @property
    def calcLog(self):
        return self.writeDir + 'calc_log.txt'

    @property
    def stockImageDir(self):
        return os.getcwd() + '/stock_images'

    def goto_calib_results(self):
        self.calibResultsScreen.refresh(self.calibSpots, self.calib,
                                        self.blankVal, self.analysisMode,
                                        self.measuredChannel)
        self.newScreen(self.calibResultsScreen)

    def goto_sample_results(self, spots, conc):
        self.sampleResultsScreen.refresh(spots, conc, self.measuredChannel)
        self.newScreen(self.sampleResultsScreen)

    def goto_image_menu(self):
        if self.targetReaderScreen == 'calib':
            self.calibNo += 1
        self.newScreen(self.imageMenuScreen)

    def goto_color_reader_screen(self, imageFile, *args):
        assert (self.targetReaderScreen == 'calib' or
                self.targetReaderScreen == 'sample'),\
            'targetReaderScreen is set to {}, this is not valid option.'\
            .format(self.targetReaderScreen)
        if self.targetReaderScreen == 'calib':
            readerScreen = self.calibrationScreen
        elif self.targetReaderScreen == 'sample':
            readerScreen = self.sampleScreen

        readerScreen.updateImage(imageFile)
        self.newScreen(readerScreen)

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

    def newScreen(self, screen):
        for widget in Window.children:
            Window.remove_widget(widget)
        Window.add_widget(screen)

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

    def selectDataSet(self, pathList):
        if len(pathList) == 0:
            return
        self.writeDir = pathList[0] + '/'
        self.calib = util.CalibrationCurve(file=self.calibFile)
        self.logger = calc.CalcLogger('log', self.calcLog)
        self.goto_image_menu()

    def on_pause(self):
        return True

    def on_resume(self):
        pass


if __name__ == '__main__':
    AnalyserApp().run()
