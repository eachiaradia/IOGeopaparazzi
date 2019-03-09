# -*- coding: utf-8 -*-

"""
/***************************************************************************
 IOGeopaparazzi
								 A QGIS plugin
 A plugin to import/export geodata from/to geopaparazzi
								-------------------
		begin				: 2017-02-27
		copyright			: (C) 2017 by Enrico A. Chiaradia
		email				: enrico.chiaradia@yahoo.it
 ***************************************************************************/

/***************************************************************************
 *																		 *
 *	 This program is free software; you can redistribute it and/or modify	*
 *	 it under the terms of the GNU General Public License as published by	*
 *	 the Free Software Foundation; either version 2 of the License, or	 *
 *	 (at your option) any later version.									 *
 *																		 *
 ***************************************************************************/
"""

__author__ = 'Enrico A. Chiaradia'
__date__ = '2017-02-27'
__copyright__ = '(C) 2017 by Enrico A. Chiaradia'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'


from PyQt5.QtCore import QCoreApplication,QVariant,QFileInfo
from PyQt5.QtGui import QIcon

from qgis.core import (QgsProcessing,
									QgsFeatureSink,
									QgsProcessingAlgorithm,
									QgsProcessingParameterFeatureSource,
									QgsProcessingParameterFeatureSink,
									QgsProcessingParameterFileDestination,
									QgsProcessingParameterFile,
									QgsProcessingParameterExtent,
									QgsProcessingParameterNumber,
									QgsVectorLayer,
									QgsCoordinateReferenceSystem,
									QgsApplication,
									QgsField,
									QgsFields,
									QgsPointXY,
									QgsFeature,
									QgsGeometry,
									QgsProject,
									QgsAction,
									QgsWkbTypes,
									QgsCoordinateTransform,
									QgsRectangle)
									

import sqlite3 as sqlite
import os
import optparse
from osgeo import ogr

import os.path as osp
import sys
import platform

import locale
import math
import operator

from .tools.tilingthread import TilingThread

from qgis.utils import iface


