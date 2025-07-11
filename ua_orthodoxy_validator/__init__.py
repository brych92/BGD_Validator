# -*- coding: utf-8 -*-
"""
/***************************************************************************
 UA_orthodoxy_validator
                                 A QGIS plugin
 Перший український православний валідатор
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2024-09-15
        copyright            : (C) 2024 by Bohdan2505, brych92
        email                :  
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load UA_orthodoxy_validator class from file UA_orthodoxy_validator.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .ua_orthodoxy_validator import UA_orthodoxy_validator
    return UA_orthodoxy_validator(iface)
