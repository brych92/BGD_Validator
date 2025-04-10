from qgis.core import QgsMessageLog, Qgis

logging = True
validator_name = "👑Головний Валідатор👑"

def log(text: str, level: int = Qgis.Info) -> None:
    if logging:
        QgsMessageLog.logMessage(
            message = text, 
            tag = validator_name, 
            level = level)

