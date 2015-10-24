import kivy

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
import kivy.metrics as metrics

from analyser_graph import CalibGraph
from analyser_util import channelIndexFromName

class CalibResultsScreen(BoxLayout):
    pass


class SampleResultsScreen(BoxLayout):

    def refreshSampleResults(self, spots, conc, measuredChannel):
        valuesTable = self.ids['valuesTable']
        colorIndex  = channelIndexFromName(measuredChannel)
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

