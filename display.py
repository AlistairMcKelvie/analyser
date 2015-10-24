import kivy

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
import kivy.metrics as metrics

import util
from graph import CalibGraph

class CalibResultsScreen(BoxLayout):

    def refreshCalibResults(self, calibSpots, calib, blankVal,
                             analysisMode, measuredChannel):
        valuesTable = self.ids['valuesTable']
        calibGraph = self.ids['calibGraph']
        if calib.status in ['OK', 'NotEnoughConcentrations']:
            calibGraph.drawSpots(calibSpots)
        if calib.status == 'OK':
            calibGraph.drawCurve(calib)
        colorIndex = util.channelIndexFromName(measuredChannel)
        valuesTable.clear_widgets()
        assert analysisMode in ['Blank Normalize', 'Surrounds Normalize']
        if analysisMode == 'Blank Normalize':
            if blankVal is None:
                blankVal = ''
            else:
                blankVal = str(int(round(blankVal)))
        for spot in calibSpots:
            row = BoxLayout()
            valuesTable.add_widget(row)
            row.add_widget(Label(text=str(spot.idNo), font_size=metrics.dp(15)))
            row.add_widget(Label(text=str(spot.conc), font_size=metrics.dp(15)))
            row.add_widget(Label(text=str(int(round(spot.colorVal[colorIndex]))),
                                 font_size=metrics.dp(15)))
            if analysisMode == 'Surrounds Normalize':
                blankVal = str(int(round(spot.surroundsVal)))
            row.add_widget(Label(text=blankVal, font_size=metrics.dp(15)))

            if calib.status in 'NoBlank' and analysisMode == 'Blank Normalize':
                absorb = ''
            else:
                absorb = '{:.3f}'.format(spot.absorb)
            row.add_widget(Label(text=absorb,
                                 font_size=metrics.dp(15)))
        valuesTable.height = len(calibSpots) * metrics.dp(20)

        if calib.status == 'NotEnoughConcentrations':
            calibEqn = u'Not enough calibration points to calculate equation.'
        elif calib.status == 'NoBlank':
            calibEqn = ('Cannot calculate calibration, no blank value present.\n'
                        'Please read some blank samples.')
        else:
            calibEqn = (u'Concentration = {0:.3f}\u03b1 + {1:.3f}      R\u00b2 = {2:.4f}'
                        ).format(calib.M, calib.C, calib.R2)
        self.ids['calibEqn'].text = calibEqn


class SampleResultsScreen(BoxLayout):

    def refreshSampleResults(self, spots, conc, measuredChannel):
        valuesTable = self.ids['valuesTable']
        colorIndex  = util.channelIndexFromName(measuredChannel)
        valuesTable.clear_widgets()

        for spot in spots:
            row = BoxLayout()
            valuesTable.add_widget(row)
            row.add_widget(Label(text=str(spot.idNo), font_size=metrics.dp(15)))
            row.add_widget(Label(text=str(int(round(spot.colorVal[colorIndex]))),
                                 font_size=metrics.dp(15)))
            row.add_widget(Label(text='{:.3f}'.format(spot.absorb),
                                 font_size=metrics.dp(15)))
        valuesTable.height = len(spots) * metrics.dp(20)

        self.ids['calcConc'].text =\
            'Calculated Concentration: {:.3f}'.format(conc)

