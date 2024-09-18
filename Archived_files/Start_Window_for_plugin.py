
#зміна
from importlib import reload

from re import split
from typing import Union, cast 
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication, QVBoxLayout, QHBoxLayout, \
    QWidget, QDialog, QTreeView, QPushButton, QFileDialog, QMenu, QFrame, QComboBox, QMessageBox
from PyQt5.QtCore import Qt, QMimeData, QSize
from PyQt5.QtGui import QCursor
from numpy import unicode_
from qgis.core import QgsProject, QgsLayerTreeLayer, QgsLayerTreeModel, QgsLayerTree, QgsProviderRegistry, QgsVectorLayer
from qgis.utils import iface
from qgis.gui import QgsLayerTreeView
import sys, os, string, random
from osgeo import ogr
import json
# sys.path.append(r'/home/bohdan/Programming/ПЛАГІН/GIT/BGD_Validator/')

# import initialize_script
# import csv_to_json_structure_converter
# reload(csv_to_json_structure_converter)
from .csv_to_json_structure_converter import Csv_to_json_structure_converter

# reload(initialize_script)
# import Result_Window
# reload(Result_Window)
from .Result_Window import ResultWindow

# import checker_class
# reload(checker_class)
from .checker_class import EDRA_exchange_layer_checker, EDRA_validator

logging = True
# from initialize_script import run_validator
# import initialize_script
# import Result_Window

def log(text: str) -> None:
    if logging:
        print(text)



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

def run_validator(layers:dict, structure_folder:str):
    def get_guid_dict(layers):
        return "Ich bin schoen!"
    """
    Запустити валідатор для шарів.

    Args:
        layers (dict): Словник шарів. Кожен шар - це словник з ключами:
            - layer_crs (str): Система координат шару.
            - layer_name (str): Ім'я шару.
            - path (str): Шлях до шару.
            - driver_name (str): Ім'я драйвера, який використовувався для відкриття шару.
        structure_path (str): Шлях до файлу структури.
        domains_path (str): Шлях до файлу доменів.

    Returns:
        dict: Словник з результатами валідатору.
            - layers (dict): Словник результатів валідатору для кожного шару.
            - exchange_format_error (list): Список шарів з помилками формату обміну.
            - missing_layers (list): Список відсутніх шарів.
    """

    all_layers_check_result_dict = {}
    all_layers_check_result_dict['layers'] = {}
    all_layers_check_result_dict['exchange_format_error'] = []
    all_layers_check_result_dict['missing_layers'] = []

    for id in layers:
        
        dataSource = ogr.Open(layers[id]['path'], 0) # 0 means read-only. 1 means writeable.
        
        if dataSource.GetDriver().GetName() in ['OpenFileGDB', 'GPKG']:
            layer = dataSource.GetLayerByName(layers[id]['layer_name'])
        else:
            layer = dataSource.GetLayer()
        
        layer_real_name = layers[id]['layer_real_name']
        
        converter = Csv_to_json_structure_converter(structure_folder)

        structure = converter.create_structure_json() 
        domains = converter.create_domain_json()
        # with open(structure_path, 'r', encoding='utf-8') as f: 
        #     structure = json.loads(f.read())
        
        # with open(domains_path, 'r', encoding='utf-8') as f: 
        #     domains = json.loads(f.read())
            
        if layer is None:
            raise AttributeError(f'Не вдалося відкрити шар {layers[id]["path"]}')
        
        guid_dict = {}

        #guid {guid:[(layer, feature_id), (layer, feature_id)....]}

        layer_EDRA_valid_class = EDRA_validator(
            layer = layer,
            layer_exchange_name=layer_real_name,
            structure_json=structure,
            domains_json=domains)
        
        validate_checker = EDRA_exchange_layer_checker(
            layer_EDRA_valid_class = layer_EDRA_valid_class,
            layer_props = layers[id],
            layer_id = id)
        
        validate_result = validate_checker.run()
        
        all_layers_check_result_dict['layers'][list(validate_result.keys())[0]] = validate_result[list(validate_result.keys())[0]]
        
    return all_layers_check_result_dict

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
    """
    Елемент списку шарів, що додається до customlayerListWidget.
    """
    def __init__(self, id:str, visible_name:str, path:str, real_name:str, features_qty:int = None):
        """
        Аргументи:
            id (str): ідентифікатор шару (унікальний для кожного шару)
            visible_name (str): назва шару, що відображається у списку
            path (str): шлях до файлу шару
            real_name (str): реальна назва шару, що використовується при перевірці
        """
        super().__init__()
        
        if id == '':
            randomid = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(36))
            id = f"⁂{real_name}_{randomid}"
        
        self.__layerID__ = id
        self.__layerVisibleName__ = visible_name
        self.__layerRealName__ = real_name
        self.__layerPath__ = path
        self.__layerFeaturesQty__ = features_qty
        
        if self.__layerVisibleName__ is not None and self.__layerVisibleName__ != "":
            self.setText(0, f"{self.__layerVisibleName__}[{self.__layerFeaturesQty__}]")
        else:
            self.setText(0, f"{self.__layerPath__}[{self.__layerFeaturesQty__}]")
    
    def get_layer_value(self):
        return {'id':self.__layerID__, 'name':self.__layerVisibleName__, 'path':self.__layerPath__, 'real_name':self.__layerRealName__}
    
    def getFeaturesQty(self):
        return self.__layerFeaturesQty__

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
        return f'{self.__layerVisibleName__}({self.__layerPath__})[{self.__layerFeaturesQty__}]'

