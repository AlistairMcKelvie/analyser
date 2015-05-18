import kivy

from kivy.garden.graph import Plot, Color
from kivy.properties import AliasProperty
from kivy.graphics import Point


class DotPlot(Plot):
    def create_drawings(self):
        self._color = Color(*self.color)
        self._mesh = Point(points=(0, 0), pointsize=1)
        self.bind(color=lambda instr, value: setattr(self._color.rgba, value))
        return [self._color, self._mesh]

    def draw(self, *args):
        points = self.points
        mesh = self._mesh
        params = self._params
        funcx = log10 if params['xlog'] else lambda x: x
        funcy = log10 if params['ylog'] else lambda x: x
        xmin = funcx(params['xmin'])
        ymin = funcy(params['ymin'])
        size = params['size']
        ratiox = (size[2] - size[0]) / float(funcx(params['xmax']) - xmin)
        ratioy = (size[3] - size[1]) / float(funcy(params['ymax']) - ymin)
        mesh.points = ()
        for k in range(len(points)):
            x = (funcx(points[k][0]) - xmin) * ratiox + size[0]
            y = (funcy(points[k][1]) - ymin) * ratioy + size[1]
            mesh.add_point(x, y)

    def _set_pointsize(self, value):
        if hasattr(self, '_mesh'):
            self._mesh.pointsize = value
    pointsize = AliasProperty(lambda self: self._mesh.pointsize, _set_pointsize)

    def _set_source(self, value):
        if hasattr(self, '_mesh'):
            self._mesh.source = value
    source = AliasProperty(lambda self: self._mesh.source, _set_source)

