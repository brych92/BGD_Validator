
import sys
from logging import critical, warn
import json
from math import e
from pyexpat import model
from typing import Union, cast
from warnings import filters
from numpy import isin, union1d
from qgis.PyQt.QtWidgets import (
    QLabel, QVBoxLayout, QTabWidget, QTreeWidget, QHBoxLayout,
    QPushButton, QApplication, QMenu, QTreeWidgetItem, QDialog, 
    QTextEdit, QWidget, QTreeView, QCheckBox, QSplitter
)
from qgis.PyQt.QtCore import Qt, QSortFilterProxyModel, QModelIndex, pyqtSignal, pyqtSlot, QUrl, QTimer
from qgis.PyQt.QtGui import QFont, QColor, QPixmap, QIcon, QStandardItemModel, QStandardItem, QDesktopServices

from qgis.core import (
    QgsProject, QgsProviderRegistry, QgsVectorLayer, 
    QgsFeature, QgsPointXY, QgsFeature)
from qgis.utils import iface

from .benchmark import Benchmark

from datetime import date

import os, urllib.parse

from .result_window_widgets import SwitchWidget, FilterWidget, statusWidget, CheckboxesGroup

def get_layer_by_id(layer_id: str) -> QgsVectorLayer:
    """
    Отримує шар за його ID.

    Аргументи:
        layer_id (str): ID шару.

    Повертає:
        QgsVectorLayer: Шар.

    Звикання:
        ValueError: Якщо шар не знайдено.
    """
    layer = QgsProject.instance().mapLayer(layer_id)
    
    if not isinstance(layer, QgsVectorLayer):
        raise TypeError("Помилка отримання шару. Шар має бути обєктом 'QgsVectorLayer'.")
    
    return layer

def get_feature_by_id(layer: QgsVectorLayer, feature_id: int) -> QgsFeature:
    """
    Отримує елемент з шару за його ID.

    Аргументи:
        layer (QgsVectorLayer): Шар, який містить елемент.
        feature_id (int): ID елемента.

    Повертає:
        QgsFeature: Елемент з шару.

    Звикання:
        ValueError: Якщо елемент з шару не знайдено.
    """
    if not isinstance(layer, QgsVectorLayer):
        raise TypeError("Помилка отримання елемента. Шар має бути обєктом 'QgsVectorLayer'.")
    
    feature = layer.getFeature(feature_id)
    if feature.id() != feature_id:
        raise AttributeError(f"Неправильно задано значення ID: {feature_id}, шару {layer.name()}")

    return feature

def get_feature_display_name(layer: QgsVectorLayer, feature: QgsFeature) -> str:
    """
    Отримує відображальну назву елемента з заданого шару.

    Аргументи:
        layer (QgsVectorLayer): Шар, який містить елемент.
        feature (QgsFeature): Елемент, з якого отримати відображальну назву.

    Повертає:
        будь-який: Відображальна назва елемента.

    Звикання:
        ValueError: Якщо назва поля відображення не встановлена або недійсна.
    """
    if not isinstance(layer, QgsVectorLayer):
        raise TypeError("Помилка отримання назви відображення. Шар має бути обєктом 'QgsVectorLayer'.")
    
    display_field_name = layer.displayField()

    if not display_field_name or display_field_name == '':
        result = "без імені"
    else:
        result = feature[display_field_name]

    return result

def get_index(list_v: list, index: int) -> Union[str, None]:
    if 0 <= index < len(list_v):
        element = list_v[index]
        return element
    else:
        return None    