class layerSelectionDialog(QDialog):
    def __init__(self, layer_list: list[layerItem], parent=None ):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        
        hbox = QHBoxLayout()
        layout.addLayout(hbox)
        
        select_all_button = QPushButton("Вибрати всі")
        select_all_button.clicked.connect(self.select_all)
        hbox.addWidget(select_all_button)
        
        select_with_objects = QPushButton("Вибрати з об'єктами")
        select_with_objects.clicked.connect(self.select_with_objects)
        hbox.addWidget(select_with_objects)
        
        deselect_all_button = QPushButton("Скинути всі")
        deselect_all_button.clicked.connect(self.deselect_all)
        hbox.addWidget(deselect_all_button)

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

        done_button = QPushButton("Готово")
        done_button.clicked.connect(self.accept)        
        layout.addWidget(done_button)

    def select_all(self):
        for i in range(self.layer_list.topLevelItemCount()):
            item = self.layer_list.topLevelItem(i)
            item.setCheckState(0, Qt.Checked)

    def deselect_all(self):
        for i in range(self.layer_list.topLevelItemCount()):
            item = self.layer_list.topLevelItem(i)
            item.setCheckState(0, Qt.Unchecked)
    
    def select_with_objects(self):
        for i in range(self.layer_list.topLevelItemCount()):
            item = self.layer_list.topLevelItem(i)
            item = cast(layerItem, item)
            if item.getFeaturesQty() > 0:
                item.setCheckState(0, Qt.Checked)

    def get_selected_layers(self) -> list[layerItem]:
        result = []
        for i in range(self.layer_list.topLevelItemCount()):
            item = cast(layerItem, self.layer_list.topLevelItem(i))
            if item.checkState(0) == Qt.Checked:
                new_item = layerItem(id = item.getID(), visible_name=item.getVisibleName(), real_name=item.getRealName(), path = item.getPath(), features_qty = item.getFeaturesQty())
                result.append(new_item)
        
        return result

