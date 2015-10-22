from kivy.app import App
from kivy.clock import Clock
from kivy.uix.popup import Popup

from plyer import camera
from functools import partial
from PIL import Image as PILImage


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

