from re import split
import re
from typing import Union, cast 
from PyQt5.QtWidgets import QTreeWidget, QTreeWidgetItem, QApplication, QVBoxLayout, QHBoxLayout, \
    QWidget, QDialog, QTreeView, QPushButton, QFileDialog, QMenu, QFrame, QComboBox, QMessageBox, QAbstractItemView, QLabel

from PyQt5.QtWidgets import QSizePolicy, QAction

from PyQt5.QtCore import Qt, QMimeData, QSize, QUrl
from PyQt5.QtGui import QCursor, QIcon, QDesktopServices, QPixmap, QKeySequence
from numpy import unicode_
from qgis.core import (
    QgsProject, QgsLayerTreeLayer, QgsLayerTreeModel, QgsTask, QgsApplication,
    QgsLayerTree, QgsProviderRegistry, QgsVectorLayer, QgsMapLayerType, QgsMessageLog, Qgis)
from qgis.utils import iface
from qgis.gui import QgsLayerTreeView
import sys, os, string, random
from osgeo import ogr
import json

from .csv_to_json_structure_converter import Csv_to_json_structure_converter

from .benchmark import Benchmark

from .result_windows import ResultWindow, CustomTreeView, CustomItemModel


from .checker_class import EDRA_exchange_layer_checker, EDRA_validator

import gc

from .sidefunctions import log, save_dict_as_file, save_validator_log, compress_last_validation_folder
from .sidefunctions import validator_name, validator_icon



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

