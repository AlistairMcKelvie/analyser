from kivy.app import App
from kivy.clock import Clock
from kivy.uix.popup import Popup

from plyer import camera

from functools import partial
from datetime import datetime
from PIL import Image as PILImage
import os
from types import *


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

class CalibrationCurve(object):
    def __init__(self, M=None, C=None, R2=None, channel=None,
                 pointsCount=0, file=None, status='OK'):
        assert status in ['OK', 'NoBlank', 'NotEnoughConcentrations']
        if file is not None:
            assert M is None
            assert C is None
            assert R2 is None
            assert pointsCount is None
            self.readCalibFile(file)
        elif status == 'OK':
            assert type(M) is FloatType
            assert type(C) is FloatType
            assert type(R2) is FloatType
            assert channel in ['red', 'green', 'blue']
            self.M = M
            self.C = C
            self.R2 = R2
            self.channel = channel
            self.pointsCount = pointsCount
            self.status = status
        else:
            self.status = status

    def readCalibFile(self, calibFile):
        with open(calibFile, 'r') as f:
            self.status = f.next().split()[1]
            if self.status == 'OK':
                self.M = float(f.next().split()[1])
                self.C = float(f.next().split()[1])
                self.R2 = float(f.next().split()[1])
                self.channel = f.next().split()[1]
                self.pointsCount = int(f.next().split()[1])


    def writeCalibFile(self, calibFile):
        with open(calibFile, 'wb') as f:
            if self.status == 'OK':
                f.write('Status: {}\n'.format(self.status))
                f.write('M: {}\n'.format(self.M))
                f.write('C: {}\n'.format(self.C))
                f.write('R2: {}\n'.format(self.R2))
                f.write('Channel: {}\n'.format(self.channel))
                f.write('PointsCount: {}\n'.format(self.pointsCount))
            else:
                f.write(self.status + '\n')