class InspectionItem(QStandardItem):
    '''Клас-контейнер для елементів дерева помилок.
    
    Має такі властивості:
        - тип елемента (TYPE) - може бути 'file'/'layer'/'feature'/'inspection',
        - посилання на сторінку з описом помилки (HELP_URL),
        - повний шлях до файлу (RELATED_FILE_PATH),
        - ідентифікатор шару (RELATED_LAYER_ID),
        - реальна назва шару (REAL_LAYER_NAME),
        - відображувана назва шару (VISIBLE_LAYER_NAME),
        - ідентифікатор об'єкта (RELATED_FEATURE_ID),
        - назва типу перевірки (INSPECTION_TYPE_NAME),
        - критичність помилки (CRITICITY).
    
    '''
    
    TYPE = Qt.UserRole
    HELP_URL = Qt.UserRole + 1
    RELATED_FILE_PATH = Qt.UserRole + 2
    RELATED_LAYER_ID = Qt.UserRole + 3
    REAL_LAYER_NAME = Qt.UserRole + 4
    VISIBLE_LAYER_NAME = Qt.UserRole + 5
    RELATED_FEATURE_ID = Qt.UserRole + 6
    INSPECTION_TYPE_NAME = Qt.UserRole + 7
    CRITICITY = Qt.UserRole + 8

    def set_color(self, criticity):
        colors = ["green", "orange", "red"]
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(colors[criticity]))

        icon = QIcon()
        icon.addPixmap(pixmap)

        self.setIcon(icon)
        self.colorIndex = criticity

    def parent(self): return cast(InspectionItem, super().parent())
    
    def set_parent_color(self, criticity = None):
        if criticity is None:
            criticity = self.getData(self.CRITICITY)
        parent = self.parent()
        if parent is not None:
            if parent.colorIndex <= criticity:
                parent.set_color(criticity)
                parent.set_parent_color(criticity)

    def __init__(self, IDict: dict):
        '''Конструктор класу InspectionItem.'''
        self.colorIndex = 0

        item_name = IDict.get('item_name')
        
        if type(item_name) is list and len(item_name) > 0:
            item_name = IDict.get('inspection_type_name', item_name[0]) + ':'

        if item_name is None:
            raise AttributeError("Немає значення 'item_name' у даних елемента.")
        
        super().__init__(item_name)  # Викликаємо конструктор батьківського класу
        self.set_color(IDict.get('criticity', 0))
        
        item_type = IDict.get('type')
        if item_type is None:
            raise AttributeError("Немає значення 'type' у даних елемента.")
        self.setData(item_name, Qt.DisplayRole)
        self.setData(item_type, self.TYPE)  # Зберігаємо тип елемента
        self.setData(IDict.get('item_tooltip'), Qt.ToolTipRole)

        self.setData(IDict.get('help_url', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygURcmlja3JvbGwgMTAgaG91cnM%3D'), self.HELP_URL)

        self.setData(IDict.get('related_file_path'), self.RELATED_FILE_PATH)

        self.setData(IDict.get('related_layer_id'), self.RELATED_LAYER_ID)

        self.setData(IDict.get('real_layer_name'), self.REAL_LAYER_NAME)

        self.setData(IDict.get('visible_layer_name'), self.VISIBLE_LAYER_NAME)

        self.setData(IDict.get('related_feature_id'), self.RELATED_FEATURE_ID)

        self.setData(IDict.get('inspetcion_type_name'), self.INSPECTION_TYPE_NAME)

        self.setData(IDict.get('criticity', 0), self.CRITICITY)

        self.setEditable(False)# Забороняємо редагування елементів

        #self.set_parent_color(IDict.get('criticity', 0))

    def setErrorGeometry(self, crs, error_points=None, error_polygons=None):
        """Встановлює геометрію помилки."""
        self.error_geometry['crs'] = crs
        self.error_geometry['error_points'] = error_points or []
        self.error_geometry['error_polygons'] = error_polygons or []

    def addCorrespondingObject(self, related_layer_id, related_feature_id, object_GUID, related_feature_visible_name):
        """Додає відповідний об'єкт до списку."""
        corresponding_object = {
            'related_layer_id': related_layer_id,
            'related_feature_id': related_feature_id,
            'object_GUID': object_GUID,
            'related_feature_visible_name': related_feature_visible_name,
        }
        self.corresponding_objects.append(corresponding_object)

    def addCorrection(self, correction_type, current_value, correct_value):
        """Додає виправлення до списку."""
        correction = {
            'correction_type': correction_type,
            'current_value': current_value,
            'correct_value': correct_value,
        }
        self.corrections.append(correction)

    def getData(self, role=Qt.UserRole):
        """Отримує дані елемента для зазначеної ролі."""
        return super().data(role)

    def setData(self, value, role=Qt.UserRole):
        """Встановлює дані елемента для зазначеної ролі."""
        super().setData(value, role)

    def realtedPath(self):
        """Отримує повний шлях до файлу."""
        return self.getData(self.RELATED_FILE_PATH)
    
    def relatedLayer(self):
        """Отримує відповідний шар."""
        layer_id = self.getData(self.RELATED_LAYER_ID)
        if type(layer_id) is not str or layer_id.startswith('⁂'):
            return None
        
        return get_layer_by_id(layer_id)

    def relatedFeatureID(self):
        """Отримує ідентифікатор відповідного об'єкта."""
        return self.getData(self.RELATED_FEATURE_ID)

    def relatedFeature(self) -> Union[QgsFeature, None]:
        """Отримує відповідний об'єкт."""
        feature_id = self.getData(self.RELATED_FEATURE_ID)
        if feature_id is None or type(feature_id) is not int or feature_id < 0:
            return None
        
        layer = self.relatedLayer()
        if layer is None:
            return None
        
        return get_feature_by_id(layer, feature_id)
    
    def __repr__(self):
        """Отримує текстову репрезентацію елемента."""
        return f"InspectionItem('{self.getData(0)}', type={self.getData(self.TYPE)}, criticity={self.getData(self.CRITICITY)})"

class CustomItemModel(QStandardItemModel):
    def __init__(self, structure: list = None, parent=None):
        self.inspection_QTY = 0
        self.critical_QTY = 0
        self.warning_QTY = 0

        self.parse_bench = Benchmark("Item benchmark")

        super().__init__(parent)
        if structure is not None: 
            self.fill_model(structure)

    def parse_dict(self, IDict, parent_item: InspectionItem = None, PIDict = None):
        def copy_key_if_absent(IDict, PIDict, keys:list):
            for key in keys:
                if key not in IDict and key in PIDict:
                    IDict[key] = PIDict[key]

        #if PIDict is not None:
            # self.parse_bench.start('copy_key_if_absent')
            # copy_key_if_absent(IDict, PIDict,
            #     ['item_tooltip',
            #     'help_url', 
            #     'related_file_path', 
            #     'related_layer_id', 
            #     'real_layer_name', 
            #     'visible_layer_name', 
            #     'related_feature_id', 
            #     'inspetcion_type_name'] )
            # self.parse_bench.stop()
        
        self.parse_bench.start('Create inspection item')
        item = InspectionItem(IDict)
        self.parse_bench.stop()

        self.parse_bench.start('parsing 1')
        children = IDict.get('subitems',[])
        name = IDict.get('item_name')
        self.parse_bench.stop()

        if len(children) > 0:
            
            if type(name) is list and len(name) > 0:
                raise Exception(f"Елемент {name} має дочірні елементи, і не має мати спискової назви.")
            
            for child in children:
                self.parse_dict(child, item, IDict)
        
        elif type(name) is list and len(name) > 0:
            #print(json.dumps(IDict, indent=4, ensure_ascii=False))
            self.parse_bench.start('filling false children')
            for n in name:
                IDict_n = IDict.copy()
                IDict_n['item_name'] = n
                child = InspectionItem(IDict_n)
                self.parse_bench.join(child.parse_bench)
                del(child.parse_bench)
                
                item.appendRow(child)
            self.parse_bench.stop()
        
        self.parse_bench.start('append father')       
        if parent_item is not None:
            parent_item.appendRow(item)
            self.parse_bench.stop()
            #print(self.parse_bench.get_report())
        else:
            self.parse_bench.stop()
            #print(self.parse_bench.get_report())
            return(item)

    def get_root_element(self):
        """Отримує кореневий елемент моделі."""
        return self.invisibleRootItem()

    def fill_model(self, structure: list):
        benchi_f = Benchmark("Fill model")
        
        benchi_f.start('fill_model')
        for element in structure:
            root_children = self.parse_dict(element)
            self.invisibleRootItem().appendRow(root_children)
        benchi_f.stop()

        benchi_f.start('update_colors')
        self.update_colors()
        benchi_f.stop()

        benchi_f.start('get_inspections')
        self.get_inspections()
        benchi_f.stop()

        benchi_f.join(self.parse_bench)
        
        print(benchi_f.get_report())

    def get_inspections(self):
        def iterate_model(parent: InspectionItem):
            items = []
            if parent.hasChildren():
                for row in range(parent.rowCount()):
                    child = parent.child(row)
                    items += iterate_model(child)
            if type(parent) is InspectionItem and parent.getData(InspectionItem.TYPE) == 'inspection':
                items.append(parent)
            return items
        
        inspections = iterate_model(self.invisibleRootItem())
        self.inspection_QTY = len(inspections)
        
        self.critical_QTY = len([item for item in inspections if item.getData(InspectionItem.CRITICITY) == 2])
        self.warning_QTY = len([item for item in inspections if item.getData(InspectionItem.CRITICITY) == 1])
        return iterate_model(self.invisibleRootItem())

    def get_all_elements(self)->list[InspectionItem]:
        def iterate_model(parent: InspectionItem):
            items = []
            if parent.hasChildren():
                for row in range(parent.rowCount()):
                    child = parent.child(row)
                    items += iterate_model(child)
            if type(parent) is InspectionItem:
                items.append(parent)
            return items
        
        return iterate_model(self.invisibleRootItem())

    def update_colors(self):
        def iterate_model(parent: InspectionItem):
            items = []
            if parent.hasChildren():
                for row in range(parent.rowCount()):
                    child = parent.child(row)
                    items += iterate_model(child)
            else:
                items.append(parent)
            return items
        
        items  = iterate_model(self.invisibleRootItem())
        if len(items) == 0:
            return

        for item in items:
            if type(item) is InspectionItem:
                item.set_parent_color()

    def get_filtration_dict(self):
        #f_bench = Benchmark("Filtration dict benchmark")
        #f_bench.start('for all item')
        filtration_dict = {'files': {}, 'layers': {}, 'errors': {}}
        for item in self.get_all_elements():
            item_file = item.getData(InspectionItem.RELATED_FILE_PATH)
            if item_file is not None and  item_file != '':
                filtration_dict['files'][item_file] = os.path.basename(item_file)

            item_layer = item.getData(InspectionItem.RELATED_LAYER_ID)
            item_layer_name = item.getData(InspectionItem.VISIBLE_LAYER_NAME)
            if item_layer is not None and item_layer != '':
                filtration_dict['layers'][item_layer] = item_layer_name
            
            item_error = item.getData(InspectionItem.INSPECTION_TYPE_NAME)
            if item_error is not None and item_error != '':
                filtration_dict['errors'][item_error] = item_error
        #f_bench.stop()
        #print(f_bench.get_report())
        return filtration_dict
    
class FilterProxyModel(QSortFilterProxyModel):
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.filter_dict = {
            'criticity': [],
            'type': [],
            'related_file': [],
            'related_layer': [],
            'related_feature': [],
            'inspection_type_name': []
        }

        self.setRecursiveFilteringEnabled(True)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex):
        source_model = self.sourceModel()
        index = source_model.index(source_row, 0, source_parent)
        
        item_data = {
            'criticity': source_model.data(index, InspectionItem.CRITICITY),
            'type': source_model.data(index, InspectionItem.TYPE),
            'related_file': source_model.data(index, InspectionItem.RELATED_FILE_PATH),
            'related_layer': source_model.data(index, InspectionItem.RELATED_LAYER_ID),
            'related_feature': source_model.data(index, InspectionItem.RELATED_FEATURE_ID),
            'inspection_type_name': source_model.data(index, InspectionItem.INSPECTION_TYPE_NAME)
        }
        
        for key, value in self.filter_dict.items():
            if item_data[key] is None:
                continue
            if len(value) > 0 and item_data[key] not in value:
                return False
        
        return True

    
    
    @pyqtSlot(list)
    def filterByCriticity(self, criticity_filter: list):
        self.filter_dict['criticity'] = criticity_filter
        self.invalidateFilter()
    
    @pyqtSlot(list)
    def filterByType(self, type_filter: list):
        self.filter_dict['type'] = type_filter    
        self.invalidateFilter()   

    @pyqtSlot(list)
    def filterByFile(self, related_file_filter: list):
        self.filter_dict['related_file'] = related_file_filter    
        self.invalidateFilter()

    @pyqtSlot(list)
    def filterByLayer(self, related_layer_filter: list):
        self.filter_dict['related_layer'] = related_layer_filter    
        self.invalidateFilter()

    @pyqtSlot(list)
    def filterByInspectionType(self, inspection_type_name_filter: list):
        self.filter_dict['inspection_type_name'] = inspection_type_name_filter    
        self.invalidateFilter()

class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)

