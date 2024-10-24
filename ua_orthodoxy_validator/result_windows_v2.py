
from logging import critical
import json
from math import e
from typing import Union, cast
from numpy import isin, union1d
from qgis.PyQt.QtWidgets import (
    QLabel, QVBoxLayout, QTabWidget, QTreeWidget, QHBoxLayout,
    QPushButton, QApplication, QMenu, QTreeWidgetItem, QDialog, QTextEdit, QWidget, QTreeView
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont, QColor, QPixmap, QIcon, QStandardItemModel, QStandardItem

from qgis.core import QgsProject, QgsProviderRegistry, QgsVectorLayer, QgsFeature, QgsPointXY, QgsFeature
from qgis.utils import iface

from datetime import date

import os, urllib.parse


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

    def __init__(self, IDict: dict):
        '''Конструктор класу InspectionItem.'''
        criticity = IDict.get('criticity', 0)
        colors = ["green", "orange", "red"]
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(colors[criticity]))

        icon = QIcon()
        icon.addPixmap(pixmap)
        
        item_name = IDict.get('item_name')
        if type(item_name) is list and len(item_name) > 0:
            item_name = IDict.get('inspection_type_name', item_name[0]) + ':'
        
        if item_name is None:
            raise AttributeError("Немає значення 'item_name' у даних елемента.")
        
        super().__init__(icon, item_name)  # Викликаємо конструктор батьківського класу
        
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

        self.setEditable(False)

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

    def relatedLayer(self):
        """Отримує відповідний шар."""
        layer_id = self.getData(self.RELATED_LAYER_ID)
        if type(layer_id) is not str or layer_id.startswith('⁂'):
            return None
        
        return get_layer_by_id(layer_id)

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

class MyStandardItemModel(QStandardItemModel):
    def __init__(self):
        super().__init__()
        print("Custom model initialized")
        
    # Custom method to add an item
    def addItem(self, DICT):
        item = InspectionItem(DICT)
        print(item)
        self.appendRow(item)

class CustomItemModel(QStandardItemModel):
    def __init__(self, structure: list = None, parent=None):
        super().__init__(parent)
        if structure is not None: 
            self.fill_model(structure)

    def parse_dict(self, IDict, parent_item: InspectionItem = None):
        item = InspectionItem(IDict)
        children = IDict.get('subitems',[])
        name = IDict.get('item_name')
        #print(json.dumps(IDict, indent=4, ensure_ascii=False))
        if len(children) > 0:
            for child in children:
                self.parse_dict(child, item)
        elif type(name) is list and len(name) > 0:
            for n in name:
                IDict_n = IDict.copy()
                IDict_n['item_name'] = n
                child = InspectionItem(IDict_n)
                item.appendRow(child)

        if parent_item is not None:
            parent_item.appendRow(item)
        else:
            return(item)

    def get_root_element(self):
        """Отримує кореневий елемент моделі."""
        return self.invisibleRootItem()

    def fill_model(self, structure: list):
        for element in structure:
            self.invisibleRootItem().appendRow(self.parse_dict(element))        

class CustomTreeView(QTreeView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderHidden(True)



class ResultWindow(QDialog):
    def __init__(self, errors_table:dict, parent=None):
        super().__init__(parent)
        
        #ініціалізація глобальних змінних
        #словник з результатом перевірки
        self.errors_table = errors_table
    
        # Налаштування основного вікна
        self.setWindowTitle("Результати перевірки")
        
        #self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        
        icon_path = "/resources/Team_logo_c_512.png"
        self.setWindowIcon(QIcon(icon_path))
        
        # Головний вертикальний лейаут
        main_layout = QVBoxLayout(self)

        #дерево помилок
        self.tree_widget = CustomTreeView()
        self.model = CustomItemModel(self.errors_table)
        self.tree_widget.setModel(self.model)

        main_layout.addWidget(self.tree_widget)


        # Поле результату перевірки
        self.result_text_field = QLabel(self)
        self.result_text_field.setAlignment(Qt.AlignCenter)
        self.result_text_field.setMaximumHeight(101)
        self.result_text_field.setMinimumHeight(100)
        font = QFont()
        font.setPointSize(16)
        self.result_text_field.setFont(font)
        self.result_text_field.setStyleSheet("background-color: pink; color: white;")
        self.result_text_field.setText("Заглушка")
        main_layout.addWidget(self.result_text_field)

        # Кнопки управління
        button_layout = QHBoxLayout()
        go_to_error_button = QPushButton("Заглушка", self)
        mark_as_fixed_button = QPushButton("Заглушка", self)
        close_button = QPushButton("Заглушка", self)

        button_layout.addWidget(go_to_error_button)
        button_layout.addWidget(mark_as_fixed_button)
        button_layout.addWidget(close_button)

        main_layout.addLayout(button_layout)

       

        # Підключення контекстного меню до багатошарового списку
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)


    def show_context_menu(self, position):
        canvas = iface.mapCanvas()
        selected_indexes = self.tree_widget.selectedIndexes()
        if selected_indexes:
            selected_item = self.tree_widget.model().itemFromIndex(selected_indexes[0])
            print(selected_item.text())
            selected_item = cast(InspectionItem, selected_item)
        else:
            print("No item selected")
            return    

        if selected_item is not None:
            menu = QMenu(self)
            if selected_item.relatedLayer() is not None:
                related_layer = selected_item.relatedLayer()
                menu.addAction("Виділити шар")
                menu.addAction("Перейти в налаштування шару")
                menu.addAction("Переглянуи таблицю атрибутів шару")
            
            if selected_item.relatedFeature() is not None:
                related_feature = selected_item.relatedFeature()
                if selected_item.relatedLayer() is not None:
                    menu.addAction("Виділити об'єкт")
                    menu.addAction("Виділити та наблизити до об'єкту")
                    menu.addAction("Відкрити форму об'єкту")
                
                menu.addAction("Наблизити до об'єкту")
            else:
                related_feature = None

            

            if menu.isEmpty():
                return
            
            selected_action = menu.exec_(self.mapToGlobal(position))


            if selected_action:
                if selected_action.text() == "Виділити шар":
                    iface.setActiveLayer(related_layer)
                
                elif selected_action.text() == "Перейти в налаштування шару":
                    iface.showLayerProperties(related_layer)
                
                elif selected_action.text() == "Переглянуи таблицю атрибутів шару":
                    if related_feature is not None:
                        atTable = iface.showAttributeTable(related_layer)
                        atTable.filterSelectedFeatures(True)
                    else:
                        iface.showAttributeTable(related_layer)
                    
                elif selected_action.text() == "Виділити об'єкт":
                    print(related_feature.id())
                    related_layer.selectByIds([related_feature.id()])

                elif selected_action.text() == "Виділити та наблизити до об'єкту":
                    print(related_feature.id())
                    related_layer.selectByIds([related_feature.id()])

                    canvas.zoomToSelected(related_layer)

                elif selected_action.text() == "Наблизити до об'єкту":
                    canvas.zoomToFeatureIds(related_layer, [related_feature.id()])

                elif selected_action.text() == "Відкрити форму об'єкту":
                    featureForm = iface.getFeatureForm(related_layer, related_feature)
                    featureForm.show()

                print(f"Вибрано дію: {selected_action.text()}")
