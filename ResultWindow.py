from symbol import eval_input
from typing import Union, cast
from numpy import isin
from qgis.PyQt.QtWidgets import (
    QLabel, QVBoxLayout, QTabWidget, QTreeWidget, QHBoxLayout,
    QPushButton, QApplication, QMenu, QTreeWidgetItem, QDialog, QTextEdit, QWidget
)
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QFont, QColor, QPixmap, QIcon

from qgis.core import QgsProject, QgsProviderRegistry, QgsVectorLayer, QgsFeature
from qgis.utils import iface

from datetime import date

import os


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
    if layer is None:
        return ''
    
    display_field_name = layer.displayField()
    if not display_field_name:
        raise ValueError("The display field name is not set or is invalid.")
    
    print(feature.id())
    
    #field_index = feature.fieldIndex(display_field_name)
    #print(feature.attribute(display_field_name))
    return feature[display_field_name]

def get_index(list_v: list, index: int) -> Union[str, None]:
    """
    Отримує відображальну назву елемента з заданого шару.

    Аргументи:
        layer (QgsVectorLayer): Шар, який містить елемент.
        feature (QgsFeature): Елемент, з якого отримати відображальну назву.

    Повертає:
        будь-який: Відображальна назва елемента.

    Звикання:
        ValueError: Якщо назва поля відображення не встановлена або недействітна.
    """
    if 0 <= index < len(list_v):
        element = list_v[index]
        return element
    else:
        return None    

def get_real_layer_name(layer: QgsVectorLayer) -> str:
    
    """
    Отримує назву реального шару, присутнього у QGIS.

    Аргументи:
        layer (QgsVectorLayer): Шар, з якого отримати назву.

    Повертає:
        str: Назва реального шару.
    """

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

class CustomTreeWidgetItem(QTreeWidgetItem):
    def __init__(self, parent:Union['CustomTreeWidgetItem', QTreeWidget], el_name:str, el_criticity:int = None, el_type:str = None, el_actions:dict = None) -> None:
        if not isinstance(parent, CustomTreeWidgetItem) and not isinstance(parent, QTreeWidget):
            raise TypeError(f"Батьківський елемент має бути 'CustomTreeWidgetItem' або 'QTreeWidget'. Передано - '{type(parent)}'.")
        super().__init__(parent)
        self.el_name = el_name
        self.el_criticity = None

        if not isinstance(el_actions, dict):
            self.action_dict = None
        else:
            self.action_dict = el_actions

        self.action_dict1 = {
            "selectLayer": "layerID",
            "openLyerProperties": "layerID",
            "selectFeature": {
                "layerID": "layerID",
                "featureID": "featureID"},
            "deleteFeature": {
                "layerID": "layerID",
                "featureID": "featureID"},
            "openFeatureForm": {
                "layerID": "layerID",
                "featureID": "featureID"},
            "goToGeometryError": {
                "layerID": "layerID",
                "featureID": "featureID",
                "coord": (1531.5315, 5315.53153)},
            "deleteduplicateNodes": {
                "layerID": "layerID",
                "featureID": "featureID"}
            }
        
        if el_criticity is None:
            self.setCriticity(0)
        else:
            self.setCriticity(el_criticity)
        
        if el_criticity == 2:
            self.addParentCriticalError()
        if el_criticity == 1:
            self.addParentLightError()

        self.children_critical_errors = 0
        
        self.children_light_errors = 0

        
        if el_type in ["Шар", "Поле", "Об'єкт", "Атрибут", "Помилка"]:
            self.el_type = el_type
        else:
            self.el_type = None

        self.updateName()
        self.updateTooltip()
        
    def parent(self) -> 'CustomTreeWidgetItem':
        return super().parent()

    def updateName(self):
        name = self.el_name
        self.setText(0, name)

    def updateTooltip(self):
        errors = ''
        if self.children_critical_errors > 0:
            errors = f"Критичних помилок: {self.children_critical_errors}"
        if self.children_light_errors >0:
            if self.children_critical_errors > 0:
                errors = errors + "\r\n"
            errors = f"{errors}Легких помилок: {self.children_light_errors}"
        if self.children_critical_errors + self.children_light_errors == 0:
            errors = 'Помилки відсутні'
        

        self.setToolTip(0, errors)
        
    def getChildrenCriticalErrors(self) -> int:
        return self.children_critical_errors
    def getChildrenLightErrors(self) -> int:
        return self.children_light_errors

    def setCriticity(self, criticity:int, recursive:bool = True):
        if not isinstance(criticity, int) or not 0 <= criticity <= 2:
            raise ValueError("Criticity must be an integer between 0 and 2")
        if not isinstance(recursive, bool):
            raise ValueError("Recursive must be a boolean")
        
        if self.el_criticity is not None and criticity <= self.el_criticity:
            
            return False
        
        self.el_criticity = criticity
        colors = ["green", "orange", "red"]
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(colors[criticity]))

        icon = QIcon()
        icon.addPixmap(pixmap)
        self.setIcon(0, icon)

        if recursive:
            parent = self.parent()
            if parent is not None:
                parent.setCriticity(criticity)
        return True

    def addCritialError(self):
        self.children_critical_errors += 1
        self.updateTooltip()
        self.addParentCriticalError()
    def addLightError(self):
        self.children_light_errors += 1
        self.updateTooltip()
        self.addParentLightError()
    
    def addParentCriticalError(self):
        parent = self.parent()
        if parent is not None:
            parent.addCritialError()
            return True
        else:
            return False
    def addParentLightError(self):
        parent = self.parent()
        if parent is not None:
            parent.addLightError()
            return True
        else:
            return False

