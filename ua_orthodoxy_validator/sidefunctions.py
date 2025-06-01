from qgis.core import QgsMessageLog, Qgis

logging = True
validator_name = "👑Головний Валідатор👑"

def get_desktop_path():
    import os, platform , ctypes
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
            print(f"Error retrieving desktop path on Windows: {e}")
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

def save_dict_as_file(dictionary: dict, file_name: str, file_path: str = None) -> None:
    """
    Зберегти словник у файл.
    
    :param dictionary: словник, який потрібно зберегти
    :param file_name: ім'я файлу, у який потрібно зберегти словник
    :param file_path: шлях до папки, у яку потрібно зберегти файл.
                      Якщо не вказано, то буде використовуватися шлях до стільниці.
    """
    import json, os
    
    if file_path is None:
        file_path = os.path.join(get_desktop_path(), f"{file_name}.json")
    else:
        file_path = os.path.join(file_path, f"{file_name}.json")
    
    with open(file_path, 'w') as file:
        json.dump(dictionary, file, indent=4, ensure_ascii=False)