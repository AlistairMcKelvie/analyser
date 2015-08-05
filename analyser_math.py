import math
import csv
from collections import namedtuple, OrderedDict
from color_reader import ColorReaderSpot


class CalcLogger(object):
    def __init__(self, mode='print', fileName=''):
        self.mode = mode
        if mode == 'log':
            if file == '':
                raise RuntimeError('fileName is required argument'
                                   'for log mode')
            else:
                self.f = open(fileName, 'ab')
        elif mode != 'print':
            raise RuntimeError('{} is not a valid log mode'.format(mode))
    
    
    def log(self, st):
        if self.mode == 'print':
            print st.encode('utf-8')
        else:
            self.f.write('{}\n'.format(st.encode('utf-8')))


def calculateConc(calib, colorVal):
    A = math.log10(colorVal) / calib.blank
    result = (A - calib.C) / calib.M
    return result


def readQConf(N, conf, qConfCSV):
    with open(qConfCSV, 'rb') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row['N']) == N:
                return row['CL{}'.format(conf)]
        else:
            raise RuntimeError(('no matching Q conf value for '
                               'N: {}, CL: {}').format(N, conf))


def calculateACalibCurve(spots, calcLog, measuredChannel, qConfCSV, CL=90):
    log = CalcLogger('print', calcLog).log
    channelIndex = channelIndexFromName(measuredChannel)
    colorValAverageDict = {}
    concSet = set()
    spotConcDict = OrderedDict()
    for spot in spots:
        concSet.add(spot.conc)
    while concSet:
        #TODO: handle no blank value
        spotConcDict[concSet.pop()] = []
    for spot in spots:
        spot.exclude = False
        spotConcDict[spot.conc].append(spot)

    for conc in spotConcDict:
        #TODO handle cases for less than 3 spots or more that 10
        assert len(spotConcDict[conc]) > 2
        assert len(spotConcDict[conc]) <= 10
        log('color values for {}'.format(conc))
        for sp in spotConcDict[conc]:
            log('{0}  {1}'.format(sp.idNo, sp.colorVal[channelIndex]))
        recQ = readQConf(len(spotConcDict[conc]), CL, qConfCSV)
        spotConcDict[conc].sort(key=lambda spot: spot.colorVal[channelIndex])

        lowestVal = spotConcDict[conc][0].colorVal[channelIndex]
        highestVal = spotConcDict[conc][-1].colorVal[channelIndex]
        log('lowest value is {}'.format(lowestVal))
        log('highest value is {}'.format(highestVal))
        valRange = highestVal - lowestVal
        log('range is {}'.format(valRange))
        secondLowest = spotConcDict[conc][1].colorVal[channelIndex] 
        qValLow = (secondLowest - lowestVal) / valRange 
        log(('Q-value for lowest is ({0} - {1})/{2} = {3}'
             ).format(secondLowest, lowestVal, valRange, qValLow))
        log(('max allowed Q-value for N: {0}, CL{1} is {2}'
             ).format(len(spotConcDict[conc]), CL, recQ))
        if qValLow <= recQ:
            log('OK!')
        else:
            log('Failed! Treating as an outlier and excluding')
            spotConcDict[conc][1].exclude = True

        secondHighest = spotConcDict[conc][-2].colorVal[channelIndex] 
        qValHigh = (highestVal - secondHighest) / valRange 
        log(('Q-value for highest is ({0} - {1})/{2} = {3}'
             ).format(highestVal, secondHighest, valRange, qValHigh))
        log(('max allowed Q-value for N: {0}, CL{1} is {2}'
             ).format(len(spotConcDict[conc]), CL, recQ))
        if qValHigh <= recQ:
            log('OK!')
        else:
            log('Failed! Treating as an outlier and excluding')
            spotConcDict[conc][-1].exclude = True

        valCount = 0
        valSum = 0.0
        for sp in spotConcDict[conc]:
            if sp.exclude is False:
                valCount += 1
                valSum += sp.colorVal[channelIndex]
        colorValAverageDict[conc] = valSum / valCount
        log(('mean brightness value from {0} values for {1} is {2}'
             ).format(valCount, conc, colorValAverageDict[conc]))
        log('-----------------------------------------------------')

    blankVal = colorValAverageDict[0]
    
    log(u'calculating \u03b1 values')
    log(u'\u03b1 = -log(color value/blank value)')
    log('blank value: {}'.format(blankVal))

    calibPoints = []
    for key in colorValAverageDict:
        alpha = -math.log10(colorValAverageDict[key] / blankVal)
        calibPoints.append((key, alpha))
        log(u'conc: {0}  \u03b1: {1}'.format(key, alpha))

    # Make calibration curve
    N = len(calibPoints)
    if N >= 2:
        log('Calculating LSR')
        log(u'conc = M\u03b1 + C')
        log(u'M = (n\u2211XY - \u2211X\u2211Y)/'
            u'(n\u2211X\u00b2 - (\u2211X)\u00b2)')
        log(u'C = (\u2211Y - M\u2211X)/n')
        log('')
        log('n = {}'.format(N))
        sumX = sum([x for x, y in calibPoints])
        log(u'\u2211X = {}'.format(sumX))
        sumY = sum([y for x, y in calibPoints])
        log(u'\u2211Y = {}'.format(sumY))
        sumXY = sum([x * y for x, y in calibPoints])
        log(u'\u2211XY = {}'.format(sumXY))
        sumXX = sum([x * x for x, y in calibPoints])
        log(u'\u2211XX = {}'.format(sumXX))
        log('')

        M = (N * sumXY - sumX * sumY) / (N * sumXX - sumX**2)
        log('M = {}'.format(M))

        C = (sumY - M * sumX) / N
        log('C = {}'.format(C))
        log(u'conc = {M}\u03b1 + {C}'.format(M=M, C=C))
        log('')
        
        log(u'calculating R\u00b2')
        log(u'R\u00b2 = 1 - SSres/SStot')
        log(u'SSres = \u2211(y - f)\u00b2')
        SSres = sum([(y - (x * M + C))**2 for x, y in calibPoints])
        log('SSres = {}'.format(SSres)) 
        log(u'SStot = \u2211(y - \u1ef9)\u00b2')
        meanY = sum([y for x, y in calibPoints]) / len(calibPoints)
        SStot = sum([(y - meanY)**2 for x, y in calibPoints])
        log('SStot = {}'.format(SStot))
        R2 = 1 - SSres / SStot
        log(u'R\u00b2 = {:.5f}'.format(R2))
        Calib = namedtuple('CalibCurve',
                           ['M', 'C', 'R2', 'blank', 'channel'])
        return Calib(M=M, C=C, R2=R2, blank=blankVal,
                     channel=measuredChannel)