class ErrorTreeWidget(QTreeWidget):
    def __init__(self, parent:QWidget, errors_table:dict):
        super().__init__(parent)

        self.errors_table = errors_table

        self.setColumnCount(1)
        self.setHeaderHidden(True)
        stylesheet = "QTreeWidget { background-image: \
        url('/resources/Background.png');\
        background-repeat: no-repeat;\
        background-size: 100px;} "

        self.setStyleSheet(stylesheet)
        self.add_layers_errors_to_tree()
    
    def getErrorsTable(self) -> dict:
        return self.errors_table
    
    def getTopLevelItems(self) -> list:
        result = []
        for i in range(self.topLevelItemCount()):
            result.append(self.topLevelItem(i))
        return result

    def add_layers_errors_to_tree(self):
        if not isinstance(self.errors_table, dict):
            raise AttributeError("Помилка стврення багатошарового списку помилок: Типи вхідних даних не відповідають описаному типу")
        
        if 'layers' in self.errors_table:
            layers_errors_dict = self.errors_table['layers']
        else:
            layers_errors_dict = {}
        
        project_instance = QgsProject.instance()
        
        for layer_name, value in layers_errors_dict.items():
            if project_instance.mapLayer(value['layer_id']):#mapLayersByName(layer_name):
                layer = project_instance.mapLayer(value['layer_id'])#project_instance.mapLayersByName(layer_name)[0]
                
            else:
                raise AttributeError(f"Шар не знайдено за його ID: {project_instance.mapLayer(value['layer_id'])}")
                
            
            if not isinstance(layer, QgsVectorLayer):
                raise AttributeError(f"Шар не є векторним: {layer_name}")

            layer = cast(QgsVectorLayer, layer)

            #знаходимо спражнє ім'я шару (не тестувалося з gdb базами)
            source_layer_name = get_real_layer_name(layer)
                
            layer_tree_item = CustomTreeWidgetItem(parent=self, el_name=f"Шар: {layer_name}({source_layer_name})", el_type="Шар")

            if "layer_name_errors" in value:
                if isinstance(value['layer_name_errors'], dict) and len(value['layer_name_errors'])>0:
                    layer_main_errors_item = CustomTreeWidgetItem(parent=layer_tree_item, el_name="Помилка імені шару")
                    
                    for err, val in value['layer_name_errors'].items():
                        if err == "general":
                            if get_index(val, 0) == True:
                                field_errors_item = CustomTreeWidgetItem(parent = layer_main_errors_item, el_name = f"Назва класу «{source_layer_name}» не відповідає структурі",el_criticity=2, el_type="Помилка")
                                
                            
                            if get_index(val, 1):
                                pass
                            
                        if err == "capital_leters" and val == True:
                            field_errors_item = CustomTreeWidgetItem(parent = layer_main_errors_item, el_name = f"В назві класу «{source_layer_name}» наявні великі літери", el_criticity=1, el_type="Помилка")
                            
                        
                        if err == "used_alias" and val:
                            field_errors_item = CustomTreeWidgetItem(parent = layer_main_errors_item, el_name = f"Замість назви класу використано псевдонім «{source_layer_name}», вимагається «{val}»", el_criticity=2, el_type="Помилка")
                            
                        
                        if err == "spaces_used" and val == True:
                            field_errors_item = CustomTreeWidgetItem(parent = layer_main_errors_item, el_name = f"В назві класу «{source_layer_name}» наявні пробіли", el_criticity=1, el_type="Помилка")
                else:
                    pass
              
            if "layer_invalid" in value:
                if value['layer_invalid']:
                    layer_main_errors_item = CustomTreeWidgetItem(parent = layer_tree_item, el_name = f"Клас «{source_layer_name}» пошкоджено", el_criticity = 2, el_type = "Помилка")
                    
            if "wrong_geometry_type" in value:
                if value['wrong_geometry_type']:
                    layer_main_errors_item = CustomTreeWidgetItem(parent = layer_tree_item, el_name = f"Невідповідний геометричний тип класу: «{value['wrong_geometry_type'][0]}», вимагається «{value['wrong_geometry_type'][1]}»", el_criticity = 2, el_type="Помилка")
                    
            if "wrong_layer_CRS" in value:
                if value['wrong_layer_CRS']:
                    layer_main_errors_item = CustomTreeWidgetItem(parent = layer_tree_item, el_name = f"Невідповідна СК шару: «{value['wrong_layer_CRS'][0]}», очікується: «{value['wrong_layer_CRS'][0]}»", el_criticity = 2, el_type="Помилка")

            if "field_errors" in value:
                field_errors_main_item = CustomTreeWidgetItem(parent = layer_tree_item, el_name = f"Помилки атрибутів:")
                field_errors = value['field_errors']
                if "missing_fields" in field_errors:
                    if len(field_errors['missing_fields']) > 0:
                        layer_main_errors_item = CustomTreeWidgetItem(parent = field_errors_main_item, el_name = f"Відсутні деякі атрибути класу:")
                        
                        for item in field_errors['missing_fields']:
                            field_errors_item = CustomTreeWidgetItem(parent = layer_main_errors_item, el_name = f"Атрибут: «{item}»", el_criticity = 2, el_type="Помилка")
    
                if "field_name_errors" in field_errors:
                    if field_errors['field_name_errors']:
                        layer_main_errors_item = CustomTreeWidgetItem(parent = field_errors_main_item, el_name = f"Присутні атрибути, назва яких не відповідає структурі:")

                        for field, errors in field_errors['field_name_errors'].items():
                            field_errors_item = CustomTreeWidgetItem(parent = layer_main_errors_item, el_name = f"Атрибут: «{item}»")

                            for err, val in errors.items():                        
                                if err == "general" and get_index(val, 0) == True:
                                    error_item = CustomTreeWidgetItem(parent = field_errors_item, el_name = f"Назва атрибуту «{source_layer_name}» не відповідає структурі", el_criticity = 2, el_type="Помилка")

                                if err == "capital_leters" and val == True:
                                    error_item = CustomTreeWidgetItem(parent = field_errors_item, el_name = f"В назві атрибуту «{source_layer_name}» наявні великі літери", el_criticity = 1, el_type="Помилка")

                                if err == "used_alias" and val:
                                    error_item = CustomTreeWidgetItem(parent = field_errors_item, el_name = f"Замість назви атрибуту використано псевдонім «{source_layer_name}», вимагається «{val}»", el_criticity = 2, el_type="Помилка")

                                if err == "spaces_used" and val == True:
                                    error_item = CustomTreeWidgetItem(parent = field_errors_item, el_name = f"В назві атрибуту «{source_layer_name}» є пробіли", el_criticity = 2, el_type="Помилка")
                                
                                if err == "used_cyrillic" and val == True:
                                    error_item = CustomTreeWidgetItem(parent = field_errors_item, el_name = f"В назві атрибуту «{source_layer_name}» є кирилиця", el_criticity = 2, el_type="Помилка")

                if "wrong_field_type" in value:
                    if len(value['wrong_field_type']) > 0:
                        layer_main_errors_item = CustomTreeWidgetItem(parent = layer_tree_item, el_name = f"Типи атрибутів в класі не відповідають сруктурі:")

                        for field, types in value['wrong_field_type'].items():
                            error_item = CustomTreeWidgetItem(parent = layer_main_errors_item, el_name = f"Атрибт «{field}» має тип:«{get_index(types,0)}», вимагається: «{get_index(types,1)}»", el_criticity = 1, el_type="Помилка")

            if "is_empty" in value:
                if value['is_empty'] == True:
                    layer_main_errors_item = CustomTreeWidgetItem(parent = layer_tree_item, el_name = f"В класі відсутні об'єкти", el_criticity = 2, el_type="Помилка")


            if "features" in value:
                features = value["features"]
                
                if len(features) < 1 or not isinstance(features, dict):
                    raise AttributeError(f"Неправильно задане значення ключа 'features' {layer_name}")
                    
                errors_in_features = CustomTreeWidgetItem(parent = layer_tree_item, el_name = "Помилки в об'єктах:")
                
                for f_id, f_v in features.items():
                    if len(f_v) < 1 or not isinstance(f_v, dict):
                        raise AttributeError(f"Неправильно задане значення параметрів об'єкту ID: {f_id}, шару {layer_name}")
                    
                    current_feature = layer.getFeature(f_id)
                    if current_feature.id() != f_id:
                        raise AttributeError(f"Неправильно задано значення ID: {f_id}, шару {layer_name}")
                    
                    current_feature_name = get_feature_display_name(layer, current_feature)

                    feature_item = CustomTreeWidgetItem(parent = errors_in_features, el_name = f"Об'єкт: '{current_feature_name}({f_id})'")
                    
                    if "geometry errors" in f_v:
                        feature_geom_error = f_v["geometry errors"]
                        if feature_geom_error["empty"]:
                            feature_error_item = CustomTreeWidgetItem(parent = feature_item, el_name = "В об'єкті відсутнє об'єкт геометрії", el_criticity = 2, el_type="Помилка")
                        
                        if feature_geom_error["null"]:
                            feature_error_item = CustomTreeWidgetItem(parent = feature_item, el_name = "Геометрія об'єкту пуста(null)", el_criticity = 2, el_type="Помилка")
                        
                        if feature_geom_error["geometry_type_wrong"]:
                            if len(feature_geom_error["geometry_type_wrong"]) == 2:
                                feature_error_item = CustomTreeWidgetItem(parent = feature_item, el_name = f"Тип геометрії об'єкту не відповідає сруктурі. Наявно {feature_geom_error['geometry_type_wrong'][0]}, вимагається {feature_geom_error['geometry_type_wrong'][1]}", el_criticity = 2, el_type="Помилка")
                            else:
                                feature_error_item = CustomTreeWidgetItem(parent = feature_item, el_name = "Тип геометрії об'єкту не відповідає сруктурі.", el_criticity = 2, el_type="Помилка")

                        if feature_geom_error["validator_error"]:
                            for error in feature_geom_error["validator_error"]:
                                feature_error_item = CustomTreeWidgetItem(parent = feature_item, el_name = error[0], el_criticity = 2, el_type="Помилка")

                        if feature_geom_error["outside_crs_extent"]:
                            feature_error_item = CustomTreeWidgetItem(parent = feature_item, el_name = "Об'єкт виходить за межі екстента системи координат", el_criticity = 1, el_type="Помилка")

                    if "duplicated_GUID" in f_v:
                        feature_error_item = CustomTreeWidgetItem(parent = feature_item, el_name = "Об'єкт має не унікальний GUID", el_criticity = 1, el_type="Помилка")
                        for element in f_v["duplicated_GUID"]:
                            if len(element) != 2:
                                raise AttributeError(f"Неправильно задане значення параметрів словика об'єктів з дублікатами GUID, для об'єкту ID: {f_id}({current_feature_name}), шару {layer_name}")
                            
                            temp_layers = QgsProject.instance().mapLayer(element[1])
                            mapLayersByName(element[1])
                            print(temp_layers)


                            #feature_error_item = CustomTreeWidgetItem(parent = feature_item, el_name = f"Об'єкт ID: '{element[0]}', шару: '{temp_layer.name()}'", el_criticity = 1, el_type="Помилка")

        checked_layers_qty = len(layers_errors_dict)

        layers_qty = self.topLevelItemCount()
        layers_with_errors_qty = self.topLevelItemCount()
        
        self.total_critical_errors = 0
        self.total_light_errors = 0
        for item in self.getTopLevelItems():
            print(type(item))
            if isinstance(item, CustomTreeWidgetItem):
                item = cast(CustomTreeWidgetItem, item)
                self.total_critical_errors += item.getChildrenCriticalErrors()
                self.total_critical_errors += item.getChildrenLightErrors()


        self.setHeaderLabel(f"Перевірено шарів - {layers_qty}, з них з помилками - {layers_with_errors_qty}. Загальна кількість критичних помилок - {self.total_critical_errors+self.total_light_errors}, з них незначних помилок - {self.total_light_errors}")
        

        
        if self.total_critical_errors+self.total_light_errors == 0:
            no_errors_item = CustomTreeWidgetItem(parent = self, el_name = "Помилок в шарах не знайдено. Для детальної інформації дивіться вкладку Звіт")
                        
        


