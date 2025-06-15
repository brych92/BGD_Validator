from qgis.core import QgsMessageLog, Qgis
from qgis.utils import iface
from PyQt5.QtGui import QIcon
import os

logging = True
validator_name = "UA Ortodoxy validator(Alpha)"
validator_icon = QIcon(os.path.join(os.path.dirname(__file__), 'resources', 'validated.png'))

def get_desktop_path():
    import platform , ctypes
    system = platform.system()
    
    if system == "Windows":
        # Для врахування OneDrive та локалізації
        try:
            # Використовуємо API Windows для отримання правильного шляху
            csidl_desktop = 0x0000  # CSIDL_DESKTOP
            path = ctypes.create_unicode_buffer(512)
            ctypes.windll.shell32.SHGetFolderPathW(None, csidl_desktop, None, 0, path)
            return path.value
        except Exception as e:
            log(f"Error retrieving desktop path on Windows: {e}")
            return os.path.join(os.environ['USERPROFILE'], 'Desktop')
    
    elif system == "Linux":
        return os.path.join(os.environ['HOME'], 'Desktop')
    
    else:
        raise NotImplementedError(f"Unsupported OS: {system}")

def log(text: str, level: int = Qgis.Info) -> None:
    if logging:
        QgsMessageLog.logMessage(
            message = text, 
            tag = validator_name, 
            level = level)

def save_dict_as_file(dictionary: dict, file_name: str, file_dir: str = None) -> None:
    """
    Зберегти словник у файл.
    
    :param dictionary: словник, який потрібно зберегти
    :param file_name: ім'я файлу, у який потрібно зберегти словник
    :param file_path: шлях до папки, у яку потрібно зберегти файл. Якщо не вказано, то буде використовуватися шлях до стільниці.
    """
    import json

    if file_dir is None:
        file_dir = os.path.join(get_desktop_path())
    else:
        if not os.path.exists(file_dir):  
            if os.path.exists(os.path.dirname(file_dir)):
                os.mkdir(file_dir)
            else:
                log(f"Помилка під час збереження файлу '{file_name}'. Папка '{file_dir}' не знайдена.", level=Qgis.Critical)
                iface.messageBar().pushWarning("Помилка", f"Папка '{file_dir}' не знайдена...")                
                return
        file_full_path = os.path.join(file_dir, f"{file_name}.json")
    
    with open(file_full_path, 'w') as file:
        json.dump(dictionary, file, indent=None, ensure_ascii=False)

    log(f"Словник збережено в '{file_full_path}'", level=Qgis.Success)

def save_validator_log():
    from qgis.PyQt.QtWidgets import (
    QDockWidget, QTabWidget, QPlainTextEdit,
    QApplication, QAction)
    from qgis.PyQt.QtCore import Qt

    def get_log_tab_content(tab_title=validator_name):
        dock = iface.mainWindow().findChild(QDockWidget, "MessageLog")
        if dock is None:
            iface.messageBar().pushWarning("Log helper", "Dock 'MessageLog' не знайдено.")
            return None

        # робимо панель видимою, якщо схована
        if not dock.isVisible():
            act = iface.mainWindow().findChild(QAction, "mActionShowLogMessagePanel")
            act.trigger() if act else dock.setVisible(True)
            QApplication.processEvents()

        tabs = dock.findChild(QTabWidget)
        if tabs is None:
            iface.messageBar().pushWarning("Log helper", "QTabWidget не знайдено.")
            return None

        # шукаємо вкладку: точний збіг або частковий (на випадок прихованих символів)
        for i in range(tabs.count()):
            title = tabs.tabText(i).strip()
            if (title == tab_title.strip()
                    or tab_title.strip() in title
                    or title in tab_title.strip()):
                page = tabs.widget(i)

                # 1⃣ якщо сторінка вже є редактором
                if isinstance(page, QPlainTextEdit):
                    return page.toPlainText()

                # 2⃣ пробуємо знайти редактор серед нащадків (глибокий пошук)
                editor = page.findChild(QPlainTextEdit, options=Qt.FindChildrenRecursively)
                if editor:
                    return editor.toPlainText()

                # 3⃣ якщо все ще нічого — перериваємо, щось пішло не так
                break
        
        log("При спробі збереження логу в файл не змогли отримати доступ до віджету редактора.", level=Qgis.Critical)
        iface.messageBar().pushWarning("Валідатор", "При спробі збереження логу в файл не змогли отримати доступ до віджету редактора.")
        return None
    
    content = get_log_tab_content()
    if not content:
        return
    file_dir = os.path.join(os.path.dirname(__file__), 'last_validation')
    
    if not os.path.exists(file_dir):  
        if os.path.exists(os.path.dirname(file_dir)):
            os.mkdir(file_dir)
        else:
            log(f"Помилка під час збереження файлу Логування. Папка '{file_dir}' не знайдена.", level=Qgis.Critical)
            iface.messageBar().pushWarning("Помилка", f"Папка '{file_dir}' не знайдена...")
            return
    
    file_path = os.path.join(file_dir, "log.txt")
    
    with open(file_path, 'w') as file:
        file.write(content)
    log(f"Логування збережено в файл: {file_path}", level=Qgis.Success)

def compress_last_validation_folder():
    save_validator_log()
    import shutil
    from qgis.PyQt.QtWidgets import QFileDialog
    source_folder = os.path.join(os.path.dirname(__file__), 'last_validation')
    target_folder, _ = QFileDialog.getSaveFileName(None, "Зберегти архів останньої перевірки", get_desktop_path(), "Zip files (*.zip)")
    if target_folder:
        if target_folder.endswith('.zip'):
            target_folder = target_folder[:-4]  # Remove the .zip extension if present
        shutil.make_archive(target_folder, 'zip', source_folder)
        log(f"Архів збережено: {target_folder}.zip", level=Qgis.Success)
        iface.messageBar().pushSuccess(validator_name, f"Архів збережено: {target_folder}.zip")
