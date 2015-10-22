from kivy.app import App
from kivy.clock import Clock
from kivy.uix.popup import Popup

from plyer import camera

from functools import partial
from datetime import datetime
from PIL import Image as PILImage
import os


def channelIndexFromName(measuredChannel):
    if measuredChannel == 'red':
        return 0
    if measuredChannel == 'green':
        return 1
    if measuredChannel == 'blue':
        return 2
    raise RuntimeError('{} is not a valid channel '
                       'name.'.format(measuredChannel))


def take_photo(filepath):
    try:
        print 'taking picture'
        camera.take_picture(filepath, camera_callback)
    except NotImplementedError:
        popup = MsgPopup(msg="This feature has not yet been "
                             "implemented for this platform.")
        popup.open()


def camera_callback(imageFile, **kwargs):
    app = App.get_running_app()
    print 'got camera callback'
    PILImage.open(imageFile).resize((800,600)).save(imageFile)
    Clock.schedule_once(partial(app.goto_color_reader_screen, imageFile, 0.3))
    return False


class MsgPopup(Popup):
    def __init__(self, msg):
        super(MsgPopup, self).__init__()
        self.ids.message_label.text = msg


def create_new_data_set(dirName):
    setDataDir = '{0}/{1:%Y%m%d_%H:%M}/'.format(dirName, datetime.now())
    # TODO handle data error if dir already exists
    try:
        os.mkdir(setDataDir)
    except OSError:
        setDataDir = '{0}/{1:%Y%m%d_%H:%M:%S}/'.format(dirName, datetime.now())
        os.mkdir(setDataDir)
    return setDataDir


def delete_data_set():
    app = App.get_running_app()
    fileChooser = app.calibChooserScreen.ids['calibChooser']
    try:
        shutil.rmtree(fileChooser.selection[0])
        fileChooser._update_files()
    except Exception as e:
        pass

