import os
import shutil

from kivy.uix.listview import ListItemButton
from kivy.uix.widget import Widget
from kivy.adapters.listadapter import ListAdapter
from kivy.properties import StringProperty
from kivy.app import App

class CalibChooserScreen(Widget):
    selectedCalib = StringProperty('')
    def refresh(self):
        self.listView = self.ids['listView']
        app = App.get_running_app()

        drs = os.listdir(app.dataSetDir)
        data = []
        for dr in drs:
            if os.path.isfile(app.dataSetDir + '/' + dr + '/calib.txt'):
                data.append({'text': dr, 'is_selected': False})

        args_converter = lambda row_index, rec: {'text': rec['text'],
                                       'size_hint_y': None,
                                       'height': '30dp'}

        self.listView.adapter = ListAdapter(data=data,
                           args_converter=args_converter,
                           cls=ListItemButton,
                           selection_mode='single',
                           allow_empty_selection=True)


    def deleteDataSet(self):
        selection = self.listView.adapter.selection
        if selection:
            app = App.get_running_app()
            shutil.rmtree(app.dataSetDir + '/' + selection[0].text)
            self.refresh()

    def selectDataSet(self):
        selection = self.listView.adapter.selection
        if selection:
            app = App.get_running_app()
            app.selectDataSet(app.dataSetDir + '/' + selection[0].text)
