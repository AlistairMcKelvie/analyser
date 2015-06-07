import kivy

from kivy.app import App
from kivy.lang import Builder

from kivy.garden.graph import Graph, MeshLinePlot

from dotPlot import DotPlot
from random import random

from kivy.uix.label import Label
import math

class MyGraph(Graph):
    def __init__(self, **kwargs):
        super(MyGraph, self).__init__(**kwargs)
        self.xlabel = 'Concentration (mg/L)'
        self.ylabel = 'A'
        self.x_ticks_major = 0.2
        self.y_ticks_major = 0.2
        self.y_grid_label = True
        self.x_grid_label = True
        self.padding = 5
        self.xlog = False
        self.ylog = False
        self.x_grid = True
        self.y_grid = True
        self.xmin = -0.2
        self.xmax = 2
        self.ymin = -0.2
        self.ymax = 0.4
        
        self.dotPlot = DotPlot(color=[1, 1, 1, 1])
        self.dotPlot.points = [(x, x - 2 + 4 * random()) for x in range(10)]
        self.dotPlot.pointsize = 3
        self.add_plot(self.dotPlot)

        self.linePlot = MeshLinePlot(color=[0, 1, 0, .75])
        self.add_plot(self.linePlot)

        
    def updateGraph(self, concs, vals):
        print concs
        print vals
        colorIndex = 0
        averageConcs = {}
        for conc in concs:
            if conc is not None:
                concSum = 0
                for i in range(len(concs)):
                    if concs[i] == conc:
                        concSum += vals[i][colorIndex]
                averageConcs[conc] = concSum / concs.count(conc)
        print averageConcs
        blankVal = averageConcs.pop('Blank')
        self.dotPlot.points = [(0, 0)]
        for key in averageConcs:
            self.dotPlot.points.append((key, -math.log10(averageConcs[key] / blankVal)))
        print self.dotPlot.points
        
        # Calculate least squares reg
        N = len(self.dotPlot.points)
        print 'N', N
        sumX = sum([x for x, y in self.dotPlot.points])
        print 'sumX', sumX
        sumY = sum([y for x, y in self.dotPlot.points])
        print 'sumY', sumY
        sumXY = sum([x * y for x, y in self.dotPlot.points])
        print 'sumXY', sumXY
        sumXX = sum([x * x for x, y in self.dotPlot.points])
        print 'sumXX', sumXX

        A = (N * sumXY - sumX * sumY) / (N * sumXX - sumX**2)
        print 'A', A
        
        C = (sumY - A * sumX) / N
        print 'C', C
        print 'y = {A}x + {C}'.format(A=A, C=C)
        self.linePlot.points = [(x, (x * A + C)) for x in range(-1, 11)]

        # Calculate R2
        SSres = sum([(y - (x * A + C))**2 for x, y in self.dotPlot.points])
        print 'SSres', SSres
        meanY = sum([y for x, y in self.dotPlot.points]) / len(self.dotPlot.points)
        print 'meanY', meanY
        SStot = sum([(y - meanY)**2 for x, y in self.dotPlot.points])
        print 'SStot', SStot
        R2 = 1 - SSres / SStot
        print 'R2', R2
        self.parent.parent.ids['LSR'].text = 'y = {A:.5f}x + {C:.5f}'.format(A=A, C=C)  
        self.parent.parent.ids['R2'].text = 'R2 = {:.5f}'.format(R2)  

        
        
        



main_widget = Builder.load_string('''
#
BoxLayout:
    MyGraph:

''')

class MainApp(App):
    def build(self):
        return main_widget   

if __name__ == '__main__':
    MainApp().run()

