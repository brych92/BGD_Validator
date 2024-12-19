from qgis.PyQt.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QRadioButton, QTabWidget, QCheckBox, QPushButton, QScrollArea
)
from qgis.PyQt.QtGui import QIcon, QFont
from qgis.PyQt.QtCore import Qt, pyqtSignal

class CheckboxFilterWidget(QWidget):
    filtered_items_signal = pyqtSignal(list)

    def __init__(self, items: dict, parent=None):
        super().__init__(parent)
        self.setHidden(True)
        self.main_layout = QVBoxLayout(self)
        
        self.checkboxes = []
        
        
        self.checkboxes_tray =  QWidget(self)
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.checkboxes_tray)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        
        
        self.checkboxes_tray_layout = QVBoxLayout(self.checkboxes_tray)
        self.checkboxes_tray.setLayout(self.checkboxes_tray_layout)

        for k, v in items.items():
            checkbox = QCheckBox(v, self)
            checkbox.setProperty("value", k)
            checkbox.setToolTip(k)
            checkbox.setCheckState(Qt.Checked)
            checkbox.stateChanged.connect(self.filter_items)
            self.checkboxes.append(checkbox)
            self.checkboxes_tray_layout.addWidget(checkbox)
        
        self.checkboxes_tray_layout.addStretch(1)

        self.main_layout.addWidget(self.scroll_area)
        # Create buttons
        self.select_all_button = QPushButton("Всі", self)
        self.select_none_button = QPushButton("Нічого", self)
        #self.filter_button = QPushButton("Відфільтрувати", self)
        
        # Connect buttons to their functions
        self.select_all_button.clicked.connect(self.select_all)
        self.select_none_button.clicked.connect(self.select_none)
        #self.filter_button.clicked.connect(self.filter_items)
        
        self.button_layout = QHBoxLayout()
        # Add buttons to layout
        self.button_layout.addWidget(self.select_all_button)
        self.button_layout.addWidget(self.select_none_button)
        #self.button_layout.addWidget(self.filter_button)
        
        self.main_layout.addLayout(self.button_layout)

    def filter_items(self):
        self.filtered_items_signal.emit(self.get_checked_values())

    def select_all(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def select_none(self):
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def get_checked_values(self):
        checked_values = set()
        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                checked_values.add(checkbox.property("value"))
        return list(checked_values)  # Convert set to list before returning checked_values

class FilterWidget(QWidget):
    file_filtered_signal = pyqtSignal(list)
    layer_filtered_signal = pyqtSignal(list)
    inspection_name_filtered_signal = pyqtSignal(list)

    def __init__(self, parent=None, filtration_dict: dict = None):
        super().__init__(parent)
        self.isShrinked = False
        self.tabs = QTabWidget()
        self.tabs.tabBarClicked.connect(self.tab_clicked)
        
        self.tabs.setTabPosition(QTabWidget.East)
        self.widgets = {}
        self.widgets[0] = CheckboxFilterWidget(filtration_dict['files'], self) 

        self.widgets[1] = CheckboxFilterWidget(filtration_dict['layers'], self)  
        
        self.widgets[2] = CheckboxFilterWidget(filtration_dict['errors'], self)  

        self.add_tab("📄Файли", self.widgets[0])
        self.add_tab("🗂️Шари", self.widgets[1])
        self.add_tab("⚠️Перевірки", self.widgets[2])

        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.tabs)
        
        self.setLayout(self.main_layout)
        
        self.widgets[0].filtered_items_signal.connect(self.file_filtered_signal)
        self.widgets[1].filtered_items_signal.connect(self.layer_filtered_signal)
        self.widgets[2].filtered_items_signal.connect(self.inspection_name_filtered_signal)

        self.tabs.setCurrentIndex(0)
        self.widgets[0].setHidden(True)
        self.tabs.setMaximumWidth(50)
        self.setMaximumWidth(50)
        self.isShrinked = True

    def tab_clicked(self, index):
        if self.isShrinked:
            self.tabs.setCurrentIndex(index)
            self.widgets[index].setHidden(False)
            self.tabs.setMaximumWidth(16777215)
            self.setMaximumWidth(16777215)
            self.isShrinked = False
        else:
            if index != self.tabs.currentIndex():
                self.tabs.setCurrentIndex(index)
            else:
                self.tabs.setCurrentIndex(index)
                self.widgets[index].setHidden(True)
                self.tabs.setMaximumWidth(50)
                self.setMaximumWidth(50)
                self.isShrinked = True

    def add_tab(self, name, widget,icon = None):
        if icon is not None:
            self.tabs.addTab(widget, icon, name)
        else:
            self.tabs.addTab(widget, name)

class SwitchWidget(QWidget):
    changed_signal = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.all_button = QRadioButton("Всі перевірки")
        self.errors_button = QRadioButton("Тільки з помилками")
        self.critical_button = QRadioButton("Тільки критичні")

        self.all_button.setChecked(True)

        layout = QHBoxLayout()
        layout.addWidget(self.critical_button)
        layout.addWidget(self.errors_button)
        layout.addWidget(self.all_button)

        self.setLayout(layout)
        layout.setAlignment(Qt.AlignLeft)
        

        self.all_button.toggled.connect(self.changed)
        self.errors_button.toggled.connect(self.changed)
        self.critical_button.toggled.connect(self.changed)
        
    def changed(self):
        self.changed_signal.emit(self.get_selected())
    

    def get_selected(self):
        if self.all_button.isChecked():
            return [0,1,2]
        elif self.errors_button.isChecked():
            return [1,2]
        elif self.critical_button.isChecked():
            return [2]

class CheckboxesGroup(QWidget):
    checked_values_changed = pyqtSignal(list)
    
    def __init__(self, options: dict = None):
        super().__init__()
        self.options = options
        self.checkboxes = {}
        self.checked_values = []

        self.create_checkboxes()

    def create_checkboxes(self):
        layout = QVBoxLayout()
        if self.options is not None:
            options = self.options
        else:
            options = {
                0: "Всі перевірки", 
                1: "Тільки неуспішні",
                2: "Тільки критичні"
            }

        for k, v in options.items():
            checkbox = QCheckBox(v)
            layout.addWidget(checkbox)
            self.checkboxes[k] = checkbox

        button = QPushButton("Відфільтрувати")
        button.clicked.connect(self.get_checked_values)
        layout.addWidget(button)

        self.setLayout(layout)

    def get_checked_values(self):
        self.checked_values = []
        for k, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                self.checked_values.append(k)
        #print(self.checked_values)
        
        self.checked_values_changed.emit(self.checked_values)
        
        return self.checked_values

class statusWidget(QLabel):
    def __init__(self, model, parent=None):
        super().__init__(parent)
        
        total_inspections = model.inspection_QTY
        warning_qty = model.warning_QTY
        critical_qty = model.critical_QTY
        errors_qty = warning_qty + critical_qty

        
        self.setAlignment(Qt.AlignCenter)
        self.setMaximumHeight(101)
        self.setMinimumHeight(100)
        font = QFont()
        font.setPointSize(16)
        self.setFont(font)
        if errors_qty == 0:
            self.setStyleSheet("background-color: green; color: white;")
            self.setText(f'Проведено {total_inspections} перевірок. \r\nПомилок не виявлено.')
        else:
            self.setStyleSheet("background-color: red; color: white;")
            self.setText(
                f'Проведено {total_inspections} перевірок. \r\nЗ них було виявлено помилки в {errors_qty} перевірках.\r\n({critical_qty} критичних, {warning_qty} важливих).')
