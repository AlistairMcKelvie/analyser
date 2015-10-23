def channelIndexFromName(measuredChannel):
    if measuredChannel == 'red':
        return 0
    if measuredChannel == 'green':
        return 1
    if measuredChannel == 'blue':
        return 2
    raise RuntimeError('{} is not a valid channel '
                       'name.'.format(measuredChannel))


class CalibrationCurve(object):
    def __init__(self, M=None, C=None, R2=None, channel=None, pointsCount=0, file=None, status='OK')
        Calib = namedtuple('CalibCurve', ['M', 'C', 'R2', 'channel'])
        assert status in ['OK', 'NoBlank', 'NotEnoughPoints']
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
            self.measuredChannel = channel
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
                self.measuredChannel = f.next().split()[1]
                self.pointsCount = int(f.next().split()[1]


    def writeCalibFile(self, calibFile):
        with open(calibFile, 'wb') as f:
            if self.status == 'OK':
                f.write('Status: {}\n'.format(self.status)
                f.write('M: {}\n'.format(self.M))
                f.write('C: {}\n'.format(self.C))
                f.write('R2: {}\n'.format(self.R2))
                f.write('Channel: {}\n'.format(self.channel))
                f.write('PointsCount: {}\n'.format(self.pointsCount))
            else:
                f.write(self.status + '\n')


