# -*- coding: utf-8 -*-
"""
/***************************************************************************
 IOGeopaparazzi
                                 A QGIS plugin
 A plugin to import/export geodata from/to geopaparazzi
                              -------------------
        begin                : 2017-02-27
        copyright            : (C) 2017 by Enrico A. Chiaradia
        email                : enrico.chiaradia@yahoo.it
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

__author__ = 'Enrico A. Chiaradia'
__date__ = '2017-02-27'
__copyright__ = '(C) 2017 by Enrico A. Chiaradia'


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load IOGeopaparazzi class from file IOGeopaparazzi.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .io_geopaparazzi import IOGeopaparazziPlugin
    return IOGeopaparazziPlugin()
