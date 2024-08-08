
from importlib import reload
from typing import Union, cast 
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication, QVBoxLayout, QHBoxLayout, \
    QWidget, QDialog, QTreeView, QPushButton, QFileDialog, QMenu, QFrame, QComboBox
from PyQt5.QtCore import Qt, QMimeData
from numpy import unicode_
from qgis.core import QgsProject, QgsLayerTreeLayer, QgsLayerTreeModel, QgsLayerTree, QgsProviderRegistry, QgsVectorLayer
from qgis.utils import iface
from qgis.gui import QgsLayerTreeView
import sys, os, string, random
from osgeo import ogr
import json
sys.path.append(r'C:\Users\brych\OneDrive\Документы\01 Робота\98 Сторонні проекти\ua mbd team\Плагіни\Перевірка на МБД\BGD_Validator')

import initialize_script
import Result_Window

reload(initialize_script)
reload(Result_Window)

from initialize_script import run_validator
from Result_Window import ResultWindow
# import initialize_script
# import Result_Window

def get_real_layer_name(layer: QgsVectorLayer) -> str:
    """
    Отримує назву реального шару, присутнього у QGIS.

    Аргументи:
        layer (QgsVectorLayer): Шар, з якого отримати назву.

    Повертає:
        str: Назва реального шару.
    """
    if not isinstance(layer, QgsVectorLayer):
        return None
    
    if layer.providerType() == "postgres":
        uri = layer.dataProvider().uri()
        source_layer_name = uri.table()
        source_layer_name = source_layer_name.strip("''")
    elif layer.providerType() == "ogr":
        uri_components = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.dataProvider().dataSourceUri())
        if uri_components["layerName"]:
            source_layer_name = uri_components["layerName"]
        else:
            directory, filename_with_extension = os.path.split(uri_components["path"])
            source_layer_name, extension = os.path.splitext(filename_with_extension)
    else:
        source_layer_name = ''
        
    return source_layer_name

class customlayerListWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderHidden(True)

        self.setDragEnabled(True)

        self.setAcceptDrops(True)

        self.setDropIndicatorShown(True)

        self.setDragDropMode(QTreeWidget.DragDrop)
    
    def addTopLevelItem(self, newItem:QTreeWidgetItem):
        newItem = cast(layerItem, newItem)

        for i in range(self.topLevelItemCount()):
            item = cast(layerItem, self.topLevelItem(i))
            if newItem.get_layer_value() == item.get_layer_value():
                return
        
        super().addTopLevelItem(newItem)


class layerItem(QTreeWidgetItem):
    def __init__(self, id:str, visible_name:str, path:str, real_name:str):
        super().__init__()
        
        if id == '':
            randomid = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(36))
            id = f"⁂{real_name}_{randomid}"
        
        self.__layerID__ = id
        self.__layerVisibleName__ = visible_name
        self.__layerRealName__ = real_name
        self.__layerPath__ = path
        
        if self.__layerVisibleName__ is not None and self.__layerVisibleName__ != "":
            self.setText(0, self.__layerVisibleName__)
        else:
            self.setText(0, self.__layerPath__)
    
    def get_layer_value(self):
        return {'id':self.__layerID__, 'name':self.__layerVisibleName__, 'path':self.__layerPath__, 'real_name':self.__layerRealName__}
    
    def isConnected(self):
        if '⁂' in self.__layerID__:
            return False
        else:
            return True
    
    def getID(self):
        return self.__layerID__

    def getRealName(self):
        return self.__layerRealName__

    def getVisibleName(self):
        return self.__layerVisibleName__

    def getPath(self):  
        return self.__layerPath__
    
    def __repr__(self) -> str:
        '''Текстове представлення елемента.'''
        return f'{self.__layerVisibleName__}({self.__layerPath__})'

