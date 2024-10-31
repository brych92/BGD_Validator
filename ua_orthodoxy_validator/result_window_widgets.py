from qgis.PyQt.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, 
    QRadioButton, QTabWidget, QCheckBox, QPushButton
)
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtCore import Qt, pyqtSignal

class CheckboxFilterWidget(QWidget):
    filtered_items_signal = pyqtSignal(list)

    def __init__(self, items: dict, parent=None):
        super().__init__(parent)
        self.setHidden(True)
        self.main_layout = QVBoxLayout(self)
        self.checkboxes = []
        print(items)
        # Create checkboxes for each item
        for k, v in items.items():
            checkbox = QCheckBox(v, self)
            checkbox.setProperty("value", k)
            checkbox.setToolTip(k)
            self.checkboxes.append(checkbox)
            self.main_layout.addWidget(checkbox)
        self.main_layout.addStretch(1)
        # Create buttons
        self.select_all_button = QPushButton("Всі", self)
        self.select_none_button = QPushButton("Нічого", self)
        self.filter_button = QPushButton("Відфільтрувати", self)
        
        # Connect buttons to their functions
        self.select_all_button.clicked.connect(self.select_all)
        self.select_none_button.clicked.connect(self.select_none)
        self.filter_button.clicked.connect(self.filter_items)
        
        self.button_layout = QHBoxLayout()
        # Add buttons to layout
        self.button_layout.addWidget(self.select_all_button)
        self.button_layout.addWidget(self.select_none_button)
        self.button_layout.addWidget(self.filter_button)
        
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
                checked_values.add(checkbox.getProperty("value"))
        return checked_values

class FilterWidget(QWidget):
    def __init__(self, parent=None, filtration_dict: dict = None):
        super().__init__(parent)

        self.tabs = QTabWidget()
        self.tabs.tabBarClicked.connect(self.tab_clicked)
        
        self.tabs.setTabPosition(QTabWidget.East)
        self.widgets = {}
        self.widgets[0] = CheckboxFilterWidget(filtration_dict['files'])  # Replace with your actual widget for files
        self.widgets[1] = CheckboxFilterWidget(filtration_dict['layers'])  # Replace with your actual widget for layers
        self.widgets[2] = CheckboxFilterWidget(filtration_dict['errors'])  # Replace with your actual widget for errors

        

        self.add_tab("📄Файли", self.widgets[0])
        self.add_tab("🗂️Шари", self.widgets[1])
        self.add_tab("⚠️Помилки", self.widgets[2])

        self.main_layout = QHBoxLayout()
        self.main_layout.addWidget(self.tabs)

        self.setLayout(self.main_layout)

    def tab_clicked(self, index):
        if self.tabs.currentIndex() == index:
            if self.widgets[index].isHidden():
                self.widgets[index].setHidden(False)
            else:    
                self.widgets[index].setHidden(True)
                
        else:
            self.tabs.setCurrentIndex(index)

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

        self.errors_button.setChecked(True)

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
