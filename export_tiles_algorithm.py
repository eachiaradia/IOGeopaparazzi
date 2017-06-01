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
"""

__author__ = 'Enrico A. Chiaradia'
__date__ = '2017-02-27'
__copyright__ = '(C) 2017 by Enrico A. Chiaradia'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterFile,ParameterMultipleInput,ParameterExtent,ParameterNumber,ParameterCrs
from processing.core.outputs import OutputVector,OutputDirectory,OutputFile
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter

from processing.core.GeoAlgorithmExecutionException import GeoAlgorithmExecutionException
from processing.core.ProcessingLog import ProcessingLog
from processing.gui.AlgorithmDialog import AlgorithmDialog

import sqlite3 as sqlite
import os
import optparse
from osgeo import ogr

from tools.tilingthread import TilingThread

import os.path as osp
import sys
import platform

from pyspatialite import dbapi2 as db

from qgis.core import *
from qgis.gui import *

from qgis.utils import iface

from PyQt4.QtCore import QVariant  
from PyQt4.QtGui import *

import locale
import math
import operator

currentpath = osp.dirname(sys.modules[__name__].__file__)

class ExportTilesAlgorithmDialog(AlgorithmDialog):
  def __init__(self, alg):
    AlgorithmDialog.__init__(self, alg)
    
  def closeEvent(self, evnt):
    # necessary to close the thread before it is finished
    if self.alg.workThread is not None:
      self.alg.workThread.stop()
    else:
      pass
    
    # call original function
    # on QGIS 1.8.4 I received this error:
    # "C:/PROGRA~1/QGIS2~1.18/apps/qgis/./python/plugins\processing\gui\AlgorithmDialog.py", line 332, in closeEvent
    # QgsMapLayerRegistry.instance().layerWasAdded.disconnect(self.mainWidget.layerAdded)
    # TypeError: 'instancemethod' object is not connected
    # So I added a try
    try:
        super(ExportTilesAlgorithmDialog, self).closeEvent(evnt)
    except Exception as e:
        ProcessingLog.addToLog(ProcessingLog.LOG_INFO, 'closeEvent error')
        ProcessingLog.addToLog(ProcessingLog.LOG_INFO, str(e))
    

class ExportTilesAlgorithm(GeoAlgorithm):
    """This is an example algorithm that takes a vector layer and
    creates a new one just with just those features of the input
    layer that are selected.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the GeoAlgorithm class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.
    OUTFILE = 'OUTFILE'
    EXTENT = 'EXTENT'
    MINZOOM = 'MINZOOM'
    MAXZOOM = 'MAXZOOM'
    TILEWIDTH = 'TILEWIDTH'
    MAXNUMTILES = 'MAXNUMTILES'
    
    CURRENTPATH = osp.dirname(sys.modules[__name__].__file__)
    
    
    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """
        # The name that the user will see in the toolbox
        self.name = 'canvas layers to MBTiles'

        # The branch of the toolbox under which the algorithm will appear
        self.group = 'Export to Geopaparazzi'

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterExtent(self.EXTENT, self.tr('Set maximum extend')))
        self.addParameter(ParameterNumber(self.MINZOOM, self.tr('Set minimum scale'), default=16))
        self.addParameter(ParameterNumber(self.MAXZOOM, self.tr('Set maximum scale'),default=18))
        self.addParameter(ParameterNumber(self.TILEWIDTH, self.tr('Set tile dimension'),default=256))
        self.addParameter(ParameterNumber(self.MAXNUMTILES, self.tr('Max number of tiles to be generated'),default=10000))
        
        # We add a vector layer as output
        self.addOutput(OutputFile(self.OUTFILE,self.tr('Output file'),'mbtiles'))
        
        # the thread
        self.workThread = None
        
    def getIcon(self):
        """We return the default icon.
        """
        return QIcon(osp.join(self.CURRENTPATH,'icons','IOGeopaparazzi.png'))
        
    def getCustomParametersDialog(self):
      self.customDialog = ExportTilesAlgorithmDialog(self)
      return self.customDialog
        
    def processAlgorithm(self, progress):
      self.progress = progress
      extent = self.getParameterValue(self.EXTENT)
      minzoom = self.getParameterValue(self.MINZOOM)
      maxzoom = self.getParameterValue(self.MAXZOOM)
      tilewidth = self.getParameterValue(self.TILEWIDTH)
      crs = iface.mapCanvas().mapRenderer().destinationCrs().authid()
      maxnumtiles = self.getParameterValue(self.MAXNUMTILES)
      
      outFile = self.getOutputValue(self.OUTFILE)
      fileInfo = QFileInfo(outFile)
      outPath = os.path.dirname(outFile)
      
      # others
      tileheigh = tilewidth
      transparency = 255
      quality = 70
      fformat = 'PNG'
      antialiasing = False
      TMSConvention = False
      MBTilesCompression = False
      WriteJson = False
      WriteOverview = False
      RenderOutsideTiles = True
      writeMapurl = False
      writeViewer = False
      
      if minzoom > maxzoom:
          progress.setText(self.tr('Maximum zoom value is lower than minimum. Please correct this and try again.'))
          return
      
      toks = extent.split(',')
      extent = QgsRectangle(float(toks[0]),float(toks[2]),float(toks[1]),float(toks[3]))
      extent = QgsCoordinateTransform(QgsCoordinateReferenceSystem(crs), QgsCoordinateReferenceSystem('EPSG:4326')).transform(extent)
      arctanSinhPi = math.degrees(math.atan(math.sinh(math.pi)))
      extent = extent.intersect(QgsRectangle(-180, -arctanSinhPi, 180, arctanSinhPi))
      
      layermap = iface.legendInterface().layers()
      layers = []
      # add only visible layers
      for layer in layermap:
        if iface.legendInterface().isLayerVisible(layer):
          layers.append(layer)
      
      # reverse the list of layers
      layers = layers[::-1]
      
      self.workThread = TilingThread(
          layers,
          extent,
          minzoom,
          maxzoom,
          tilewidth,
          tileheigh,
          transparency,
          quality,
          fformat,
          fileInfo,
          fileInfo.fileName(),
          antialiasing,
          TMSConvention,
          MBTilesCompression,
          WriteJson,
          WriteOverview,
          RenderOutsideTiles,
          writeMapurl,
          writeViewer,
          maxnumtiles
      )
      self.workThread.updateProgress.connect(self.updateProgress)
      self.workThread.updateText.connect(self.updateText)
      #self.workThread.start()
      self.workThread.run()
  
    def updateProgress(self,val):
      self.progress.setPercentage(val)
      
    def updateText(self,txt):
      self.progress.setText(txt)