class ResultWindow(QDialog):
    def __init__(self, errors_table:dict, parent=None):
        super().__init__(parent)
        self.benchi = Benchmark("Бенчмарк вікна")
        #print(json.dumps(errors_table, indent=4, ensure_ascii=False))
        #ініціалізація глобальних змінних
        #словник з результатом перевірки
        self.errors_table = errors_table
        #ініціалізація моделі
        self.benchi.start('fill_custom_model')
        self.model = CustomItemModel(self.errors_table, parent=self)
        
        
        self.benchi.start('create_proxy_model')
        self.proxyModel = FilterProxyModel(self)
        
        
        self.benchi.start('set_proxy_model')
        self.proxyModel.setSourceModel(self.model)


        self.benchi.start('interface1')
        # Налаштування основного вікна
        self.setWindowTitle("Результати перевірки")
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        
        icon_path = "/resources/Team_logo_c_512.png"
        self.setWindowIcon(QIcon(icon_path))
        
        # Головний вертикальний лейаут
        sidebar_layout = QHBoxLayout(self)
        main_layout = QVBoxLayout()
        sidebar_layout.addLayout(main_layout)
        

        # Поле вибору критичності
        self.criticity_radio = SwitchWidget(self)
        self.criticity_radio.changed_signal.connect(self.proxyModel.filterByCriticity)
        main_layout.addWidget(self.criticity_radio)
        
        self.benchi.stop()

        self.benchi.start('create_tree_widget')
        #дерево помилок
        self.tree_widget = CustomTreeView(self)
        self.benchi.stop()

        self.benchi.start('set_model_to widget')
        self.tree_widget.setModel(self.proxyModel)
        self.benchi.stop()
        self.benchi.start('interface2')
        main_layout.addWidget(self.tree_widget)
        
        self.benchi.stop()

        # Поле результату перевірки
        self.benchi.start('create_status_widget')
        self.result_text_field = statusWidget(self.model, self)
        main_layout.addWidget(self.result_text_field)
        self.benchi.stop()

        self.benchi.start('interface3')

        # Кнопки управління
        button_layout = QHBoxLayout()
        go_to_error_button = QPushButton("Заглушка", self)
        mark_as_fixed_button = QPushButton("Заглушка", self)
        close_button = QPushButton("Заглушка", self)

        button_layout.addWidget(go_to_error_button)
        button_layout.addWidget(mark_as_fixed_button)
        button_layout.addWidget(close_button)

        main_layout.addLayout(button_layout)
        
        filters_layout = QHBoxLayout()
        sidebar_layout.addLayout(filters_layout)
        self.benchi.stop()

        # Фільтрація
        self.benchi.start('create_filter_dict')
        filtration_dict  = self.make_filter_dict()
        self.benchi.stop()
        self.benchi.start('Create filter widget')
        filters_widget = FilterWidget(parent = self, filtration_dict = filtration_dict)
        #self.benchi.join(filters_widget.widget_bench)
        filters_layout.addWidget(filters_widget)
        filters_widget.file_filtered_signal.connect(self.proxyModel.filterByFile)
        filters_widget.layer_filtered_signal.connect(self.proxyModel.filterByLayer)
        filters_widget.inspection_name_filtered_signal.connect(self.proxyModel.filterByInspectionType)
        self.benchi.stop()

        print(self.benchi.get_report())
        # Підключення контекстного меню до багатошарового списку
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)

    def make_filter_dict(self):
        return self.model.get_filtration_dict()

    def closeEvent(self, event):
        print('triggered close event')
        self.deleteLater()
        event.accept()

    def ondelete(self):
        print('triggered delete event')
        self.deleteLater()

    def show_context_menu(self, position):        
        # знайти батьківські атрибути
        def check_attr(item: InspectionItem, attr: str):
            '''Перевіряє, чи є у елемента батьківського атрибуту attr, і якщо є, то повертає його'''
            if type(item) != InspectionItem:
                return None
            
            if attr == 'path':
                if item.realtedPath() is not None:
                    return item.realtedPath()
                elif item.parent() is None:
                    return None
                return check_attr(item.parent(), attr)
            
            elif attr == 'layer':
                if item.relatedLayer() is not None:
                    return item.relatedLayer()
                elif item.parent() is None:
                    return None
                return check_attr(item.parent(), attr)
            
            elif attr == 'feature':
                if item.relatedFeatureID() is not None:
                    return item.relatedFeatureID()
                elif item.parent() is None:
                    return None
                return check_attr(item.parent(), attr)
            else:
                return None

        #Задонатити на ЗСУ
        def donate():
            url = QUrl("https://send.monobank.ua/jar/6v8t4TNdaX")
            QDesktopServices.openUrl(url)

        #відкрити файл
        def open_file(file_path):
            os.startfile(file_path)
        
        #відкрити папку
        def open_folder(file_path):
            folder_path = os.path.dirname(file_path)
            os.startfile(folder_path)

        #виділити та наблизити до об'єкта
        def highlight_and_zoom(layer, feature):
            canvas = iface.mapCanvas()
            layer.selectByIds([feature.id()])
            canvas.zoomToSelected()
        
        #наблизити до не виділеного об'єкту за ід об'єкту та шаром
        def zoom_to_feature(layer, feature):
            canvas = iface.mapCanvas()
            canvas.zoomToFeatureIds(layer, [feature.id()])
        #відкрити форму об''єкта
        def open_feature_form(layer, feature):
            featureForm = iface.getFeatureForm(related_layer, related_feature)
            featureForm.show()

        canvas = iface.mapCanvas()
        proxy_index = self.tree_widget.selectedIndexes()
        
        if proxy_index is None:
            return
        
        proxy_model = self.tree_widget.model()
        proxy_model = cast(FilterProxyModel, proxy_model)
        
        main_model = proxy_model.sourceModel()
        main_model = cast(CustomItemModel, main_model)

        main_index = proxy_model.mapToSource(proxy_index[0])
        
        selected_item = cast(InspectionItem, main_model.itemFromIndex(main_index))
            
        if selected_item is None:
            return
        
        related_path = check_attr(selected_item, 'path')
        related_layer = check_attr(selected_item, 'layer')
        related_feature = check_attr(selected_item, 'feature')

        if related_layer is not None and related_feature is not None:
            related_feature = related_layer.getFeature(related_feature)
        else:
            related_feature = None

        menu = QMenu(self)
        
        menu.addAction("Задонатити на ЗСУ")
        menu.addSeparator()

        if related_path is not None:
            menu.addAction("Відкрити файл")
            menu.addAction("Відкрити папку")
            menu.addSeparator()

        if related_layer is not None:
            menu.addAction("Виділити шар")
            menu.addAction("Перейти в налаштування шару")
            menu.addAction("Переглянуи таблицю атрибутів шару")
            menu.addSeparator()
        
        if related_feature is not None and related_layer is not None:
            menu.addAction("Відкрити форму об'єкту")            
            menu.addAction("Наблизити до об'єкту")
            menu.addAction("Виділити об'єкт")
            menu.addAction("Виділити та наблизити до об'єкту")

        if menu.isEmpty():
            return
        
        selected_action = menu.exec_(self.mapToGlobal(position))

        actions = {
            "Задонатити на ЗСУ": donate,
            "Відкрити файл": lambda: open_file(related_path),
            "Відкрити папку": lambda: open_folder(related_path),
            "Виділити шар": lambda: iface.setActiveLayer(related_layer),
            "Перейти в налаштування шару": lambda: iface.showLayerProperties(related_layer),
            "Переглянуи таблицю атрибутів шару": lambda: iface.showAttributeTable(related_layer),
            "Відкрити форму об'єкту": lambda: open_feature_form(related_layer, related_feature),
            "Наблизити до об'єкту": lambda: zoom_to_feature(related_layer, related_feature),
            "Виділити об'єкт": lambda: related_layer.selectByIds([related_feature.id()]),
            "Виділити та наблизити до об'єкту": lambda: highlight_and_zoom(related_layer, related_feature)
        }

        if selected_action:
            actions[selected_action.text()]()
            return