def run_validator(task:QgsTask = None, input_list:list = None):
    """
    Запустити валідатор для шарів.

    Args:
        task (QgsTask, optional): Об'єкт QgsTask для валідатора. Дефолтне значення None.

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
    def validate_file_format(path: str, reuired_format: str) -> bool:
        """
        Перевіряє, чи файл має заданий формат.

        Args:
            path (str): Шлях до фаєлу.
            reuired_format (str): Формат, який потрібно перевірити.

        Returns:
            bool: True, якщо фаєл має заданий формат, інакше False.
        """
        file_extension = os.path.splitext(path)[1]
        return file_extension in reuired_format
    
    save_dict_as_file(input_list, 'input_list_for_run_validator', file_dir = os.path.join(os.path.dirname(__file__), 'last_validation'))

    layers = input_list[0]
    structure_folder = input_list[1]
    output = []
    all_layers_check_result_dict = {
        'layers': {}, 
        'exchange_format_error': [], 
        'missing_layers': []}

    temp_files_dict = {}

    global_guid_dict = {}
    damaged_files_list = []

    #print('start run_validator.................')
    for id in layers:
        file_path = layers[id]['path']
        
        if file_path in damaged_files_list: #відпрацювання скіпу перевірки якшо файл вже перевірявся і він битий
            continue
        log(f"Пробую відкрити файл {file_path}...")
        dataSource = ogr.Open(file_path, 0)
        
        if dataSource is None: #відпрацювання скіпу перевірки якшо файл битий
            temp_files_dict[file_path] = {
                'type' : 'inspection',
                'item_name' :  f"[AF1]Помилка завантаження файлу «{os.path.basename(file_path)}»",
                'related_file_path' : file_path,
                'item_tooltip' : f"(Запоровся на шарі {layers[id]['layer_name']}){file_path}",
                'criticity' : 2
            }
            damaged_files_list.append(file_path)
            continue

        if not file_path in temp_files_dict: 
            temp_files_dict[file_path] = {
                'type' : 'file',
                'item_name' :  f"Файл: «{os.path.basename(file_path)}»",
                'related_file_path' : file_path,
                'item_tooltip' : file_path,
                'subitems' : []
            }
        
        if dataSource.GetDriver().GetName() in ['OpenFileGDB', 'GPKG']:
            layer = dataSource.GetLayerByName(layers[id]['layer_real_name'])
        else:
            layer = dataSource.GetLayer()
        
        layer_real_name = layers[id]['layer_real_name']
        
            
        if layer is None:
            temp_files_dict[file_path]['subitems'].append = {
                'type' : 'inspection',
                'item_name' :  f"Помилка завантаження шару «{layers[id]['layer_name']}»",
                'related_file_path' : file_path,
                'item_tooltip' : file_path,
                'criticity' : 2
            }
            continue
            raise AttributeError(f'Не вдалося відкрити шар {layers[id]["path"]}')

        converter = Csv_to_json_structure_converter(structure_folder)

        structure = converter.create_structure_json()
        domains = converter.create_domain_json()
        
        if not validate_file_format(layers[id]['path'], layers[id]['exchange_format']):            
            file_format = os.path.splitext(layers[id]['path'])[1]
            required_format = layers[id]['exchange_format']
            if temp_files_dict[layers[id]['path']]['subitems'] == [] or not f"Формат файлу '{file_format}' не відповідає '{required_format}', що вимагаються структурою" in temp_files_dict[layers[id]['path']]['subitems'][0].values():
                inspection = {
                    'type' : 'inspection',
                    'item_name' :  f"Формат файлу '{file_format}' не відповідає '{required_format}', що вимагаються структурою",
                    'related_file_path' : file_path,
                    'item_tooltip' : file_path,
                    'criticity' : 1
                }
                temp_files_dict[file_path]['subitems'].append(inspection)
        else:
            file_format = os.path.splitext(layers[id]['path'])[1]
            required_format = layers[id]['exchange_format']
            if temp_files_dict[layers[id]['path']]['subitems'] == [] or not f"Формат файлу '{file_format}' відповідає '{required_format}', що вимагаються структурою" in temp_files_dict[layers[id]['path']]['subitems'][0].values():
                inspection = {
                    'type' : 'inspection',
                    'item_name' :  f"Формат файлу '{file_format}' відповідає '{required_format}', що вимагаються структурою",
                    'related_file_path' : file_path,
                    'item_tooltip' : file_path,
                    'criticity' : 0
                }
                temp_files_dict[file_path]['subitems'].append(inspection)
        
        validate_checker = EDRA_exchange_layer_checker(
            layer = layer,
            layer_exchange_name = layer_real_name,
            structure_json = structure,
            domains_json = domains,
            layer_props = layers[id],
            layer_id = id,
            task = task,
            driver_name = dataSource.GetDriver().GetName())
        
        #print(f"Driver name: {dataSource.GetDriver().GetName()}")
        
        validate_result = validate_checker.run()
        

        temp_files_dict[layers[id]['path']]['subitems'].append(validate_result)
        del validate_result
        del validate_checker
        del layer
    
    for k, v in temp_files_dict.items():
        output.append(v)
    
    
    return output

class customlayerListWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderHidden(True)

        self.setDragEnabled(True)

        self.setAcceptDrops(True)

        self.setDropIndicatorShown(True)

        self.setDragDropMode(QTreeWidget.DragDrop)

        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    


    def deleteSelectedItems(self):
        for item in self.selectedItems():
            self.takeTopLevelItem(self.indexOfTopLevelItem(item))

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            self.deleteSelectedItems()
        else:
            super().keyPressEvent(event)

    def addTopLevelItem(self, newItem:QTreeWidgetItem):
        newItem = cast(layerItem, newItem)

        for i in range(self.topLevelItemCount()):
            item = cast(layerItem, self.topLevelItem(i))
            if newItem.get_layer_value() == item.get_layer_value():
                log(f"Шар {newItem.getVisibleName()} вже був доданий", level = Qgis.Warning)
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
        tootip = ''
        if self.__layerVisibleName__ is not None and self.__layerVisibleName__ != "":
            self.setText(0, f"{self.__layerVisibleName__}[{self.__layerFeaturesQty__}]")
            if self.__layerPath__ is not None and self.__layerPath__ != "":
                tootip = f'{self.__layerPath__}\r\n'
            if self.__layerRealName__ is not None and self.__layerRealName__ != "":
                tootip = f'{tootip}{self.__layerRealName__}' 
        else:
            self.setText(0, f"{self.__layerRealName__}[{self.__layerFeaturesQty__}]")
            if self.__layerPath__ is not None and self.__layerPath__ != "":
                tootip = self.__layerPath__

        self.setToolTip(0, tootip)
            
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


class LayerButtonsPanel(QWidget):
    def __init__(self, parent =None):
        def clear_empty_layers():
            log("Видаляю пустиі шари...", level=Qgis.Info)
            for i in reversed(range(parent.layer_list_widget.topLevelItemCount())):
                item = cast(layerItem, parent.layer_list_widget.topLevelItem(i))
                if item and item.getFeaturesQty() == 0:
                    parent.layer_list_widget.takeTopLevelItem(i)
            log("Пусті шари - видалено!", level=Qgis.Info)
        
        super().__init__(parent)
        self.setContentsMargins(0, 0, 0, 0)
        resources_path = os.path.join(os.path.dirname(__file__), 'resources')
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(0, 0, 0, 0)

        # Кнопка "Додати виділені шари"
        self.add_selected_btn = QPushButton()
        self.add_selected_btn.setToolTip("Додати виділені шари з дерева шарів QGIS")
        self.add_selected_btn.setIcon(QIcon(os.path.join(resources_path, 'from_selected.png')))
        self.add_selected_btn.clicked.connect(parent.add_selected_layers)
        layout.addWidget(self.add_selected_btn)
        

        # Кнопка "Додати шари з файлу"
        self.add_from_file_btn = QPushButton()
        self.add_from_file_btn.setToolTip("Додати шари з вибраного файлу")
        self.add_from_file_btn.setIcon(QIcon(os.path.join(resources_path, 'from_file.png')))
        self.add_from_file_btn.clicked.connect(lambda: parent.openFiles(True))
        layout.addWidget(self.add_from_file_btn)

        # Кнопка "Видалити всі пусті шари"
        self.remove_empty_btn = QPushButton()
        self.remove_empty_btn.setToolTip("Видалити всі пусті шари зі списку")
        self.remove_empty_btn.setIcon(QIcon(os.path.join(resources_path, 'clear_empty.png')))
        self.remove_empty_btn.clicked.connect(clear_empty_layers)
        layout.addWidget(self.remove_empty_btn)

        #кнопка видалити всі шари
        self.remove_all_btn = QPushButton()
        self.remove_all_btn.setToolTip("Видалити всі шари зі списку")
        self.remove_all_btn.setIcon(QIcon(os.path.join(resources_path, 'clear_all.png')))
        self.remove_all_btn.clicked.connect(parent.layer_list_widget.clear)
        layout.addWidget(self.remove_all_btn)
        
        layout.addStretch()

        # Кнопка "Відкрити результати перевірки"
        self.open_results_btn = QPushButton()
        self.open_results_btn.setToolTip("Відкрити результати перевірки")
        self.open_results_btn.setIcon(QIcon(os.path.join(resources_path, 'load_validation.png')))
        self.open_results_btn.clicked.connect(parent.open_json)
        layout.addWidget(self.open_results_btn)

        # Розділювач
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator)

        # Кнопка "Відкрити допомогу"
        self.help_btn = QPushButton()
        self.help_btn.setToolTip("Відкрити допомогу")
        self.help_btn.setIcon(QIcon(os.path.join(resources_path, 'help.png')))
        self.help_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.join(os.path.dirname(__file__), 'help', 'index.html'))))
        layout.addWidget(self.help_btn)

        button_size = 32  # або 36, 40, як хочеш
        for btn in [self.add_selected_btn, self.add_from_file_btn, self.remove_empty_btn,
                    self.remove_all_btn, self.open_results_btn, self.help_btn]:
            btn.setIconSize(QSize(button_size, button_size))
            btn.setFixedSize(button_size + 10, button_size + 10)

class LaunchValidationButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)

        # Шлях до картинки-космонавта
        resources_path = os.path.join(os.path.dirname(__file__), 'resources')
        astronaut_path = os.path.join(resources_path, 'run_validator.png')  # заміни на свою назву

        # Встановлення тексту та стилю
        self.setText("  Запустити перевірку  ")  # з відступами
        self.setToolTip("Запустити перевірку відповідності ваших шарів")
        self.setIcon(QIcon(QPixmap(astronaut_path)))
        self.setIconSize(QSize(84, 42))  # підігнано під висоту кнопки

        # Мінімальний і максимальний розмір
        self.setMinimumHeight(42)
        self.setMaximumHeight(42)
        self.setMinimumWidth(350)
        self.setMaximumWidth(640)

        # Автоматичне масштабування по ширині
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # CSS стиль
        self.setStyleSheet("""
            QPushButton {
                background-color: #199ca6;
                color: white;
                font-size: 14px;
                border-radius: 3px;
                padding-left: 12px;
                text-align: left;
                font-weight: bold;
            
            }
            QPushButton:hover {
                background-color: #1fbac0;
            }
            QPushButton:pressed {
                background-color: #188f99;
            }
        """)        




class MainWindow(QDialog):
    def parse_structures(self, directory:str) -> dict:
        """Парсить структури з директорії, повертаючи словник з наступною структурою:
        {
            коротка назва структури: {
                версія: {
                    'path': шлях до версії,
                    'structure_name': Повна назва структури,  
                    'structure_date': Дата створення структури,
                    'author': Автор,
                    'description': Опис структури,
                    'format': Формат структури(json, gdb, geojson...),
                    'crs': Система координат
                }
            }
        }
        """

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
        self.bench = Benchmark("Головне вікно")
        self.bench.start('init')
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
        
        self.validator_result = []

        self.validator_task = ''
        
        self.setWindowTitle(validator_name.strip())
        self.setWindowIcon(validator_icon)
        self.folder_path=os.path.expanduser('~')
        self.filter = ''
        max_height = QApplication.desktop().screenGeometry().height()
        max_width = 640#QApplication.desktop().screenGeometry().width()
        self.setMaximumSize(QSize(max_width-40, max_height-40))

        # Create a QHBoxLayout
        self.side_to_side_layout = QHBoxLayout(self)
        # Create a QVBoxLayout
        layerslayout = QVBoxLayout(self)
        self.ll = layerslayout
        
        layerslayout.addWidget(QLabel("Шари до валідації:"))

        self.layer_list_widget = customlayerListWidget()
        self.layer_list_widget.setMinimumHeight(400)
        #self.layer_list_widget.customContextMenuRequested.connect(self.show_context_menu)
        self.layer_list_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.layer_list_widget.setContextMenuPolicy(Qt.ActionsContextMenu)
        delete_action = QAction("Видалити виділений елемент", self)
        delete_action.setShortcut(QKeySequence.Delete)
        delete_action.triggered.connect(self.layer_list_widget.deleteSelectedItems)
        self.layer_list_widget.addAction(delete_action)
        # Add the tree view to the layout
        layerslayout.addWidget(self.layer_list_widget)
        
        
        self.plugin_dir = os.path.dirname(__file__)
        self.path_to_structures = os.path.join(self.plugin_dir, 'stuctures')
        self.strutures = self.parse_structures(self.path_to_structures)
        
        self.BGD_type_combo_box = QComboBox()
        self.BGD_type_combo_box.addItems(self.strutures.keys())
        for i in range(self.BGD_type_combo_box.count()):
            version_index = [key for key in self.strutures[self.BGD_type_combo_box.itemText(i)].keys()][0]
            self.BGD_type_combo_box.setItemData(i, self.strutures[self.BGD_type_combo_box.itemText(i)][version_index]['structure_name'], Qt.ToolTipRole)

        self.BGD_version_combo_box = QComboBox()
        update_version_combo_box()
        
        self.crs_combo_box = QComboBox()
        update_crs_combo_box()
        
        self.BGD_type_combo_box.currentIndexChanged.connect(update_version_combo_box)
        self.BGD_version_combo_box.currentIndexChanged.connect(update_crs_combo_box)

        layerslayout.addWidget(self.BGD_type_combo_box)
        layerslayout.addWidget(self.BGD_version_combo_box)
        layerslayout.addWidget(self.crs_combo_box)
        self.runButton = QPushButton("Запустити перевірку")
        self.runButton = LaunchValidationButton()
        self.runButton.clicked.connect(self.run)
        
        self.runLayout = QHBoxLayout()
        self.runLayout.addWidget(self.runButton)
        layerslayout.addLayout(self.runLayout)
        self.sidebar = LayerButtonsPanel(self)
        self.side_to_side_layout.addWidget(self.sidebar)
        self.side_to_side_layout.addLayout(layerslayout)
        self.setLayout(self.side_to_side_layout)
        self.bench.stop()
    
    def get_BGD_type(self):
        """Повертає тип МБД вибраний в комбобоксі"""
        return self.BGD_type_combo_box.currentText()
    
    def get_BGD_version(self):
        """Повертає версію МБД вибраний в комбобоксі"""
        return self.BGD_version_combo_box.currentText()
    
    def get_crs(self):
        """Повертає систему координат вибрану в комбобоксі"""
        return self.crs_combo_box.currentText()

    def open_json(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFile)
        file_dialog.setWindowTitle("Виберіть файл з результатом перевірки")
        file_dialog.setNameFilter("JSON files (*.json)")
        file_dialog.setDirectory(self.folder_path)
        if file_dialog.exec_():
            path = file_dialog.selectedFiles()[0]
            self.folder_path = os.path.dirname(path)
            with open(path, 'r', encoding='utf-8') as f:
                result_list = json.load(f)
            if result_list:
                self.folder_path=os.path.dirname(path)
                window = ResultWindow(result_list, parent=self)
                window.show()

    def run(self):
        def обробник(помилка, результат = None):
            print('обробник')
            if помилка is None:
                print('помилка is None')
                if результат is None:
                    print('результат is None')
                    pass
                else:
                    #self.validator_result = результат
                    print('Запускаю вікно результату')
                    window = ResultWindow(результат, parent=self)
                    print("Вікно результату запущено")
                    window.show()
            else:
                print(помилка)
                raise помилка
        
        log(f"Запуск перевірки: {self.get_BGD_type()}({self.get_BGD_version()}){self.get_crs()[:100]}...", level = Qgis.Info)
        layers_dict = {}
        structure_folder = self.strutures[self.get_BGD_type()][self.get_BGD_version()]['path']
        #print(json.dumps(self.strutures, indent=4, ensure_ascii=False))
        self.bench.start('run')
        
        for i in range(self.layer_list_widget.topLevelItemCount()):
            layer = self.layer_list_widget.topLevelItem(i)
            layer = cast(layerItem, layer)
            
            crs_text = self.strutures[self.get_BGD_type()][self.get_BGD_version()]['crs'][self.get_crs()]
            crs_list = crs_text.replace(' ', '').replace('\r', '').replace('\n', '').replace('\t', '').replace(';', ',').split(',')
            
            required_file_format = self.strutures[self.get_BGD_type()][self.get_BGD_version()]['format']
            #print(required_file_format)

            layers_dict[layer.getID()] = {
                'layer_name': layer.getVisibleName() or layer.getRealName(),
                'path': layer.getPath(),
                'layer_real_name': layer.getRealName(),
                'required_crs_list': crs_list,
                'exchange_format': required_file_format
                }
            
        layers_output = '\n'.join([f"\t{i+1}. {layer_id} - {layer_info['layer_real_name']}({os.path.basename(layer_info['path'])})" 
                        for i, (layer_id, layer_info) in enumerate(layers_dict.items())])
        log(f"Перевіряю шари:\n{layers_output}", level=Qgis.Info)

        input = [layers_dict, structure_folder]
        #self.bench.start('run_validator')
        result_list = run_validator(task = None, input_list = input)
        save_dict_as_file(result_list, 'run_validator_result', os.path.join(os.path.dirname(__file__), 'last_validation'))
        #self.bench.start('result_window')
        window = ResultWindow(result_list, parent=self)
        #self.bench.start('show_window')
        window.show()
        #compress_last_validation_folder()
        #self.bench.stop()
        #self.bench.print_report()

        # self.validator_task = QgsTask.fromFunction('Валідую валідую, та не вивалідую', run_validator, on_finished = обробник, input_list = input)
        # tm = QgsApplication.taskManager()
        # tm.addTask(self.validator_task)
        
        # result_structure = run_validator(
        #     layers = layers_dict,
        #     structure_folder = self.strutures[self.BGD_type_combo_box.currentText()][self.BGD_version_combo_box.currentText()]['path'])
        
        # window = ResultWindow(result_structure, parent=self)#iface.mainWindow())
        # window.show()

    def openFiles(self, addLayers:bool = False):
        def random_id(layerName):
            randomid = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(36))
            return f"⁂{layerName}_{randomid}"

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.ExistingFiles)
        file_dialog.setWindowTitle("Виберіть файл(файли) для імпорту")
        file_dialog.setNameFilter("Geopackage (*.gpkg);;GeoJSON (*.json, *.geojson);;GeoDatabase (gdb);;Shapefile (*.shp)")
        if self.filter != '': 
            file_dialog.selectNameFilter(self.filter)

        file_dialog.setDirectory(self.folder_path)

        if file_dialog.exec_():
            pathArr = file_dialog.selectedFiles()
            self.filter = file_dialog.selectedNameFilter()
        else:            
            log(f"OpenFile: Нічого не вибрано")
            return
        
        self.folder_path=os.path.dirname(pathArr[0])
        file_type = pathArr[0].split('.')[-1]
        log(f"OpenFile: Вибрано {len(pathArr)} файл(ів) з типом {file_type}")

        layersList = []

        for path in pathArr:
            if file_type in ['json','geojson', 'shp']:
                #print(path)
                ds  = ogr.Open(path, 0)
                if ds is None:
                    log(f"OpenFile: Неможливо відкрити файл {path}", Qgis.Warning)
                    continue
                
                layer = ds.GetLayer()
                
                if file_type in ['geojson', 'json']:
                    layerName = os.path.splitext(os.path.basename(path))[0]
                else:
                    layerName = layer.GetName()
                
                obj_qty = layer.GetFeatureCount()
                id = random_id(layerName)
                layersList.append(layerItem(id=id, visible_name=layerName, real_name=layerName, path=path, features_qty = obj_qty))
            
            elif file_type == 'gdb/gdb':
                gbd_path = os.path.dirname(path)
                ds = ogr.Open(gbd_path)
                if ds is None:
                    QMessageBox.critical(None, "Помилка", f"Файл {path} пошкоджено")
                tempLayersList = []
                for i in range(ds.GetLayerCount()):
                    layer = ds.GetLayerByIndex(i)
                    layerName = layer.GetName()
                    obj_qty = layer.GetFeatureCount()
                    id = random_id(layerName)
                    tempLayersList.append(layerItem(id=id, visible_name=layerName, real_name=layerName, path=gbd_path, features_qty = obj_qty))
                
                lsDialog = layerSelectionDialog(tempLayersList, parent=self)
                errors_list = []
                if lsDialog.exec_() == 1:
                    layersList = lsDialog.get_selected_layers()

            elif file_type=='gpkg':
                ds = ogr.Open(path)
                if ds is None:
                    QMessageBox.critical(None, "Помилка", f"Файл {path} пошкоджено")
                
                tempLayersList = []
                for i in range(ds.GetLayerCount()):
                    layer = ds.GetLayerByIndex(i)
                    layerName = layer.GetName()
                    obj_qty = layer.GetFeatureCount()
                    id = random_id(layerName)
                    tempLayersList.append(layerItem(id=id, visible_name=layerName, real_name=layerName, path=path, features_qty = obj_qty))
                
                lsDialog = layerSelectionDialog(tempLayersList, parent=self)
                errors_list = []
                if lsDialog.exec_() == 1:
                    layersList = lsDialog.get_selected_layers()

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
        dataURI = QgsProviderRegistry.instance().decodeUri(layer.dataProvider().name(), layer.dataProvider().dataSourceUri())
        if 'path' not in dataURI:
            log(f"Не можу додати шар '{layerVisibleName}' - Тимчасовий", level=Qgis.Warning)
            iface.messageBar().pushWarning(validator_name,f"Не можу додати шар '{layerVisibleName}' - Тимчасовий")
            return None
        
        layerPath = dataURI['path']
        features_qty = layer.featureCount()
        layer_item = layerItem(
            id = layerID, 
            visible_name = layerVisibleName, 
            real_name = layerRealName, 
            path = layerPath, 
            features_qty = features_qty)
        
        return layer_item

    def update_layers(self):
        self.layer_list_widget.clear()
        for layer in iface.layerTreeView().selectedLayersRecursive():
            if layer.type() == QgsMapLayerType.VectorLayer:
                self.layer_list_widget.addTopLevelItem(self.make_layer_item_from_layer(layer))
        
    def update_layers_with_objects(self):
        self.layer_list_widget.clear()
        for layer in iface.layerTreeView().selectedLayersRecursive():
            if layer.type() == QgsMapLayerType.VectorLayer and layer.featureCount() > 0:
                self.layer_list_widget.addTopLevelItem(self.make_layer_item_from_layer(layer))

    def add_selected_layers(self):
        for layer in iface.layerTreeView().selectedLayersRecursive():
            if layer.type() != QgsMapLayerType.VectorLayer:
                log(f"Не можу додати шар '{layer.name()}' - не векторний", level=Qgis.Warning)
                iface.messageBar().pushWarning(validator_name,f"Не можу додати шар '{layer.name()}' - не векторний")
                continue
            item = self.make_layer_item_from_layer(layer)
            if item is not None:
                self.layer_list_widget.addTopLevelItem(item)

    


    def show_context_menu(self, position):
        log('Колбек на відкриття контекстного меню', level=Qgis.Info)
        if self.layer_list_widget.selectedItems() == []:
            return
        
        selected_items = self.layer_list_widget.selectedItems()

        if len(selected_items) >0:
            menu = QMenu(self)
            
            layers = [QgsProject.instance().mapLayer(selected_item.__layerID__) for selected_item in selected_items if selected_item.isConnected()]
            
            if len(layers) < 0:
                if len(layers) == 1:
                    menu.addAction("Виділити шар")
                    menu.addAction("Перейти в налаштування шару")
                    menu.addAction("Переглянуи таблицю атрибутів шару")
                else:
                    menu.addAction("Виділити шари")
                menu.addSeparator()
                
            if len(layers) == 1: 
                menu.addAction("Видалити шар")
            else:
                menu.addAction("Видалити шари")

            selected_action = menu.exec_(QCursor.pos())

            if selected_action:
                if selected_action.text() == "Виділити шар" or selected_action.text() == "Виділити шари":
                    iface.layerTreeView().setSelectedLayers(layers)
                
                elif selected_action.text() == "Перейти в налаштування шару":
                    iface.showLayerProperties(layers[0])
                
                elif selected_action.text() == "Переглянуи таблицю атрибутів шару":
                    iface.showAttributeTable(layers[0])
                    
                elif selected_action.text() == "Видалити шар" or selected_action.text() == "Видалити шари":
                    for item in selected_items:
                        selected_index = self.layer_list_widget.indexOfTopLevelItem(item)
                        self.layer_list_widget.takeTopLevelItem(selected_index)

