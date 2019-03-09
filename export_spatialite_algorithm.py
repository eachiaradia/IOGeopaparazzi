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

from PyQt5.QtCore import QCoreApplication,QVariant
from PyQt5.QtGui import QIcon

from qgis.core import (QgsProcessing,
									QgsFeatureSink,
									QgsProcessingAlgorithm,
									QgsProcessingParameterFeatureSource,
									QgsProcessingParameterFeatureSink,
									QgsProcessingParameterFileDestination,
									QgsProcessingParameterMultipleLayers,
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
									QgsWkbTypes)
									
from qgis.gui import *
from qgis.core import *

import sqlite3 as sqlite
import os
import optparse
from osgeo import ogr

from .tools.Table import Table
from .tools.JSONparser import JSONparser

import os.path as osp
import sys
import platform

##from pyspatialite import dbapi2 as db
from qgis.utils import spatialite_connect


class ExportSpatialiteAlgorithm(QgsProcessingAlgorithm):
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

	LAYERS = 'LAYERS'
	OUTFILE = 'OUTFILE'

	CURRENTPATH = osp.dirname(sys.modules[__name__].__file__)
	CRS = QgsCoordinateReferenceSystem()
	CRS.createFromId(4326)
	
	
	def initAlgorithm(self, config):
		"""Here we define the inputs and output of the algorithm, along
		with some other properties.
		"""

		# We add the input vector layer. It can have any kind of geometry
		# It is a mandatory (not optional) one, hence the False argument
		
		self.addParameter(
			QgsProcessingParameterMultipleLayers(
				self.LAYERS,
				self.tr('Layers to export'))
		)
		
		self.addParameter(
			QgsProcessingParameterFileDestination(
				self.OUTFILE,
				self.tr("Output file"),
				self.tr('SQLite files (*.sqlite)') )
		)
		
		
	def name(self):
		"""
		Returns the algorithm name, used for identifying the algorithm. This
		string should be fixed for the algorithm, and must not be localised.
		The name should be unique within each provider. Names should contain
		lowercase alphanumeric characters only and no spaces or other
		formatting characters.
		"""
		return 'vector_layers_to_sqlite'

	def displayName(self):
		"""
		Returns the translated algorithm name, which should be used for any
		user-visible display of the algorithm name.
		"""
		return self.tr('vector layers to sqlite')

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
		return ExportSpatialiteAlgorithm()

		
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
				

	def processAlgorithm(self, parameters, context, feedback):
		"""Here is where the processing itself takes place."""
		## MULTIPOINT is a collection of two or more POINTs belonging to the same entity.
		## MULTILINESTRING is a collection of two or more LINESTRINGs.
		## MULTIPOLYGON is a collection of two or more POLYGONs.
		## GEOMETRYCOLLECTION is an arbitrary collection containing any other kind of geometries.
		# to manage multi type shapefile
		dict = {'POINT': 'MULTIPOINT','LINESTRING': 'MULTILINESTRING', 'POLYGON': 'MULTIPOLYGON',\
		'MULTIPOINT': 'MULTIPOINT','MULTILINESTRING': 'MULTILINESTRING', 'MULTIPOLYGON': 'MULTIPOLYGON',\
		'GEOMETRYCOLLECTION': 'GEOMETRYCOLLECTION'}
		
		# use CastToMulti in the next release ...

		# The first thing to do is retrieve the values of the parameters
		# entered by the user
		
		inLayers = self.parameterAsLayerList(parameters, self.LAYERS, context)
		
		outFile = self.parameterAsFileOutput(parameters, self.OUTFILE, context)
		
		# delete file if it exists
		if os.path.exists(outFile):
			os.remove(outFile)
		
		# create new sqlite file
		feedback.pushInfo(self.tr('Create sqlite'))
		feedback.setProgress(int(0))

		##conn = db.connect(outFile)
		#conn = qgis.utils.spatialite_connect(outFile)
		conn = spatialite_connect(outFile)

		# creating a Cursor
		cur = conn.cursor()
		
		# initializing Spatial MetaData
		# using v.2.4.0 this will automatically create
		# GEOMETRY_COLUMNS and SPATIAL_REF_SYS
		sql = 'SELECT InitSpatialMetadata(1)'
		cur.execute(sql)
		
		nlay = len(inLayers)
		i = -1.0
		for layer in inLayers:
			name = layer.name()
			source = layer.dataProvider().dataSourceUri()
			# open vector layer
			feedback.pushInfo(self.tr('Exporting layer %s') %(name))
			
			try:
				cod = layer.dataProvider().encoding()
			except:
				cod = 'System'

			if cod == 'System':
				cod = sys.getdefaultencoding()
				
			feedback.pushInfo(self.tr('layer %s is coded as %s')%(name,cod))
				
			i +=1.0
			feedback.pushInfo(self.tr('processing %s layer') %(name))
			feedback.setProgress(int(100*i/nlay))
			# move to db
			# get layer type (point, line, polygon)
			vtype = self.getGeomType(layer).upper()
			forcedVtype = dict[vtype]
			# get name and type of fields
			vfields = self.getFieldList(layer)
			# get crs code
			vcrs = layer.crs().postgisSrid()
			# something like: "crs":{"type":"name","properties":{"name":"EPSG:4326"}}
			vcrsAuthid = '"crs":{"type":"name","properties":{"name":"%s"}}' %(layer.crs().authid())
			# create a new table
			sql = 'CREATE TABLE "'+name+'" (' + vfields + ')'
			cur.execute(sql)
			# creating a Geometry column
			sql = 'SELECT AddGeometryColumn("'+name+'",'
			sql += '"geom", '+str(vcrs)+', "'+forcedVtype+'", "XY")'
			try:
				cur.execute(sql)
			except:
				feedback.pushInfo(self.tr('SQL error at %s, sql: %s') %(str(f),sql))
			# populate with geometry and attributes
			# to be improved with selection/ROI
			
			# get field names list
			vfields = self.getFieldNameList(layer)
			iter = layer.getFeatures()
			
			f = -1.0
			nfeat = layer.featureCount() 
			for feature in iter:
				f+=1.0
				feedback.setProgress(int(100*f/nfeat))
				# retrieve every feature with its geometry and attributes
				# fetch geometry
				geom = feature.geometry().asJson()
				# split and add crs infos
				toks = geom.split(',')
				geom = ",".join([toks[0],vcrsAuthid,",".join(toks[1:])])
				# fetch attributes and geometry
				attrs = self.get_feature_attr(feature,cod)
				geom = "CastToMulti(GeomFromGeoJSON('"+geom+"'))"
				try:
					sql = 'INSERT INTO "'+name+'" ('+vfields+', geom) '
					sql += 'VALUES ('+attrs+', '+geom+')'
				except:
					feedback.pushInfo(self.tr('Attribute error at %s, attributes: %s') %(str(f),attrs))
				
				try:
					cur.execute(sql)
				except:
					feedback.pushInfo(self.tr('SQL error at %s, sql: %s') %(str(f),sql))
			
		conn.commit()
		# force spatial index
		cur.execute('SELECT CreateSpatialIndex("'+name+'", "geom")')
		# Update statistics
		cur.execute('SELECT UpdateLayerStatistics()')
		
		# run VACUUM to reduce the size
		##cur.execute('VACUUM')
		# close connection
		conn.close()
		
		return {self.OUTFILE: outFile}
	
	def getFieldList(self, layer):
		## modified from https://github.com/romain974/qspatialite/blob/master/qspatialite.py
		fields=[]
		# get layer field
		# transform field type name to string
		id = 0
		for fld in layer.fields():
			id +=1
			
			#fldName=unicode(fld.name()).encode('utf-8').replace("'"," ").replace('"'," ")
			fldName=fld.name().replace("'"," ").replace('"'," ")
			fldType=fld.type()
			#fldTypeName=unicode(fld.typeName()).encode('utf-8').upper()
			fldTypeName=fld.typeName().upper()
			if fldTypeName=='DATE':
				fldType='TEXT' 
			elif fldType in (QVariant.Char,QVariant.String): # field type is TEXT
				fldLength=len(fldName)
				fldType='TEXT(%s)'%fldLength	#Add field Length Information
			elif fldType in (QVariant.Bool,QVariant.Int,QVariant.LongLong,QVariant.UInt,QVariant.ULongLong): # field type is INTEGER
				fldType='INTEGER'
			elif fldType==QVariant.Double: # field type is DOUBLE
				fldType='REAL'
			else: # field type is not recognized by SQLITE
				fldType=fldTypeName
				
			fields.append("%s %s" %(fldName,fldType))
		
		fields = ", ".join(fields)
		return fields
		
	def getFieldNameList(self, layer):
		## modified from https://github.com/romain974/qspatialite/blob/master/qspatialite.py
		fields=[]
		# get layer field
		# transform field type name to string
		id = 0
		for fld in layer.fields():
			id +=1
			#fldName=unicode(fld.name()).encode('utf-8').replace("'"," ").replace('"'," ")
			fldName=fld.name().replace("'"," ").replace('"'," ")
			fields.append("%s" %(fldName))
	
		fields = ", ".join(fields)
		return fields
		
	def getGeomType(self, layer):
		iter = layer.getFeatures()
		feature = next(iter)
		geom = feature.geometry().asJson()
		# it's like: '{"type": "LineString","crs":{"type":'
		geomType = self.find_between(geom, '{"type": "', '", "' )
		return geomType
		
	def find_between(self, s, first, last ):
		## from http://stackoverflow.com/questions/3368969/find-string-between-two-substrings
		try:
			start = s.index( first ) + len( first )
			end = s.index( last, start )
			return s[start:end]
		except ValueError:
			return ""

	def get_feature_attr(self, feature,coding = 'utf-8'):
		# coding is not actually used but at the moment I leave it
		# for future improvements
		attrs = feature.attributes()
		attrsStr = ''
		for a in attrs:
			if type(a) =='unicode':
				a = a.encode('utf-8')
				
			a = '%s'%a
			a = a.replace("'","''")
			attrsStr+=a+"', '"
	
		# remove last sequence
		attrsStr = attrsStr[:-4]
		# add first and last single quotes
		attrsStr = "'"+attrsStr+"'"
		return attrsStr
		
