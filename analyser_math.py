import math
import csv
from collections import namedtuple, OrderedDict
from color_reader import ColorReaderSpot
from analyser_util import channelIndexFromName
from analyser_util import CalibrationCurve


class CalcLogger(object):
    '''Used for logging maths functions to log file or screen'''

    def __init__(self, mode='print', fileName=''):
        '''Create logger in print to screen or write to file mode.

        Keyword arguments:
        mode -- log mode 'print' or 'log' (default 'print')
        fileName -- file to log to, ignored if print mode
        '''
        assert mode in ['log', 'print']
        self.mode = mode
        self.fileName = fileName
        if mode == 'log':
            if file == '':
                raise RuntimeError('fileName is required argument'
                                   'for log mode')
                with open(fileName, 'wb'):
                    pass

    def log(self, st):
        '''log string as utf-8 to screen of file depending on mode.'''
        if self.mode == 'print':
            print st.encode('utf-8')
        else:
            with open(self.fileName, 'ab') as wf:
                wf.write('{}\n'.format(st.encode('utf-8')))


def calculateConc(calib, absorb):
    '''Calculate a concentration based on previously calculated 
    calibration and an absorbance value. Returns None if calib is not
    calculated, and float otherwise.'''
    if calib.status != 'OK':
        return None
    else:
        result = (absorb - calib.C) / calib.M
        return result


def calculateCalibCurve(spots, logger, measuredChannel, analysisMode,
                         qConfCSV, CL=90, blankVal=None):
    '''Calculates a calibation curve based on a list of spots.

    spots -- a list of ColorReaderSpot objects, must contain spots with
    different conc values, or 'NotEnoughConcentrations' will be returned.
    logger -- a CalcLogger object for doing logging.
    measuredChannel -- 'red'/'green'/'blue'; color channel being used for analysis.
    analysisMode -- 'Blank Normalize' or 'Surrounds Normalize'; technique for
    normalizing sample values, dividing color value by the color value of the
    blank, or by dividing by the color value of an area surrounding the main spot.
    qConfCSV -- path to csv containing the table of q test confidence values
    CL - required q test confidence percent for exclusion of a spot, (default - 90)
    blankVal -- mean color value of the blank spots, not used if mode is
    'Surrounds Normalize', otherwise 'NoBlank' will be returned.'''
    log = logger.log
    channelIndex = channelIndexFromName(measuredChannel)

    absorbAverageDict = {}
    concSet = set()
    spotConcDict = OrderedDict()
    # put lists of spots with the same conc in a dictionary
    for spot in spots:
        concSet.add(spot.conc)
    while concSet:
        spotConcDict[concSet.pop()] = []
    for spot in spots:
        spotConcDict[spot.conc].append(spot)

    assert analysisMode in ['Blank Normalize', 'Surrounds Normalize']
    if analysisMode == 'Blank Normalize':
        if blankVal is None:
            return CalibrationCurve(status='NoBlank')

    for conc in spotConcDict:
        log(u'calculating \u03b1 values')
        log(u'\u03b1 = -log(color value/blank value)')
        log('values for {}'.format(conc))
        log(u'ID    Color Val     Blank Val     \u03b1')
        for spot in spotConcDict[conc]:
            if analysisMode == 'Surrounds Normalize':
                blankVal = spot.surroundsVal
            spot.absorb = -math.log(spot.colorVal[channelIndex]/
                                    blankVal)
            log('{0: <2}    {1:9.3f}   {2:9.3f}    {3:9.3f}'.format(spot.idNo,
                                              spot.colorVal[channelIndex],
                                              blankVal,
                                              spot.absorb))
        spotConcDict[conc].sort(key=lambda spot: spot.absorb)

        if len(spotConcDict[conc]) > 10:
            percentileTest(spotConcDict[conc], log)
        elif len(spotConcDict[conc]) > 2:
            qTest(spotConcDict[conc], qConfCSV, CL, log)

        valCount = 0
        valSum = 0.0
        for spot in spotConcDict[conc]:
            if spot.exclude is False:
                valCount += 1
                valSum += spot.absorb
        absorbAverageDict[conc] = valSum / valCount
        log(('mean absorbance value from {0} values for {1} is {2}'
             ).format(valCount, conc, absorbAverageDict[conc]))
        log('-----------------------------------------------------')
    calibPoints = []
    for key in absorbAverageDict:
        calibPoints.append((key, absorbAverageDict[key]))

    # Make calibration curve
    N = len(calibPoints)
    if N < 2:
        log('Not enough different calibration '
            'concentrations to calculate curve')
        return CalibrationCurve(status='NotEnoughConcentrations')
    else:
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
        return CalibrationCurve(M=M, C=C, R2=R2, channel=measuredChannel,
                                pointsCount=len(spots))