class ResultWindow(QDialog):
    def __init__(self, errors_table:dict):
        super(ResultWindow, self).__init__()
        
        #ініціалізація глобальних змінних
        #словник з результатом перевірки
        self.errors_table = errors_table
        #Основний везультат перевірки 0 - помилок не має 1 - незначчні помилки 2 - наявні критичні помилки
        self.error_severity = 0
    
        # Налаштування основного вікна
        self.setWindowTitle("Результати перевірки")
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowMinMaxButtonsHint)
        
        icon_path = "/resourcesTeam_logo_c_512.png"
        self.setWindowIcon(QIcon(icon_path))
        
        # Головний вертикальний лейаут
        main_layout = QVBoxLayout(self)
        
        
        
        # Панель вкладок
        tab_widget = QTabWidget(self)
        main_layout.addWidget(tab_widget)

        # Поле результату перевірки
        self.result_text_field = QLabel(self)
        self.result_text_field.setAlignment(Qt.AlignCenter)
        self.result_text_field.setMaximumHeight(101)
        self.result_text_field.setMinimumHeight(100)
        font = QFont()
        font.setPointSize(16)
        self.result_text_field.setFont(font)        
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

        # Створення першої вкладки з багатошаровим списком
        self.tree_widget = ErrorTreeWidget(self, self.errors_table)

        # Підключення контекстного меню до багатошарового списку
        self.tree_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        report_widget = QWidget()
        
        report_layout = QVBoxLayout(report_widget)
        
        remark = QLabel(self)
        remark.setText("Уважно ознайомтеся зі звітом перед прийманням документації, звірте кількості та назви шарів")
        report_layout.addWidget(remark)
        
        self.report_widget = QTextEdit(self)
        #self.report_widget.setWordWrap(True)
        #self.report_widget.setAlignment(Qt.AlignTop)
        self.report_widget.setHtml(self.prepare_report_html(self.prepare_report_varaible()))
        report_layout.addWidget(self.report_widget)

        # Додавання багатошарового списку до першої вкладки
        tab_widget.addTab(self.tree_widget, "Дерево помилок")
        tab_widget.addTab(report_widget, "Звіт")

        if self.tree_widget.total_critical_errors+self.tree_widget.total_light_errors == 0:
            self.result_text_field.setStyleSheet("background-color: green; color: white;")
            self.result_text_field.setText("Помилок не знайдено.\r\nПеревірка пройдена!")
        elif self.tree_widget.total_light_errors != 0:
            self.result_text_field.setStyleSheet("background-color: orange; color: white;")
            self.result_text_field.setText("Знайдено незначні помилки.\r\nРекомендуємо повернути документ на допрацювання!")
        elif self.tree_widget.total_critical_errors != 0:
            self.result_text_field.setStyleSheet("background-color: red; color: white;")
            self.result_text_field.setText("Знайдено критичні помилки.\r\nПеревірка не пройдена!")
    

    def show_context_menu(self, position):
        selected_item = self.tree_widget.selectedItems()[0]

        if selected_item is not None:
            print(selected_item)
            item_type = selected_item.whatsThis(0)
            print(item_type)
            menu = QMenu(self)
            if item_type[0:4]=='Шар:':
                menu.addAction("Виділити шар")
                menu.addAction("Перейти в налаштування шару")
                menu.addAction("Переглянуи таблицю атрибутів шару")
                layer_name = item_type[4:]
            else:
                print("empty selection")
                return
            selected_action = menu.exec_(self.mapToGlobal(position))
            if selected_action:
                if selected_action.text() == "Виділити шар":
                    layer_to_select = QgsProject.instance().mapLayersByName(layer_name)[0]
                    iface.setActiveLayer(layer_to_select)
                elif selected_action.text() == "Перейти в налаштування шару":
                    layer_to_select = QgsProject.instance().mapLayersByName(layer_name)[0]
                    iface.showLayerProperties(layer_to_select)
                elif selected_action.text() == "Переглянуи таблицю атрибутів шару":
                    layer_to_select = QgsProject.instance().mapLayersByName(layer_name)[0]
                    iface.showAttributeTable(layer_to_select)   
                
                print(f"Вибрано дію: {selected_action.text()}")

    def set_tree_element_icon(self, element, criticity, recursive=False):
        # Check attribute types
        if not isinstance(element, QTreeWidgetItem):
            raise TypeError("Element must be a QTreeWidgetItem")
        if not isinstance(criticity, int) or not 0 <= criticity <= 2:
            raise ValueError("Criticity must be an integer between 0 and 2")
        if not isinstance(recursive, bool):
            raise ValueError("Recursive must be a boolean")
            
        if self.error_severity < criticity:
            self.error_severity = criticity 

        colors = ["green", "orange", "red"]
        # Define icons based on criticity level
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(colors[criticity]))

        # Create a QLabel to display the icon
        icon = QIcon()
        icon.addPixmap(pixmap)

        # Set the icon at the QTreeWidget level
        element.setIcon(0,icon)

        # Recursively set icon for child elements
        if recursive:
            for i in range(element.childCount()):
                child_element = element.child(i)
                self.set_tree_element_icon(child_element, criticity, recursive)


    def prepare_report_string(self, variable=''):
        return ''
        result=''
        project = QgsProject.instance()

        # Get a list of all layers in the project
        all_layers = project.mapLayers()
        
        for name, layer in all_layers.items():
            if isinstance(layer, QgsVectorLayer) and layer.name().endswith("_metadata"):
                if layer and layer.featureCount()>0:
                    feature = next(layer.getFeatures())
                    
                    if 'title' in feature.attributeMap() and feature['title']:
                        title = str(feature['title']).replace('\n', ' ')
                    if 'company_name' in feature.attributeMap() and feature['company_name']:
                        company_name = str(feature['company_name'])
                    if 'decision_authority' in feature.attributeMap() and feature['decision_authority']:
                        decision_authority = str(feature['decision_authority'])
                    if 'decision_date' in feature.attributeMap() and feature['decision_date']:
                        decision_date = feature['decision_date'].toPyDate()
                    if 'decision_number' in feature.attributeMap() and feature['decision_number']:
                        decision_number = str(feature['decision_number'])
                        
        if title:
            result = result + F"\r\n\tЗгідно проведеної перевірки обмінних файлів базги геоданих документу «{title}»"
        if company_name or decision_authority:
            result = result + ", розробленої"
        if company_name:    
            result = result + F" {company_name}"
        if decision_authority:
            result = result + F" на основі рішення, що прийняла {decision_authority}"
            if decision_number:
                result = result + F" №{decision_number}"
                if decision_date:
                    result = result+ F" від {decision_date}"
       
        result = result + f".\r\n\r\n\tПід час перевірки було оброблено {variable['total_layers_qty']} шарів"
        
        if variable["error_layers_qty"] == 0:
            result = result + f".\r\n\tВ перевірених шарах помилок не знайдено."
        else:
            result = result + f", з яких {variable['error_layers_qty']} мають помилки.\r\n\r\n"
        
        result = result + f"\tБули перевірені наступні шари:\r\n\r\n"
        layers_table = variable["layers"]
        
        counter = 1
        
        for layer_name, value in layers_table.items():
            s_name = value["source_name"]
            result = result + f"\t{counter}.\tШар «{layer_name}»({s_name})"
            if "errors" not in value:
                result = result + f" - помилки відсутні;\r\n\r\n"
            else:
                result = result + f":\r\n"
                for error in value["errors"]:
                    result = result + f"\t\t{error};\r\n"
                result = result + "\r\n"
            counter = counter + 1
        
        if variable["error_layers_qty"] == 0 or not "exchange format error" in variable:
            result = result + f"\r\n\r\n\tЗа результатами перевірки база геоданих допускається до прийняття.\r\n\r\n"
        else:
            if "exchange format error" in variable:
                result = result + f"\t{variable['exchange format error']}\r\n"
            result = result + f"\r\n\r\n\tЗа результатами перевірки база геоданих не допускається до прийняття. Пропонуємо повернути документ на опрацювання!\r\n\r\n"
        
            
        result = result + f"\t________________\t\t\t\t\t\t\t{date.today()}"
        print(result)
        return result
    
    def prepare_report_html(self, variable=''):
        return ''
        result = ''

        project = QgsProject.instance()

        # Get a list of all layers in the project
        all_layers = project.mapLayers()
        
        title = False
        company_name = False
        decision_authority = False
        decision_date = False
        decision_number = False
        
        
        for name, layer in all_layers.items():
            if isinstance(layer, QgsVectorLayer) and layer.name().endswith("_metadata"):
                if layer and layer.featureCount() > 0:
                    feature = next(layer.getFeatures())

                    if 'title' in feature.attributeMap() and feature['title']:
                        title = str(feature['title']).replace('\n', ' ')
                    if 'company_name' in feature.attributeMap() and feature['company_name']:
                        company_name = str(feature['company_name'])
                    if 'decision_authority' in feature.attributeMap() and feature['decision_authority']:
                        decision_authority = str(feature['decision_authority'])
                    if 'decision_date' in feature.attributeMap() and feature['decision_date']:
                        decision_date = feature['decision_date'].toPyDate()
                    if 'decision_number' in feature.attributeMap() and feature['decision_number']:
                        decision_number = str(feature['decision_number'])

        result += "<h2>Результати перевірки бази геоданих</h2>\n"

        if title:
            result += F"<p>Згідно проведеної перевірки обмінних файлів базги геоданих документу <b>«{title}»</b>"
        if company_name or decision_authority:
            result += ", розробленої"
        if company_name:
            result += F" {company_name}"
        if decision_authority:
            result += F" на основі рішення, що прийняла {decision_authority}"
            if decision_number:
                result += F" №{decision_number}"
                if decision_date:
                    result += F" від {decision_date}"

        result += F".</p>\n<p>Під час перевірки було оброблено {variable['total_layers_qty']} шарів"

        if variable["error_layers_qty"] == 0:
            result += ". В перевірених шарах помилок не знайдено.</p>\n"
        else:
            result += F", з яких {variable['error_layers_qty']} мають помилки.</p>\n"

        result += "<p>Були перевірені наступні шари:</p>\n<ol>\n"

        layers_table = variable["layers"]

        counter = 1

        for layer_name, value in layers_table.items():
            s_name = value["source_name"]
            result += F"<li>Шар «{layer_name}»({s_name})"
            if "errors" not in value:
                result += " - помилки відсутні;</li>\n"
            else:
                result += ":</li>\n<ul>\n"
                for error in value["errors"]:
                    result += F"<li>{error};</li>\n"
                result += "</ul>\n"
        
            counter += 1
        
        result += "</ol>\n"
        
        if variable["error_layers_qty"] == 0 or not "exchange format error" in variable:
            result += "<p>За результатами перевірки база геоданих допускається до прийняття.</p>\n"
        else:
            if "exchange format error" in variable:
                result += F"<p>{variable['exchange format error']}</p>\n"
            result += "<p>За результатами перевірки база геоданих не допускається до прийняття. " \
                      "Пропонуємо повернути документ на опрацювання!</p>\n<p></p><p></p>"

        
        result +='<table width: 500px;">' \
             '<col style="width:20%">' \
             '<col style="width:20%">' \
             '<col style="width:20%">' \
             '<col style="width:20%">' \
             '<col style="width:20%">' \
             '<tr>' \
             f'<td>{date.today()}</td>' \
             '<td>                                                                         </td>' \
             '<td>________________</td>' \
             '<td>                                                                         </td>' \
             '<td>_________________</td>' \
             '</tr>' \
             '</table>'


        print(result)
        return result
    
    def prepare_report_varaible(self):
        return {}
        base = self.errors_table
        result = {}
        
        
        project = QgsProject.instance()
        all_layers = project.mapLayers()
        
        if "total layers" in self.errors_table:
            result["total_layers_qty"] = self.errors_table["total layers"]
        else:
            result["total_layers_qty"] = len(all_layers)
        
        if "layers" in self.errors_table:
            result["error_layers_qty"] = len(self.errors_table["layers"])
        else:
            result["error_layers_qty"] = 0
        
        result["layers"]={}    
        for name, layer in all_layers.items():
            #print(layer.name())
            if isinstance(layer, QgsVectorLayer):
                name = layer.name()
                source_name = self.get_real_layer_name(layer)
                result["layers"][name] = {"source_name" : source_name}
                result["layers"][name]["errors"] = ["sdfsdfsdf","32rfwefef","32rfewdfwe"]
                
        if "exchange format error" in self.errors_table:
            err = self.errors_table["exchange format error"]
            if len(err) == 2:
                result["exchange format error"] = f"Також прошу зауважити, що обмінний файл подано у форматі {err[0]}, що недопустимо згідно чинного законодавства. Пропонуємо конвертувати обмінний файл в один з наступних форматів {err[1]}, та повторно подати базу геоданих на перевірку."
            if len(err) == 1:
                result["exchange format error"] = f"Також прошу зауважити, що обмінний файл подано у форматі {err[0]}, що недопустимо згідно чинного законодавства. Пропонуємо конвертувати обмінний файл у відповідний формат, та повторно подати базу файли на перевірку."
                
        return result
        
    

    
