import kivy

from kivy.app import App
from kivy.lang import Builder

from kivy.garden.graph import Graph, MeshLinePlot

from dot_plot import DotPlot
from random import random

from kivy.uix.label import Label
import math

class CalibGraph(Graph):
    def __init__(self, **kwargs):
        super(CalibGraph, self).__init__(**kwargs)
        self.xlabel = 'Concentration (mg/L)'
        self.ylabel = u'\u03b1'.encode('utf-8')
        self.x_ticks_major = 0.1
        self.y_ticks_major = 0.1
        self.y_grid_label = True
        self.x_grid_label = True
        self.padding = 5
        self.xlog = False
        self.ylog = False
        self.x_grid = True
        self.y_grid = True
        
        self.dotPlot = DotPlot(color=[1, 1, 1, 1])
        self.dotPlot.pointsize = 2
        self.add_plot(self.dotPlot)

        self.linePlot = MeshLinePlot(color=[0, 1, 0, .75])
        self.add_plot(self.linePlot)


    def drawSpots(self, spots):
        self.dotPlot.points = [(spot.conc, spot.alpha) for spot in spots]
        self.xmin = round(min([spot.conc for spot in spots]), 1) - 0.1
        self.ymin = round(min([spot.alpha for spot in spots]), 1) - 0.1
        self.xmax = round(max([spot.conc for spot in spots]), 1) + 0.1
        self.ymax = round(max([spot.alpha for spot in spots]), 1) + 0.1


    def drawCurve(self, calib):
        self.linePlot.points = [(x, x * calib.M + calib.C) for x in range(-1, 11)]


        