def calculateBlankVal(spots, measuredChannel, logger):
    '''Calculates the mean color value of the spots with
    conc 0 from as list of ColorReaderSpots.

    spots -- a list of ColorReaderSpot objects.
    measuredChannel -- 'red'/'green'/'blue'; color channel being used for analysis.
    logger -- a CalcLogger object for doing logging.'''
    channelIndex = channelIndexFromName(measuredChannel)
    blanksList = []
    for spot in spots:
        if spot.conc == 0:
            blanksList.append(spot.colorVal[channelIndex])
    if len(blanksList) != 0:
        blankVal = sum(blanksList) / len(blanksList)
        return blankVal
    else:
        logger.log('No blank values found')
        return None


def writeRawData(calib, rawFile, spots, analysisMode, blankVal=None, firstWrite=False):
    '''Writes out the raw data from a list of spots.

    calib -- a namedtuple CalibrationCurve object which contains data on the calibration curve.
    rawFile -- path of the file to write to.
    spots -- a list of spots to write out.
    analysisMode -- 'Blank Normalize' or 'Surrounds Normalize'; technique for
    normalizing sample values, dividing color value by the color value of the
    blank, or by dividing by the color value of an area surrounding the main spot.
    qConfCSV -- path to csv containing the table of q test confidence values
    blankVal -- mean color value of the blank spots, not used if mode is
    'Surrounds Normalize', otherwise will raise 'NoBlank' if not present.
    firstWrite -- whether this is the first time writing to the file, will overwrite
    if true, otherwise will append (default - False).'''
    fieldNames = ['type', 'sample_group', 'sample_no',
                  'known_concentration', 'calculated_concentration',
                  'red','green', 'blue', 'measured_channel']
    if firstWrite:
        with open(rawFile, 'wb') as sFile:
            csvWriter = csv.DictWriter(sFile, fieldnames=fieldNames)
            csvWriter.writeheader()

    try:
        assert analysisMode in ['Blank Normalize', 'Surrounds Normalize']
    except:
        import ipdb;ipdb.set_trace()

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
            if analysisMode == 'Surrounds Normalize':
                blankVal = spot.surroundsVal

            if blankVal is not None:
                spot.absorb = -math.log(spot.colorVal[channelIndexFromName(spot.channel)]/
                                        blankVal)
                calculatedConc = calculateConc(calib, spot.absorb)
                if calculatedConc is not None:
                    calculatedConc = '{:.3f}'.format(calculatedConc)
                else:
                    calculatedConc = ''
            else:
                calculatedConc = ''

            csvWriter.writerow(
                {'type': type,
                 'sample_group': sample_group,
                 'sample_no': sample_no,
                 'known_concentration': conc,
                 'red': '{:.3f}'.format(spot.colorVal[0]),
                 'green': '{:.3f}'.format(spot.colorVal[1]),
                 'blue': '{:.3f}'.format(spot.colorVal[2]),
                 'measured_channel': spot.channel,
                 'calculated_concentration': calculatedConc})


def percentile(percentileNo, data):
    '''Calculates a percentile value from a list of data and a percentile number.'''
    data = sorted(data)
    r = percentileNo / 100.0 * (len(data) + 1)
    ir = int(math.floor(r))
    result = (r - ir) * (data[ir] - data[ir - 1]) + data[ir - 1]
    return result


def calculateSampleConc(calib, spots, analysisMode, logger, sampleGrp,
                        qConfCSV, CL=90, blankVal=None):
    '''Calculates a sample concentration from a list of spots and a calibration
    curve.

    calib -- a namedtuple Calib object which contains data on the calibraion curve.
    spots -- a list of spots to write out.
    analysisMode -- 'Blank Normalize' or 'Surrounds Normalize'; technique for
    logger -- a CalcLogger object for doing logging.
    sampleGrp -- the number the set of samples.
    qConfCSV -- path to csv containing the table of q test confidence values
    CL - required q test confidence percent for exclusion of a spot, (default - 90)
    blankVal -- mean color value of the blank spots, not used if mode is
    'Surrounds Normalize', otherwise will raise 'NoBlank' RuntimeError if not present.'''
    log = logger.log
    log('-----------------------------------------------------')
    channelIndex = channelIndexFromName(calib.channel)
    # check sample grp
    for spot in spots:
        assert sampleGrp is None or spot.sampleGrp == sampleGrp

    assert analysisMode in ['Blank Normalize', 'Surrounds Normalize']
    if analysisMode == 'Blank Normalize':
        if blankVal is None:
            raise RuntimeError('NoBlank')
    log('sample group: {}'.format(sampleGrp))
    log(u'calculating \u03b1 values')
    log(u'\u03b1 = -log(color value/blank value)')
    log(u'ID    Color Val     Blank Val     \u03b1')

    absorbList = []
    for spot in spots:
        spot.exclude = False
        if analysisMode == 'Surrounds Normalize':
            blankVal = spot.surroundsVal
        spot.absorb = -math.log(spot.colorVal[channelIndex]/
                                blankVal)
        log(('{0: <2}  {1:9.3f}    {2:9.3f}  {3:9.3f}'
             ).format(spot.idNo,
                     spot.colorVal[channelIndex],
                     blankVal,
                     spot.absorb))

    if len(spots) > 10:
        percentileTest(spots, log)
    elif len(spots) > 2:
        qTest(spots, qConfCSV, CL, log)

    valCount = 0
    valSum = 0.0
    for spot in spots:
        if not spot.exclude:
            valCount += 1
            valSum += spot.absorb
        assert calib.channel == spot.channel
    valMean = valSum / valCount

    log('mean of remaining brightness values: {}'.format(valMean))
    calcConc = calculateConc(calib, valMean)
    log('calculated concentration: {}'.format(calcConc))
    return calcConc