class layerSelectionDialog(QDialog):
    def __init__(self, layer_list: list[layerItem], parent=None ):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.layer_list = QTreeWidget(self)
        self.layer_list.setHeaderHidden(True)
        self.layer_list.setDragEnabled(True)
        self.layer_list.setAcceptDrops(True)
        self.layer_list.setDragDropMode(QTreeWidget.DragDrop)
        for layer in layer_list:
            layer.setFlags(layer.flags() | Qt.ItemIsUserCheckable)
            layer.setCheckState(0, Qt.Unchecked)
            self.layer_list.addTopLevelItem(layer)
        
        layout.addWidget(self.layer_list)

        hbox = QHBoxLayout()
        select_all_button = QPushButton("Вибрати всі")
        select_all_button.clicked.connect(self.select_all)
        hbox.addWidget(select_all_button)
        deselect_all_button = QPushButton("Скинути всі")
        deselect_all_button.clicked.connect(self.deselect_all)
        hbox.addWidget(deselect_all_button)
        done_button = QPushButton("Готово")
        done_button.clicked.connect(self.accept)        
        hbox.addWidget(done_button)
        layout.addLayout(hbox)

    def select_all(self):
        for i in range(self.layer_list.topLevelItemCount()):
            item = self.layer_list.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)

    def deselect_all(self):
        for i in range(self.layer_list.topLevelItemCount()):
            item = self.layer_list.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)
    
    def get_selected_layers(self) -> list[layerItem]:
        result = []
        for i in range(self.layer_list.topLevelItemCount()):
            item = cast(layerItem, self.layer_list.topLevelItem(i))
            if item.checkState(0) == Qt.Checked:
                new_item = layerItem(id = item.getID(), visible_name=item.getVisibleName(), real_name=item.getRealName(), path = item.getPath())
                result.append(new_item)
        
        return result

class MainWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)        

        self.folder_path=os.path.expanduser('~')

        # Create a QVBoxLayout
        layerslayout = QVBoxLayout(self)
        
        self.from_layer_tree_frame = QFrame()


        layersTopButtonsLayout = QHBoxLayout(self)
        layertreeWidgetbuttonslayout = QVBoxLayout(self)
        layersTopButtonsLayout.addLayout(layertreeWidgetbuttonslayout)
        
        update_layers_button = QPushButton("З виділених")
        update_layers_button.setToolTip("Очистити список та заповнити виділеними шарами")
        update_layers_button.clicked.connect(self.update_layers)
        layertreeWidgetbuttonslayout.addWidget(update_layers_button)
        
        update_layers_button = QPushButton("Додати виділені")
        update_layers_button.setToolTip("Додати в кінець списку виділені шари")
        update_layers_button.clicked.connect(self.add_selected_layers)
        layertreeWidgetbuttonslayout.addWidget(update_layers_button)

        self.openFromFileButton = QPushButton("Відкрити з файлу")
        layersTopButtonsLayout.addWidget(self.openFromFileButton)
        self.openFromFileButton.clicked.connect(self.openFiles)
        layerslayout.addLayout(layersTopButtonsLayout)

        self.layer_list_widget = customlayerListWidget()
        self.layer_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.layer_list_widget.customContextMenuRequested.connect(self.show_context_menu)
        # Add the tree view to the layout
        layerslayout.addWidget(self.layer_list_widget)

        self.strutures = {'EDRA:':1}
        epsg_list = ['']
        self.crs_combo_box = QComboBox()
        self.printLayerDataButton = QPushButton("Вивести дані шару")
        self.printLayerDataButton.clicked.connect(self.printSelectedLayerData)
        layerslayout.addWidget(self.printLayerDataButton)
        
        self.runButton = QPushButton("Запустити перевірку")
        self.runButton.clicked.connect(self.run)
        layerslayout.addWidget(self.runButton)
        self.setLayout(layerslayout)

    def run(self):
        layers_dict = {}
        for i in range(self.layer_list_widget.topLevelItemCount()):
            layer = self.layer_list_widget.topLevelItem(i)
            layer = cast(layerItem, layer)
            layers_dict[layer.getID()] = {'layer_name': layer.getRealName(), 'path': layer.getPath(), 'layer_real_name': layer.getRealName(), 'layer_crs': ''}
            #print(f"{layer.layerID} {layer.layerName} {layer.layerPath} {type(layer.layerPath)}")
        
        print('Вхідний список шарів:')
        print(json.dumps(layers_dict, indent=4,ensure_ascii=False))        
        result_structure = run_validator(layers_dict)

        print('\n\n\n\n\nВивід')
        print(json.dumps(result_structure, indent=4, ensure_ascii=False)) 
        window = ResultWindow(result_structure, parent=iface.mainWindow())
        window.show()
        #structure_bgd_file_path = 'C:/Users/brych/OneDrive/Документы/01 Робота/98 Сторонні проекти/ua mbd team/Плагіни/Перевірка на МБД/BGD_Validator/EDRA_structure/structure_bgd3.json'
        #domains_bgd_file_path = r'C:\Users\brych\OneDrive\Документы\01 Робота\98 Сторонні проекти\ua mbd team\Плагіни\Перевірка на МБД\BGD_Validator\EDRA_structure\structure_bgd3.json'
        

    def printSelectedLayerData(self):
        for item in self.layer_list_widget.selectedItems():
            print(item.get_layer_vlaue())

    def openFiles(self):
        pathArr=QFileDialog.getOpenFileNames(None,"Виберіть файл(файли) для імпорту", self.folder_path, "Geopackage (*.gpkg);;GeoJSON (*.json, *.geojson);;GeoDatabase (*.gdb)")[0]
        if pathArr==[]:
            print('Нічого не вибрано!')
            return
        
        self.folder_path=os.path.dirname(pathArr[0])
        type = pathArr[0].split('.')[-1]

        layersList = []

        for path in pathArr:
            if type=='json' or type=='geojson':
                #print(path)
                datasource  = ogr.Open(path, 0)
                if datasource is None:
                    print('Could not open %s' % (path))
                    continue
                layer = datasource.GetLayer()
                layerName = layer.GetName()
                randomid = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(36))
                id = f"⁂{layerName}_{randomid}"
                layersList.append(layerItem(id=id, visible_name=layerName, real_name=layerName, path=path))

            elif type=='gpkg':
                ds = ogr.Open(path)
                tempLayersList = []
                for i in range(ds.GetLayerCount()):
                    layer = ds.GetLayerByIndex(i)
                    layerName = layer.GetName()
                    randomid = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(36))
                    id = f"⁂{layerName}_{randomid}"
                    tempLayersList.append(layerItem(id=id, visible_name=layerName, real_name=layerName, path=path))
                
                lsDialog = layerSelectionDialog(tempLayersList, parent=self)
                
                if lsDialog.exec_() == 1:
                    selectedItems = lsDialog.get_selected_layers()
                    for item in selectedItems:
                        layersList.append(item)
                lsDialog = None
                
            #     layer  = ogr.Open(path, 0).getLayer()
            #     layerName = layer.GetName()
            #     randomid = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(36))
            #     id = f"⁂{layerName}_{randomid}"
            #     LayersList.append(layerItem(id, layerName, path))

            # elif type=='gdb':
            #     layer  = ogr.Open(path, 0).getLayer()
            #     layerName = layer.GetName()
            #     randomid = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(36))
            #     id = f"⁂{layerName}_{randomid}"
            #     LayersList.append(layerItem(id, layerName, path))
        
        self.layer_list_widget.clear()
        for layer in layersList:
            self.layer_list_widget.addTopLevelItem(layer)
            
    def make_layer_item_from_layer(self, layer):
        layerID = layer.id()
        layerVisibleName = layer.name()
        layerRealName = get_real_layer_name(layer)
        layerPath = layer.dataProvider().dataSourceUri()
        layer_item = layerItem(id = layerID, visible_name=layerVisibleName, real_name= layerRealName, path = layerPath)
        return layer_item

    def update_layers(self):
        self.layer_list_widget.clear()
        for layer in iface.layerTreeView().selectedLayersRecursive():
            self.layer_list_widget.addTopLevelItem(self.make_layer_item_from_layer(layer))
    
    def add_selected_layers(self):
        for layer in iface.layerTreeView().selectedLayersRecursive():
            self.layer_list_widget.addTopLevelItem(self.make_layer_item_from_layer(layer))
        
    def show_context_menu(self, position):
        selected_item = self.layer_list_widget.selectedItems()[0]
        selected_item = cast(layerItem, selected_item)

        if selected_item is not None:
            print(selected_item)
            menu = QMenu(self)
            if selected_item.isConnected():
                layer = QgsProject.instance().mapLayer(selected_item.__layerID__)
                if layer:
                    related_layer = layer
                    menu.addAction("Виділити шар")
                    menu.addAction("Перейти в налаштування шару")
                    menu.addAction("Переглянуи таблицю атрибутів шару")
                    menu.addAction("")
                    menu.addAction("Видалити шар")
                else:
                    related_layer =  None
                    menu.addAction("Видалити шар")
            if menu.isEmpty():
                return
            
            selected_action = menu.exec_(self.mapToGlobal(position))

            if selected_action:
                if selected_action.text() == "Виділити шар":
                    iface.setActiveLayer(related_layer)
                
                elif selected_action.text() == "Перейти в налаштування шару":
                    iface.showLayerProperties(related_layer)
                
                elif selected_action.text() == "Переглянуи таблицю атрибутів шару":
                        iface.showAttributeTable(related_layer)
                    
                elif selected_action.text() == "Видалити шар":
                    selected_index = self.layer_list_widget.indexOfTopLevelItem(selected_item)
                    self.layer_list_widget.takeTopLevelItem(selected_index)

                print(f"Вибрано дію: {selected_action.text()}")
    
window = MainWindow(parent=iface.mainWindow())

window.show()