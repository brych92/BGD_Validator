from qgis.PyQt.QtWidgets import (
    QLabel, QVBoxLayout, QTabWidget, QTreeWidget, QHBoxLayout,
    QPushButton, QApplication, QMenu, QTreeWidgetItem, QDialog, QTextEdit, QWidget
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont, QColor, QPixmap, QIcon

from qgis.core import QgsProject, QgsProviderRegistry, QgsVectorLayer, QgsFeature, QgsPointXY
from qgis.utils import iface


import os, urllib.parse

class startWindow(QDialog):
    def __init__(self, parent=None):
        super(startWindow, self).__init__(parent)
        # Create a layout for the window
        layout = QVBoxLayout()

        # Create a label for the layers browser
        layers_browser_label = QLabel('Drag and drop layers from layers browser')
        layout.addWidget(layers_browser_label)

        # Create a QTreeWidget to display the layers
        self.layers_widget = QTreeWidget()
        self.layers_widget.setDragDropMode(QTreeWidget.DragDrop)
        self.layers_widget.setDragEnabled(True)
        self.layers_widget.setAcceptDrops(True)
        self.layers_widget.setDropIndicatorShown(True)
        self.layers_widget.setDefaultDropAction(Qt.CopyAction)
        self.layers_widget.setDragDropOverwriteMode(False)
        layout.addWidget(self.layers_widget)

        # Set the layout for the window
        self.setLayout(layout)

        # Connect the drag and drop events to handle_drag_and_drop function
        self.layers_widget.dragEnterEvent = self.handle_drag_and_drop
        self.layers_widget.dropEvent = self.handle_drag_and_drop

    def handle_drag_and_drop(self, event):
        if event.mimeData().hasFormat('application/x-qgis-layer-list'):
            event.accept()
            layer_list = event.mimeData().data('application/x-qgis-layer-list')
            layer_list_str = str(layer_list, 'utf-8')
            layer_urls = urllib.parse.parse_qs(layer_list_str)['url']
            for layer_url in layer_urls:
                layer = QgsProject.instance().mapLayersByName(layer_url.split('/')[-1])[0]
                self.layers_widget.addTopLevelItem(QTreeWidgetItem([layer.name()]))
        else:
            event.ignore()
