from pathlib import Path
from typing import Optional, List

from qgis.PyQt import sip

from PyQt5.QtWidgets import QMenu, QToolBar, QAction
from PyQt5.QtGui import QIcon
from qgis.gui import QgisInterface


class uaSPT:
    """ 
    Збірка для уніфікування розміщення іконок плагінів від ініціативи
    "Відкриті інструменти просторового планування для України"

    Args:
        iface: QgsInterface
        toolbar_action: QAction
            іконка на панелі ініціативи(тут додаємо найголовнішу іконку,
            якщо нічого не прописано іконка не буде додана на панель)
        menu_actions: list[QAction]
            список QAction для меню ініціативи в меню плагінів
            (бажано додати всі QAction з плагіну, навіть якщо вони будуть ще і по інших менюхах)
            Якщо menu_actions = None - буде додано toolbar_action
        plugin_menu_name: str 
            Назва підменю в меню плагінів, прописуйте, якщо планується додавати більше 1 QAction
            Буде проігнорована, якщо menu_actions = None або містить тільки 1 елемент
        plugin_menu_icon: QIcon
            іконка підменю
    """
    # def tr(self, message):
    #     return self.iface.tr(message)

    def __init__(
        self,
        iface: QgisInterface,
        toolbar_action: Optional[QAction] = None,
        menu_actions: Optional[List[QAction]] = None,
        plugin_menu_name: Optional[str] = None,
        plugin_menu_icon: Optional[QIcon] = None,
    ):
        if menu_actions and len(menu_actions) > 1 and plugin_menu_name is None:
            raise ValueError('Помилка ініціалізації uaSPT.Ви пробуєте додати більше 1 QAction в меню, але не прописали назву підменю в меню ініціативи')
        if toolbar_action is None and not menu_actions:
            raise Exception('Помилка ініціалізації uaSPT. Ви не вказали дії які треба додати в меню та на панель ініціативи. Нема сенсу ініціювати клас')
        
        self.SPT_icon = self._loadInitiativeIcon()
        self.iface = iface
        self.TB_action = toolbar_action
        self.plugin_menu_name = plugin_menu_name
        if plugin_menu_icon is not None and not isinstance(plugin_menu_icon, QIcon):
            raise TypeError('Помилка ініціалізації uaSPT. Аргумент plugin_menu_icon має бути QIcon')
        self.menu_icon = plugin_menu_icon
        self.menu_actions = menu_actions
        
        self.SPT_toolbar = self._getToolbar()
        self.SPT_menu = self._getMenu()
        self.plugin_menu = self._createPluginMenu()

        if self.TB_action:
            self.SPT_toolbar.addAction(self.TB_action)


    def _loadInitiativeIcon(self, filename: str = "SPT_icon.png") -> Optional[QIcon]:
        # Іконка має лежати поруч із цим файлом
        p = Path(__file__).resolve().parent / filename
        if not p.exists():
            return None

        icon = QIcon(str(p))
        return None if icon.isNull() else icon

    def _createPluginMenu(self) -> Optional[QMenu]:
        if not self.menu_actions:
            if self.TB_action is not None:
                self.SPT_menu.addAction(self.TB_action)
            return None
        
        if self.menu_actions and len(self.menu_actions) == 1:
            self.SPT_menu.addAction(self.menu_actions[0])
            return None
        
        if self.menu_actions and self.plugin_menu_name:
            plugin_menu = QMenu(self.SPT_menu)
            if self.menu_icon:
                plugin_menu.setIcon(self.menu_icon)
            plugin_menu.setTitle(self.plugin_menu_name)
            for action in self.menu_actions:
                plugin_menu.addAction(action)
            self.SPT_menu.addMenu(plugin_menu)
            return plugin_menu
            
    
    def _getMenu(self) -> QMenu:
        plugin_menu:QMenu = self.iface.pluginMenu()

        # 1) Спроба знайти вже існуюче меню по objectName
        for act in plugin_menu.actions():
            m = act.menu()
            if m and m.objectName() == "ua_spt_menu":
                return m

        # Якщо не знайшли - то створюємо
        spt_menu = QMenu("Плагіни UA SPT", plugin_menu)
        if self.SPT_icon is not None:
            spt_menu.setIcon(self.SPT_icon)
        
        spt_menu.setObjectName("ua_spt_menu")
        #spt_menu.setToolTip('Меню ініціативи "Відкриті інструменти просторового планування для України"')

        seps = [a for a in plugin_menu.actions() if a.isSeparator()]
        sep = seps[1] if len(seps) >= 2 else (seps[0] if seps else None)
        
        if sep:
            actions = plugin_menu.actions()
            i = actions.index(sep)
            before = actions[i + 1] if i + 1 < len(actions) else None
            if before:
                plugin_menu.insertMenu(before, spt_menu)
            else:
                plugin_menu.addMenu(spt_menu)
        else:
            plugin_menu.addMenu(spt_menu)

        return spt_menu

    def _removeFromMenu(self) -> None:
        root: QMenu = self.iface.pluginMenu()

        # Не покладаємось на self.SPT_menu (може бути вже видалений/пересозданий)
        spt_menu = None
        for act in root.actions():
            m = act.menu()
            if m and m.objectName() == "ua_spt_menu":
                spt_menu = m
                break

        if spt_menu is None or sip.isdeleted(spt_menu):
            return

        # 1) Якщо було створене підменю плагіна — прибрати його
        if self.plugin_menu is not None and not sip.isdeleted(self.plugin_menu):
            try:
                spt_menu.removeAction(self.plugin_menu.menuAction())
            except RuntimeError:
                pass
            
            self.plugin_menu.deleteLater()

        # 2) Інакше — прибрати дії (або menu_actions, або TB_action як fallback)
        elif self.menu_actions:
            for action in self.menu_actions:
                try:
                    if action in spt_menu.actions():
                        spt_menu.removeAction(action)
                except RuntimeError:
                    pass

        elif self.TB_action is not None:
            try:
                if self.TB_action in spt_menu.actions():
                    spt_menu.removeAction(self.TB_action)
            except RuntimeError:
                pass

        # 3) Якщо меню порожнє (крім сепараторів) — прибрати з кореня і видалити
        try:
            if not [a for a in spt_menu.actions() if not a.isSeparator()]:
                root.removeAction(spt_menu.menuAction())
                spt_menu.setObjectName("ua_spt_menu__to_delete")
                spt_menu.deleteLater()
        except RuntimeError:
            pass
    
    def _removeFromToolbar(self) -> None:
        # Нема чого прибирати
        if self.TB_action is None:
            return

        # Не покладаємось на self.SPT_toolbar (він може вже бути видалений)
        toolbar = self.iface.mainWindow().findChild(QToolBar, "ua_spt_panel")
        if toolbar is None or sip.isdeleted(toolbar):
            return

        # Прибираємо action, якщо він там є
        if self.TB_action in toolbar.actions():
            toolbar.removeAction(self.TB_action)

        # Якщо тулбар порожній (крім сепараторів) — прибрати його з вікна і видалити
        if not [a for a in toolbar.actions() if not a.isSeparator()]:
            self.iface.mainWindow().removeToolBar(toolbar)
            toolbar.setObjectName("ua_spt_panel__to_delete")
            toolbar.deleteLater()

    def _getToolbar(self)->QToolBar:
        '''
        Повертає панель ініціативи "Відкриті інструменти просторового планування для України"
        args:
            iface: QgsInterface
        return:
            ua_spt_toolbar - об'єкт QToolBar з ідентифікатором "ua_spt_panel"
        '''
        toolbar:QToolBar = self.iface.mainWindow().findChild(QToolBar, 'ua_spt_panel')
        if not toolbar:
            toolbar:QToolBar = self.iface.addToolBar("🚀Панель UA SPT")
            toolbar.setObjectName('ua_spt_panel')
            toolbar.setToolTip('Панель ініціативи "Відкриті інструменти просторового планування для України"')
        
        return toolbar

    def unload(self):
        self._removeFromMenu()
        self._removeFromToolbar()