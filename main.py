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
from analyser_display import CalibResultsScreen,\
                             SampleResultsScreen
from analyser_util import channelIndexFromName 
from sendGmail import sendMail
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
        self.analysisMode = self.config.get('technical', 'analysisMode')
        return self.mainMenuScreen


    def goto_main_menu(self):
        self.clearAllWidgets()
        Window.add_widget(self.mainMenuScreen)


    def goto_calib_results(self):
        valuesTable = self.calibResultsScreen.ids['valuesTable']
        calibGraph = self.calibResultsScreen.ids['calibGraph']
        if self.calib.status in ['OK', 'NotEnoughConcentrations']:
            calibGraph.drawSpots(self.calibSpots)
        if self.calib.status == 'OK':
            calibGraph.drawCurve(self.calib)
        colorIndex = channelIndexFromName(self.measuredChannel) 
        valuesTable.clear_widgets()
        assert self.analysisMode in ['Blank Normalize', 'Surrounds Normalize']
        if self.analysisMode == 'Blank Normalize':
            if self.blankVal is None:
                blankVal = ''
            else:
                blankVal = str(int(round(self.blankVal)))
        for spot in self.calibSpots:
            row = BoxLayout()
            valuesTable.add_widget(row)
            row.add_widget(Label(text=str(spot.idNo), font_size=metrics.dp(15)))
            row.add_widget(Label(text=str(spot.conc), font_size=metrics.dp(15)))
            row.add_widget(Label(text=str(int(round(spot.colorVal[colorIndex]))),
                                 font_size=metrics.dp(15)))
            if self.analysisMode == 'Surrounds Normalize':
                blankVal = str(int(round(spot.surroundsVal)))
            row.add_widget(Label(text=blankVal, font_size=metrics.dp(15)))

            if self.calib.status in 'NoBlank' and self.analysisMode == 'Blank Normalize':
                absorb = ''
            else:
                absorb = '{:.3f}'.format(spot.absorb)
            row.add_widget(Label(text=absorb,
                                 font_size=metrics.dp(15)))
        valuesTable.height = len(self.calibSpots) * metrics.dp(20)

        if self.calib.status == 'NotEnoughConcentrations':
            calibEqn = u'Not enough calibration points to calculate equation.'
        elif self.calib.status == 'NoBlank':
            calibEqn = ('Cannot calculate calibration, no blank value present.\n'
                        'Please read some blank samples.')
        else:
            calibEqn = (u'Concentration = {0:.3f}\u03b1 + {1:.3f}      R\u00b2 = {2:.4f}'
                        ).format(self.calib.M, self.calib.C, self.calib.R2)
        self.calibResultsScreen.ids['calibEqn'].text = calibEqn 

        self.clearAllWidgets()
        Window.add_widget(self.calibResultsScreen)


    def goto_sample_results(self, spots, conc):
        self.sampleResultsScreen.refreshSampleResults(spots, conc,
                                                      self.measuredChannel)
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


    def goto_color_reader_screen(self, imageFile, *args):
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


    def clearAllWidgets(self):
        for widget in Window.children:
            Window.remove_widget(widget)


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


    def on_pause(self):
        return True


    def on_resume(self):
        pass


if __name__ == '__main__':
    AnalyserApp().run()

