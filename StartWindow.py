from typing import Union, cast 
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication, QVBoxLayout, QHBoxLayout, \
    QWidget, QDialog, QTreeView, QPushButton, QFileDialog, QMenu, QFrame
from PyQt5.QtCore import Qt, QMimeData
from qgis.core import QgsProject, QgsLayerTreeLayer, QgsLayerTreeModel, QgsLayerTree, QgsProviderRegistry
from qgis.utils import iface
from qgis.gui import QgsLayerTreeView
import sys, os, string, random
from osgeo import ogr




class customlayerListWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderHidden(True)

        self.setDragEnabled(True)

        self.setAcceptDrops(True)

        self.setDropIndicatorShown(True)

        self.setDragDropMode(QTreeWidget.DragDrop)
    
    def addTopLevelItem(self, item:QTreeWidgetItem):
        for i in range(self.topLevelItemCount()):
            if item.layerID == self.topLevelItem(i).layerID and \
            item.layerName == self.topLevelItem(i).layerName and \
            item.layerPath == self.topLevelItem(i).layerPath:
                return
        super().addTopLevelItem(item)


class layerItem(QTreeWidgetItem):
    def __init__(self, id:str, name:str = None, path:str = None):
        super().__init__()
        self.layerID = id
        self.layerName = name
        self.layerPath = path
        if self.layerName is not None and self.layerName != "":
            self.setText(0, self.layerName)
        else:
            self.setText(0, self.layerPath)
    
    def get_layer_vlaue(self):
        return {'id':self.layerID, 'name':self.layerName, 'path':self.layerPath}
    
    def isConnected(self):
        if '⁂' in self.layerID:
            return False
        else:
            return True

    def __repr__(self) -> str:
        '''Текстове представлення елемента.'''
        
        return f'{self.layerName}({self.layerPath})'

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
            item = self.layer_list.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                new_item = layerItem(item.layerID, item.layerName, item.layerPath)
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


        self.printLayerDataButton = QPushButton("Вивести дані шару")
        self.printLayerDataButton.clicked.connect(self.printSelectedLayerData)
        layerslayout.addWidget(self.printLayerDataButton)
        
        self.runButton = QPushButton("Запустити перевірку")
        self.runButton.clicked.connect(self.run)
        layerslayout.addWidget(self.runButton)
        self.setLayout(layerslayout)

    def run(self):
        def get_layer_list_for_validator(selected_layers):
            layers_dict = {}
            for layer in selected_layers:
                # print(type(x))
                uri_components = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.dataProvider().dataSourceUri())
                
                path_to_layer = uri_components['path']
                
                layer_name = layer.name()#get_real_layer_name(layer)
                print(f'Назва {layer_name} {path_to_layer}')
                driver_name = layer.dataProvider().storageType()
                
                layers_dict[layer.id()] = {'layer_name': layer_name, 'path': path_to_layer, 'driver_name': driver_name} 
                
            return layers_dict
        
        structure_bgd_file_path = 'C:/Users/brych/OneDrive/Документы/01 Робота/98 Сторонні проекти/ua mbd team/Плагіни/Перевірка на МБД/BGD_Validator/EDRA_structure/structure_bgd3.json'
        domains_bgd_file_path = r'C:\Users\brych\OneDrive\Документы\01 Робота\98 Сторонні проекти\ua mbd team\Плагіни\Перевірка на МБД\BGD_Validator\EDRA_structure\structure_bgd3.json'
        

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
                layersList.append(layerItem(id, layerName, path))

            elif type=='gpkg':
                ds = ogr.Open(path)
                tempLayersList = []
                for i in range(ds.GetLayerCount()):
                    layer = ds.GetLayerByIndex(i)
                    layerName = layer.GetName()
                    randomid = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(36))
                    id = f"⁂{layerName}_{randomid}"
                    tempLayersList.append(layerItem(id, layerName, path))
                
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
            

    def update_layers(self):
        self.layer_list_widget.clear()
        for layer in iface.layerTreeView().selectedLayersRecursive():
            layer_item = layerItem(layer.id(), layer.name(), layer.dataProvider().dataSourceUri())
            self.layer_list_widget.addTopLevelItem(layer_item)
    
    def add_selected_layers(self):
        for layer in iface.layerTreeView().selectedLayersRecursive():
            layer_item = layerItem(layer.id(), layer.name(), layer.dataProvider().dataSourceUri())
            self.layer_list_widget.addTopLevelItem(layer_item)
        
    def show_context_menu(self, position):
        selected_item = self.layer_list_widget.selectedItems()[0]
        selected_item = cast(layerItem, selected_item)

        if selected_item is not None:
            print(selected_item)
            menu = QMenu(self)
            if selected_item.isConnected():
                layer = QgsProject.instance().mapLayer(selected_item.layerID)
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