class ExportTilesAlgorithm(QgsProcessingAlgorithm):
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
	
	FEEDBACK = None
	
		
	def initAlgorithm(self, config):
		"""Here we define the inputs and output of the algorithm, along
		with some other properties.
		"""
		# We add the input vector layer. It can have any kind of geometry
		# It is a mandatory (not optional) one, hence the False argument
		
		self.addParameter(
			QgsProcessingParameterExtent(
				self.EXTENT,
				self.tr('Set maximum extend')
			)
		)
		
		self.addParameter(
			QgsProcessingParameterNumber (
				self.MINZOOM,
				self.tr("Set minimum scale"),
				defaultValue=16)
		)
		
		self.addParameter(
			QgsProcessingParameterNumber (
				self.MAXZOOM,
				self.tr("Set minimum scale"),
				defaultValue=18)
		)
		
		self.addParameter(
			QgsProcessingParameterNumber (
				self.TILEWIDTH,
				self.tr("Set tile dimension"),
				defaultValue=256)
		)
		
		self.addParameter(
			QgsProcessingParameterNumber (
				self.MAXNUMTILES,
				self.tr("Max number of tiles to be generated"),
				defaultValue=10000)
		)
		
		self.addParameter(
			QgsProcessingParameterFileDestination(
				self.OUTFILE,
				self.tr("Output file"),
				self.tr('MBTiles files (*.mbtiles)') )
		)
		
		# the thread
		self.workThread = None
		
		
	def name(self):
		"""
		Returns the algorithm name, used for identifying the algorithm. This
		string should be fixed for the algorithm, and must not be localised.
		The name should be unique within each provider. Names should contain
		lowercase alphanumeric characters only and no spaces or other
		formatting characters.
		"""
		return 'canvas_layers_to_mbtiles'

	def displayName(self):
		"""
		Returns the translated algorithm name, which should be used for any
		user-visible display of the algorithm name.
		"""
		return self.tr('canvas layers to MBTiles')

	def group(self):
		"""
		Returns the name of the group this algorithm belongs to. This string
		should be localised.
		"""
		return self.tr('Export')

	def groupId(self):
		"""
		Returns the unique ID of the group this algorithm belongs to. This
		string should be fixed for the algorithm, and must not be localised.
		The group id should be unique within each provider. Group id should
		contain lowercase alphanumeric characters only and no spaces or other
		formatting characters.
		"""
		return 'export_geopaparazzi'

	def tr(self, string):
		return QCoreApplication.translate('Processing', string)

	def createInstance(self):
		return ExportTilesAlgorithm()

		
	def icon(self):
		"""We return the default icon.
		"""
		return QIcon(osp.join(self.CURRENTPATH,'icons','IOGeopaparazzi.png'))


	def resolveTemporaryOutputs(self):
		"""Sets temporary outputs (output.value = None) with a
		empty string.
		"""
		for out in self.outputs:
			if not out.hidden and out.value is None:
				out.value = ''
	
	def updateProgress(self,perc):
		self.FEEDBACK.setProgress(int(perc))
		
	def updateText(self,text):
		self.FEEDBACK.pushInfo(text)

	def processAlgorithm(self, parameters, context, feedback):
		self.FEEDBACK = feedback
		
		"""Here is where the processing itself takes place."""
		extent = self.parameterAsExtent(parameters, self.EXTENT, context)
		minzoom = self.parameterAsInt(parameters, self.MINZOOM, context)
		maxzoom = self.parameterAsInt(parameters, self.MAXZOOM, context)
		tilewidth = self.parameterAsInt(parameters, self.TILEWIDTH, context)
		maxnumtiles = self.parameterAsInt(parameters, self.MAXNUMTILES, context)
		#crs = iface.mapCanvas().mapRenderer().destinationCrs().authid()
				
		outFile = self.parameterAsFileOutput(parameters, self.OUTFILE, context)
		fileInfo = QFileInfo(outFile)
		# outPath = os.path.dirname(outFile)
		
		feedback.pushInfo(self.tr('extent is <%s>')%(extent)) 
		feedback.pushInfo(self.tr('minzoom is <%s>')%(minzoom))
		feedback.pushInfo(self.tr('maxzoom is <%s>')%(maxzoom))
		feedback.pushInfo(self.tr('tilewidth is <%s>')%(tilewidth))
		feedback.pushInfo(self.tr('maxnumtiles is <%s>')%(maxnumtiles))
		
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
		
		feedback.pushInfo(self.tr('---------------'))
		feedback.pushInfo(self.tr('Other settings:')) 
		feedback.pushInfo(self.tr('tileheigh is <%s>')%(tileheigh))
		feedback.pushInfo(self.tr('tilewidth is <%s>')%(tilewidth))
		feedback.pushInfo(self.tr('transparency is <%s>')%(transparency)) 
		feedback.pushInfo(self.tr('quality is <%s>')%(quality))
		feedback.pushInfo(self.tr('fformat is <%s>')%(fformat))
		feedback.pushInfo(self.tr('antialiasing is <%s>')%(antialiasing)) 
		feedback.pushInfo(self.tr('TMSConvention is <%s>')%(TMSConvention)) 
		feedback.pushInfo(self.tr('MBTilesCompression is <%s>')%(MBTilesCompression)) 
		feedback.pushInfo(self.tr('WriteJson is <%s>')%(WriteJson)) 
		feedback.pushInfo(self.tr('WriteOverview is <%s>')%(WriteOverview)) 
		feedback.pushInfo(self.tr('RenderOutsideTiles is <%s>')%(RenderOutsideTiles)) 
		feedback.pushInfo(self.tr('writeMapurl is <%s>')%(writeMapurl)) 
		feedback.pushInfo(self.tr('writeViewer is <%s>')%(writeViewer))
		feedback.pushInfo(self.tr('---------------'))
				
		if minzoom > maxzoom:
			feedback.pushInfo(self.tr('Maximum zoom value is lower than minimum. Please correct this and try again.'))
			return {}
		
		#~ toks = extent.split(',')
		#~ extent = QgsRectangle(float(toks[0]),float(toks[2]),float(toks[1]),float(toks[3]))
		extent = QgsCoordinateTransform(QgsProject.instance().crs(), QgsCoordinateReferenceSystem('EPSG:4326'),QgsProject.instance()).transform(extent)
		arctanSinhPi = math.degrees(math.atan(math.sinh(math.pi)))
		extent = extent.intersect(QgsRectangle(-180, -arctanSinhPi, 180, arctanSinhPi))
		
		layermap = iface.mapCanvas().layers()
		layers = []
		# add only visible layers
		layTreeRoot = QgsProject.instance().layerTreeRoot()
		for layer in layermap:
			if layTreeRoot.findLayer(layer.id()).isVisible():
				feedback.pushInfo(self.tr('Exporting layer %s.')%layer.name())
				layers.append(layer)
		
		
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
		#~ #self.workThread.start()
		self.workThread.run()
		
		return {}
	