def writeSamplesFile(samplesFile, calcConc, sampleGrp, firstWrite=False):
    '''Writes out a group of sample data to a file.

    samplesFile -- path to the file to write sample data to.
    calcConc -- the concentration value of the sample.
    sampleGrp -- the number of the sample group.
    firstWrite -- whether this is the first time writing to the file, will overwrite
    if true, otherwise will append (default - False).'''
    fieldNames = ['sample_group', 'calculated_concentration']
    if firstWrite:
        with open(samplesFile, 'wb') as f:
            csvWriter = csv.DictWriter(f, fieldNames)
            csvWriter.writeheader()
    with open(samplesFile, 'ab') as f:
        csvWriter = csv.DictWriter(f, fieldNames)
        csvWriter.writerow({'sample_group': sampleGrp,
                            'calculated_concentration': calcConc})


def qTest(spots, qConfCSV, CL, logger=None):
    '''Does q test on a list of ColorReaderSpots, and sets the
    exclude property to True on any spot that fails the q test.

    spots -- a list of ColorReaderSpots for testing.
    qConfCSV -- path to csv containing the table of q test confidence values
    CL - required q test confidence percent for exclusion of a spot, (default - 90)
    logger -- a CalcLogger object for doing logging.'''
    if logger is None:
        def log(logger):
            pass
    else:
        log = logger

    for i in range(len(spots) - 1):
        assert(spots[i].conc == spots[i + 1].conc)

    reqQ = readQConf(len(spots), CL, qConfCSV)

    lowestVal = spots[0].absorb
    highestVal = spots[-1].absorb
    log('lowest value is {}'.format(lowestVal))
    log('highest value is {}'.format(highestVal))
    valRange = highestVal - lowestVal
    log('range is {}'.format(valRange))

    secondLowest = spots[1].absorb
    qValLow = (secondLowest - lowestVal) / valRange
    log(('Q-value for lowest is ({0} - {1})/{2} = {3}'
         ).format(secondLowest, lowestVal, valRange, qValLow))
    log(('max allowed Q-value for N: {0}, CL{1} is {2}'
         ).format(len(spots), CL, reqQ))
    if qValLow <= reqQ:
        log('OK!\n')
        lowestPassed = True
    else:
        log('Failed!')
        lowestPassed = False

    secondHighest = spots[-2].absorb
    qValHigh = (highestVal - secondHighest) / valRange 
    log(('Q-value for highest is ({0} - {1})/{2} = {3}'
         ).format(highestVal, secondHighest, valRange, qValHigh))
    log(('max allowed Q-value for N: {0}, CL{1} is {2}'
         ).format(len(spots), CL, reqQ))
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
            spots[0].exclude = True
        else:
            log('higher value is worse, excluding higher value')
            spots[-1].exclude = True
    elif not lowestPassed:
        log('lowest value failed, excluding')
        spots[0].exclude = True
    elif not highestPassed:
        log('highest value failed, excluding')
        spots[-1].exclude = True
    else:
        log('all passed')


def readQConf(N, conf, qConfCSV):
    '''Reads a q test confidence value file.

    N -- the number of samples in the test
    conf -- the required confidence, 90, 95 or 99.
    qConfCSV -- csv file with the q confidence data.'''

    with open(qConfCSV, 'rb') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if int(row['N']) == N:
                return row['CL{}'.format(conf)]
        else:
            raise RuntimeError(('no matching Q conf value for '
                               'N: {}, CL: {}').format(N, conf))


def percentileTest(spots, logger=None):
    '''Does percentile test on a list of ColorReaderSpots, and sets the
    exclude property to True on any spot that are outside the percentile.

    spot -- list of ColorReaderSpots for testing.
    logger -- a CalcLogger object for doing logging.'''

    if logger is None:
        def log(logger):
            pass
    else:
        log = logger

    absorbList = [x.absorb for x in spots]

    tenP = percentile(10, absorbList)
    log('10th percentile: {}'.format(tenP))
    nintyP = percentile(90, absorbList)
    log('90th percentile: {}'.format(nintyP))

    for spot in spots:
        if spot.absorb < tenP or spot.absorb > nintyP:
            spot.exclude = True
            log('excluding {}'.format(spot.absorb))

