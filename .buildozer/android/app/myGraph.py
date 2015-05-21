import kivy

from kivy.app import App
from kivy.lang import Builder

from kivy.garden.graph import Graph, MeshLinePlot

from dotPlot import DotPlot
from random import random

class MyGraph(Graph):
    def __init__(self, **kwargs):
        super(MyGraph, self).__init__(**kwargs)
        self.xlabel = 'X'
        self.ylabel = 'Y'
        self.x_ticks_minor = 1
        self.x_ticks_major = 1
        self.y_ticks_major = 1
        self.y_grid_label = True
        self.x_grid_label = True
        self.padding = 5
        self.xlog = False
        self.ylog = False
        self.x_grid = True
        self.y_grid = True
        self.xmin = -1
        self.xmax = 10
        self.ymin = -1
        self.ymax = 10
        
        dotPlot = DotPlot(color=[1, 1, 1, 1])
        dotPlot.points = [(x, x - 2 + 4 * random()) for x in range(10)]
        dotPlot.pointsize = 3
        self.add_plot(dotPlot)
        linePlot = MeshLinePlot(color=[0, 1, 0, .75])
        linePlot.points = [(x, x) for x in range(-1, 11)]
        self.add_plot(linePlot)



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

