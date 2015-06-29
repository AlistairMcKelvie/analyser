import kivy

from kivy.app import App
from kivy.core.window import Window
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup

from kivy.graphics.vertex_instructions import Rectangle
from kivy.graphics import Color

from kivy.lang import Builder

from kivy import platform

from PIL import Image as PILImage

import os
import os.path
from os import remove
from os import listdir

from plyer import camera

from myGraph import MyGraph
from color_reader import ColorReaderSpot, ColorReader, ColorReaderScreen
from sendGmail import sendMail

from myGraph import MyGraph


class MainMenuScreen(BoxLayout):
    pass


class ImageMenuScreen(BoxLayout):
    pass


class GraphScreen(Widget):
    pass


class FileChooserScreen(Widget):
    pass


class Main(App):
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
        self.fileChooserScreen.ids['fileChooser'].path = os.getcwd() + '/stock_images'
        self.clearAllWidgets()
        Window.add_widget(self.fileChooserScreen)


    def goto_color_reader(self, imageFile=None):
        colorReader = self.colorReaderScreen.ids['colorReader']
        self.clearAllWidgets()
        Window.add_widget(self.colorReaderScreen)
        
        # color reader initialization
        if not colorReader.initialImageAndDrawDone:
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
                self.config.set('SpotSizes', str(i), int(graphicsInstucts[2].size[0]))
                self.config.set('SpotX', str(i), int(graphicsInstucts[2].pos[0]))
                self.config.set('SpotY', str(i), int(graphicsInstucts[2].pos[1]))
        self.config.write()


    def resizeImage(self, imageFile):
        # not currently used!
        print imageFile
        basewidth = 800
        img = PILImage.open(imageFile)
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))
        resizedIm = img.resize((basewidth, hsize), PILImage.ANTIALIAS)
        return resizedIm


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
            popup = MsgPopup(msg="This feature has not yet been implemented for this platform.")
            popup.open()

    def camera_callback(self):
        print 'got to camera callback'



class MsgPopup(Popup):
    def __init__(self, msg):
        super(MsgPopup, self).__init__()

        self.ids.message_label.text = msg

if __name__ == '__main__':
    Main().run()