class MainWindow(QDialog):
    def parse_structures(self, directory:str) -> dict:
            temp_strcut = {}
            for root, struct_dirs, _ in os.walk(directory):
                for struct_dir in struct_dirs:
                    structure_path = os.path.join(root, struct_dir)
                    for _, version_dirs, _ in os.walk(structure_path):
                        for sub_dir in version_dirs:
                            version_path = os.path.join(structure_path, sub_dir)
                            
                            converter = Csv_to_json_structure_converter(version_path)
                            temp_metadata = converter.create_metadata_json()
                            temp_csr = converter.create_crs_json()
                            temp_branch = {
                                'path': version_path, #треба буде доробити в плагіні
                                'structure_name': temp_metadata["structure_name"],
                                'structure_date': temp_metadata["structure_date"],
                                'author': temp_metadata["author"],
                                'description': temp_metadata["description"],
                                'format': temp_metadata["format"],
                                'crs': temp_csr
                            }
                            
                            if temp_metadata["short_structure_name"] not in temp_strcut:
                                temp_strcut[temp_metadata["short_structure_name"]] = {}
                            temp_strcut[temp_metadata["short_structure_name"]][temp_metadata["structure_version"]] = temp_branch
                    
            return temp_strcut

    def __init__(self, parent=None):
        def update_version_combo_box():
            if self.BGD_type_combo_box.currentText() != '':
                self.BGD_version_combo_box.clear()
                self.BGD_version_combo_box.addItems(self.strutures[self.BGD_type_combo_box.currentText()].keys())
                
                if self.BGD_version_combo_box.count() == 1:
                    self.BGD_version_combo_box.hide()
                else:
                    self.BGD_version_combo_box.show()
                
                for i in range(self.BGD_version_combo_box.count()):
                    tooltip = f"Структура від {self.strutures[self.BGD_type_combo_box.currentText()][self.BGD_version_combo_box.itemText(i)]['structure_date']}"
                    self.BGD_version_combo_box.setItemData(i, tooltip, Qt.ToolTipRole)
        
        def update_crs_combo_box():
            if self.BGD_version_combo_box.currentText() != '' and self.BGD_type_combo_box.currentText() != '':
                self.crs_combo_box.clear()
                self.crs_combo_box.addItems([key for key in self.strutures[self.BGD_type_combo_box.currentText()][self.BGD_version_combo_box.currentText()]['crs'].keys()])
                if self.crs_combo_box.count() == 1:
                    self.crs_combo_box.hide()
                else:
                    self.crs_combo_box.show()

        super().__init__(parent)        
        self.setWindowTitle("Налаштуйте параметри перевірки")
        self.folder_path=os.path.expanduser('~')

        # Create a QVBoxLayout
        layerslayout = QVBoxLayout(self)
        
        self.from_layer_tree_frame = QFrame()

        max_height = QApplication.desktop().screenGeometry().height()
        max_width = 640#QApplication.desktop().screenGeometry().width()
        self.setMaximumSize(QSize(max_width-40, max_height-40))

        layersTopButtonsLayout = QHBoxLayout(self)
        layertreeWidgetbuttonslayout1 = QVBoxLayout(self)
        layertreeWidgetbuttonslayout2 = QVBoxLayout(self)
        layersTopButtonsLayout.addLayout(layertreeWidgetbuttonslayout1)
        layersTopButtonsLayout.addLayout(layertreeWidgetbuttonslayout2)
        
        update_layers_button = QPushButton("🔄 З виділених")
        update_layers_button.setToolTip("Очистити список та заповнити виділеними шарами")
        update_layers_button.clicked.connect(self.update_layers)
        layertreeWidgetbuttonslayout1.addWidget(update_layers_button)
        
        add_layers_button = QPushButton("➕ Додати виділені")
        add_layers_button.setToolTip("Додати в кінець списку виділені шари")
        add_layers_button.clicked.connect(self.add_selected_layers)
        layertreeWidgetbuttonslayout1.addWidget(add_layers_button)

        openFromFileButton = QPushButton("📂🔄 Відкрити з файлу")
        openFromFileButton.setToolTip("Очистити список та заповнити шарами з файлу")
        openFromFileButton.clicked.connect(self.openFiles)
        layertreeWidgetbuttonslayout2.addWidget(openFromFileButton)

        addFromFileButton = QPushButton("📂➕ Додати з файлу")
        addFromFileButton.setToolTip("Додати в кінець списку шари з файлу")
        addFromFileButton.clicked.connect(lambda: self.openFiles(True))
        layertreeWidgetbuttonslayout2.addWidget(addFromFileButton)

        layerslayout.addLayout(layersTopButtonsLayout)

        self.layer_list_widget = customlayerListWidget()
        self.layer_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.layer_list_widget.customContextMenuRequested.connect(self.show_context_menu)
        # Add the tree view to the layout
        layerslayout.addWidget(self.layer_list_widget)
        self.plugin_dir = os.path.dirname(__file__)
        self.path_to_structures = os.path.join(self.plugin_dir, 'stuctures')
        self.strutures = self.parse_structures(self.path_to_structures)
        #print(self.strutures)
        #print(json.dumps(obj=self.strutures, indent=4, ensure_ascii=False))
        
        self.BGD_type_combo_box = QComboBox()
        self.BGD_type_combo_box.addItems(self.strutures.keys())
        for i in range(self.BGD_type_combo_box.count()):
            version_index = [key for key in self.strutures[self.BGD_type_combo_box.itemText(i)].keys()][0]
            self.BGD_type_combo_box.setItemData(i, self.strutures[self.BGD_type_combo_box.itemText(i)][version_index]['structure_name'], Qt.ToolTipRole)

        self.BGD_version_combo_box = QComboBox()
        update_version_combo_box()
        # self.BGD_version_combo_box.addItems(self.strutures[self.BGD_type_combo_box.currentText()].keys())
        
        self.crs_combo_box = QComboBox()
        update_crs_combo_box()
        # self.crs_combo_box.addItems([key for key in self.strutures[self.BGD_type_combo_box.currentText()][self.BGD_version_combo_box.currentText()]['crs'].keys()])
        # if self.crs_combo_box.count() == 1:
        #     self.crs_combo_box.hide()
            
        
        self.BGD_type_combo_box.currentIndexChanged.connect(update_version_combo_box)
        self.BGD_version_combo_box.currentIndexChanged.connect(update_crs_combo_box)
        # print(json.dumps(obj=self.strutures, indent=4, ensure_ascii=False))

        self.printLayerDataButton = QPushButton("Вивести дані шару")
        self.printLayerDataButton.clicked.connect(self.printSelectedLayerData)
        layerslayout.addWidget(self.printLayerDataButton)
        layerslayout.addWidget(self.BGD_type_combo_box)
        layerslayout.addWidget(self.BGD_version_combo_box)
        layerslayout.addWidget(self.crs_combo_box)
        self.runButton = QPushButton("Запустити перевірку")
        self.runButton.clicked.connect(self.run)
        layerslayout.addWidget(self.runButton)
        self.setLayout(layerslayout)

    def run(self):
        layers_dict = {}
        for i in range(self.layer_list_widget.topLevelItemCount()):
            layer = self.layer_list_widget.topLevelItem(i)
            layer = cast(layerItem, layer)
            layers_dict[layer.getID()] = {
                'layer_name': layer.getRealName(),
                'path': layer.getPath(),
                'layer_real_name': layer.getRealName(),
                'required_crs_list': self.crs_combo_box.currentText().split(';')
                }

            #print(f"{layer.layerID} {layer.layerName} {layer.layerPath} {type(layer.layerPath)}")
        
        # print('Вхідний список шарів:')
        # print(json.dumps(layers_dict, indent=4,ensure_ascii=False))        
        # print(json.dumps(self.strutures, indent=4,ensure_ascii=False))        
        result_structure = run_validator(
            layers = layers_dict,
            structure_folder = self.strutures[self.BGD_type_combo_box.currentText()][self.BGD_version_combo_box.currentText()]['path'])

        # print('\n\n\n\n\nВивід')
        # print(json.dumps(result_structure, indent=4, ensure_ascii=False))
        window = ResultWindow(result_structure, parent=iface.mainWindow())
        window.show()

    def printSelectedLayerData(self):
        for item in self.layer_list_widget.selectedItems():
            print(item.get_layer_vlaue())

    def openFiles(self, addLayers:bool = False):
        def random_id(layerName):
            randomid = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(36))
            return f"⁂{layerName}_{randomid}"
        
        pathArr=QFileDialog.getOpenFileNames(None,"Виберіть файл(файли) для імпорту", self.folder_path, "Geopackage (*.gpkg);;GeoJSON (*.json, *.geojson);;GeoDatabase (*.gdb)")[0]
        if pathArr==[]:
            print('Нічого не вибрано!')
            return
        
        self.folder_path=os.path.dirname(pathArr[0])
        type = pathArr[0].split('.')[-1]

        layersList = []

        for path in pathArr:
            if type in ['json','geojson']:
                #print(path)
                ds  = ogr.Open(path, 0)
                if ds is None:
                    print('Could not open %s' % (path))
                    continue
                layer = ds.GetLayer()
                layerName = layer.GetName()
                id = random_id(layerName)
                layersList.append(layerItem(id=id, visible_name=layerName, real_name=layerName, path=path))

            elif type=='gpkg':
                ds = ogr.Open(path)
                if ds is None:
                    QMessageBox.critical(None, "Помилка", f"Файл {path} пошкоджено")
                
                tempLayersList = []
                for i in range(ds.GetLayerCount()):
                    layer = ds.GetLayerByIndex(i)
                    layerName = layer.GetName()
                    obj_qty = layer.GetFeatureCount()
                    id = random_id(layerName)
                    layerpath = path

                    tempLayersList.append(layerItem(id=id, visible_name=layerName, real_name=layerName, path=path, features_qty = obj_qty))
                
                lsDialog = layerSelectionDialog(tempLayersList, parent=self)
                errors_list = []
                if lsDialog.exec_() == 1:
                    layersList = lsDialog.get_selected_layers()
                    
                    # for item in layersList:
                    #     datachecker =  ogr.Open(path, 0)
                    #     layer = datachecker.GetLayerByName(item.getRealName())
                    #     if layer is None:
                    #         errors_list.append(item)
                    #         continue
                    #     layersList.append(item)
                    

                if len(errors_list) > 0: QMessageBox.critical(None, "Помилка", '\r\n'.join([f"Шар '{item.getLayerName()}', файлу '{path}' пошкоджено" for item in errors_list]))
                lsDialog = None

        if not addLayers:
            self.layer_list_widget.clear()
        
        for layer in layersList:
            self.layer_list_widget.addTopLevelItem(layer)
            
    def make_layer_item_from_layer(self, layer):
        layerID = layer.id()
        layerVisibleName = layer.name()
        layerRealName = get_real_layer_name(layer)
        layerPath = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.dataProvider().dataSourceUri())['path']
        features_qty = layer.featureCount()
        layer_item = layerItem(id = layerID, visible_name=layerVisibleName, real_name= layerRealName, path = layerPath, features_qty = features_qty)
        return layer_item

    def update_layers(self):
        self.layer_list_widget.clear()
        for layer in iface.layerTreeView().selectedLayersRecursive():
            self.layer_list_widget.addTopLevelItem(self.make_layer_item_from_layer(layer))
    
    def add_selected_layers(self):
        for layer in iface.layerTreeView().selectedLayersRecursive():
            self.layer_list_widget.addTopLevelItem(self.make_layer_item_from_layer(layer))
        
    def show_context_menu(self, position):
        if self.layer_list_widget.selectedItems() == []:
            return
        
        selected_item = self.layer_list_widget.selectedItems()[0]
        selected_item = cast(layerItem, selected_item)

        if selected_item is not None:
            #print(selected_item)
            menu = QMenu(self)
            if selected_item.isConnected():
                layer = QgsProject.instance().mapLayer(selected_item.__layerID__)
                if layer:
                    related_layer = layer
                    menu.addAction("Виділити шар")
                    menu.addAction("Перейти в налаштування шару")
                    menu.addAction("Переглянуи таблицю атрибутів шару")
                    menu.addSeparator()
                else:
                    related_layer =  None
                
            menu.addAction("Видалити шар")
            
            if menu.isEmpty():
                return
            
            selected_action = menu.exec_(QCursor.pos())

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

                # print(f"Вибрано дію: {selected_action.text()}")
    
# window = MainWindow(parent=iface.mainWindow())
# 
# window.show()
