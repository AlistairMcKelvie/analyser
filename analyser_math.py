import math
import csv
from collections import namedtuple, OrderedDict
from color_reader import ColorReaderSpot
from analyser_util import channelIndexFromName 


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


def calculateConc(calib, alpha):
    result = (alpha - calib.C) / calib.M
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
    alphaAverageDict = {}
    concSet = set()
    spotConcDict = OrderedDict()

    # put lists of spots with the same conc in a dictionary
    for spot in spots:
        concSet.add(spot.conc)
    while concSet:
        spotConcDict[concSet.pop()] = []
    for spot in spots:
        spot.exclude = False
        spotConcDict[spot.conc].append(spot)

    for conc in spotConcDict:
        #TODO handle cases for less than 3 spots or more that 10
        assert len(spotConcDict[conc]) > 2
        assert len(spotConcDict[conc]) <= 10
        log(u'calculating \u03b1 values')
        log(u'\u03b1 = -log(color value/blank value)')
        log('values for {}'.format(conc))
        log(u'ID    Color Val     Blank Val     \u03b1')
        for spot in spotConcDict[conc]:
            spot.alpha = -math.log(spot.colorVal[channelIndex]/
                                   spot.blankVal[channelIndex])
            log('{0: <2}    {1:9.3f}   {2:9.3f}    {3:9.3f}'.format(spot.idNo,
                                              spot.colorVal[channelIndex],
                                              spot.blankVal[channelIndex],
                                              spot.alpha))
        reqQ = readQConf(len(spotConcDict[conc]), CL, qConfCSV)
        spotConcDict[conc].sort(key=lambda spot: spot.alpha)

        #TODO only remove one at most
        lowestVal = spotConcDict[conc][0].alpha
        highestVal = spotConcDict[conc][-1].alpha
        log('lowest value is {}'.format(lowestVal))
        log('highest value is {}'.format(highestVal))
        valRange = highestVal - lowestVal
        log('range is {}'.format(valRange))

        secondLowest = spotConcDict[conc][1].alpha
        qValLow = (secondLowest - lowestVal) / valRange 
        log(('Q-value for lowest is ({0} - {1})/{2} = {3}'
             ).format(secondLowest, lowestVal, valRange, qValLow))
        log(('max allowed Q-value for N: {0}, CL{1} is {2}'
             ).format(len(spotConcDict[conc]), CL, reqQ))
        if qValLow <= reqQ:
            log('OK!\n')
            lowestPassed = True
        else:
            log('Failed!')
            lowestPassed = False

        secondHighest = spotConcDict[conc][-2].colorVal[channelIndex] 
        qValHigh = (highestVal - secondHighest) / valRange 
        log(('Q-value for highest is ({0} - {1})/{2} = {3}'
             ).format(highestVal, secondHighest, valRange, qValHigh))
        log(('max allowed Q-value for N: {0}, CL{1} is {2}'
             ).format(len(spotConcDict[conc]), CL, reqQ))
        if qValHigh <= reqQ:
            log('OK!\n')
            highestPassed = True
        else:
            log('Failed!')
            highestPassed = False

        if not lowestPassed and not highestPassed:
            log('both lowest and highest values failed')
            if qValLow > qValHigh:
                log('lower value is worse, excluding lower value')
                spotConcDict[conc][0].exclude = True
            else:
                log('higher value is worse, excluding higher value')
                spotConcDict[conc][-1].exclude = True
        elif not lowestPassed:
            log('lowest value failed, excluding')
            spotConcDict[conc][0].exclude = True
        elif not highestPassed:
            log('highest value failed, excluding')
            spotConcDict[conc][-1].exclude = True
        else:
            log('all passed')

        valCount = 0
        valSum = 0.0
        for spot in spotConcDict[conc]:
            if spot.exclude is False:
                valCount += 1
                valSum += spot.alpha
        alphaAverageDict[conc] = valSum / valCount
        log(('mean alpha value from {0} values for {1} is {2}'
             ).format(valCount, conc, alphaAverageDict[conc]))
        log('-----------------------------------------------------')
 
    calibPoints = []
    for key in alphaAverageDict:
        calibPoints.append((key, alphaAverageDict[key]))

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
        Calib = namedtuple('CalibCurve', ['M', 'C', 'R2', 'channel'])
        return Calib(M=M, C=C, R2=R2, channel=measuredChannel)


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
            if spot.type == 'std':
                type = 'Standard'
                conc = spot.conc
                sample_group = ''
                sample_no = ''
            elif spot.type == 'sample':
                type = 'sample'
                conc = ''
                sample_group = spot.sampleGrp
                sample_no = spot.idNo
            calculatedConc = calculateConc(calib, spot.alpha)
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
    log('-----------------------------------------------------')
    channelIndex = channelIndexFromName(calib.channel)
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
    log(u'calculating \u03b1 values')
    log(u'\u03b1 = -log(color value/blank value)')
    log(u'ID    Color Val     Blank Val     \u03b1')
    alphaList = []
    for spot in spots:
        spot.alpha = -math.log(spot.colorVal[channelIndex]/
                               spot.blankVal[channelIndex])
        log(('{0: <2}  {1:9.3f}    {2:9.3f}  {3:9.3f}'
             ).format(spot.idNo,
                     spot.colorVal[channelIndex],
                     spot.blankVal[channelIndex],
                     spot.alpha))
        alphaList.append(spot.alpha)
    tenP = percentile(10, alphaList)
    log('10th percentile: {}'.format(tenP))
    nintyP = percentile(90, alphaList)
    log('90th percentile: {}'.format(nintyP))

    includedList = []
    for val in alphaList:
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