def channelIndexFromName(measuredChannel):
    if measuredChannel == 'red':
        return 0
    if measuredChannel == 'green':
        return 1
    if measuredChannel == 'blue':
        return 2
    raise RuntimeError('{} is not a valid channel '
                       'name.'.format(measuredChannel))


def writeRawData(calib, rawFile, spots, measuredChannel, firstWrite=False):
    channelIndex = channelIndexFromName(calib.channel)
    fieldNames = ['type', 'sample_group', 'sample_no',
                  'known_concentration', 'calculated_concentration',
                  'red','green', 'blue', 'alpha', 'measured_channel']
    if firstWrite:
        with open(rawFile, 'wb') as sFile:
            csvWriter = csv.DictWriter(sFile, fieldnames=fieldNames)
            csvWriter.writeheader()
    with open(rawFile, 'ab') as sFile:
        csvWriter = csv.DictWriter(sFile, fieldnames=fieldNames)
        for spot in spots:
            if spot.type == 'Blank' or spot.type == 'Std':
                type = 'Standard'
                conc = spot.conc
                sample_group = ''
                sample_no = ''
            elif spot.type == 'Sample':
                type = 'Sample'
                conc = ''
                sample_group = spot.sampleGrp
                sample_no = spot.idNo
            calculatedConc = calculateConc(calib, spot.colorVal[channelIndex])
            if spot.colorMode == 'RGBA':
                alpha = '{:.3f}'.format(spot.colorVal[3])
            else:
                alpha = ''
            csvWriter.writerow(
                {'type': type,
                 'sample_group': sample_group,
                 'sample_no': sample_no,
                 'known_concentration': conc,
                 'red': '{:.3f}'.format(spot.colorVal[0]),
                 'green': '{:.3f}'.format(spot.colorVal[1]),
                 'blue': '{:.3f}'.format(spot.colorVal[2]),
                 'alpha': alpha,
                 'measured_channel': measuredChannel,
                 'calculated_concentration': '{:.3f}'.format(calculatedConc)})


def percentile(percentileNo, data):
    data = sorted(data)
    r = percentileNo / 100.0 * (len(data) + 1)
    ir = int(math.floor(r))
    result = (r - ir) * (data[ir] - data[ir - 1]) + data[ir - 1]
    return result


def writeSamplesFile(calib, samplesFile, spots, calcLog, firstWrite=False):
    log = CalcLogger('print', calcLog).log
    colorIndex = channelIndexFromName(calib.channel)
    fieldNames = ['sample_group', 'calculated_concentration']
    if firstWrite:
        with open(samplesFile, 'wb') as f:
            csvWriter = csv.DictWriter(f, fieldNames)
            csvWriter.writeheader()
    concSum = 0
    sampleGrp = None

    # check sample grp
    for spot in spots:
        assert sampleGrp is None or spot.sampleGrp == sampleGrp
        sampleGrp = spot.sampleGrp
    log('sample group: {}'.format(sampleGrp))

    valList = []
    for spot in spots:
        log(('Spot: {}   brightness: {}'
             ).format(spot.idNo, spot.colorVal[colorIndex]))
        valList.append(spot.colorVal[colorIndex])
    tenP = percentile(10, valList)
    log('10th percentile: {}'.format(tenP))
    nintyP = percentile(90, valList)
    log('90th percentile: {}'.format(nintyP))

    includedList = []
    for val in valList:
        if val < tenP or val > nintyP:
            log('excluding {}'.format(val))
        else:
            includedList.append(val)
    valMean = math.fsum(includedList) / len(includedList)
    log('mean of remaining brightness values: {}'.format(valMean))
    calcConc = calculateConc(calib, valMean)
    log('calculated concentration: {}'.format(calcConc))
    with open(samplesFile, 'ab') as f:
        csvWriter = csv.DictWriter(f, fieldNames)
        csvWriter.writerow({'sample_group': sampleGrp,
                            'calculated_concentration': calcConc})


