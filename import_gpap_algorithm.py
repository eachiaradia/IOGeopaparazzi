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
# TODO:
# https://anitagraser.com/2018/03/25/processing-script-template-for-qgis3/
__revision__ = '$Format:%H$'

from PyQt5.QtCore import QCoreApplication, QVariant
from PyQt5.QtGui import QIcon

from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterFeatureSink,
                       QgsProcessingParameterFile,
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
                       NULL)

import sqlite3 as sqlite
import os
import optparse
from osgeo import ogr

from .tools.Table import Table
from .tools.JSONparser import JSONparser
from .tools.image_post_processor import ImagePostProcessor

import os.path as osp
import sys
import platform

import re


class ImportGpapAlgorithm(QgsProcessingAlgorithm):
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

    OUTPUT = 'OUTPUT_FOLDER'
    IMAGESOUT = 'OUTPUT_IMAGES_FILE'
    BOOKMARKSOUT = 'OUTPUT_BOOKMARKS_FILE'
    NOTESOUT = 'OUTPUT_NOTES_FILE'
    GPSLOGSOUT = 'OUTPUT_GPSLOG_FILE'

    GPAP_FILE = 'GPAP_FILE'
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
            QgsProcessingParameterFile(
                self.GPAP_FILE,
                self.tr('Input gpap'),
                0,
                'gpap'
            )
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.IMAGESOUT,
                self.tr("Output image"),
                QgsProcessing.TypeVectorPoint)
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.BOOKMARKSOUT,
                self.tr("Output bookmarks"),
                QgsProcessing.TypeVectorPoint)
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.GPSLOGSOUT,
                self.tr("Output GPS logs"),
                QgsProcessing.TypeVectorLine)
        )

        self.addParameter(
            QgsProcessingParameterFeatureSink(
                self.NOTESOUT,
                self.tr("Output notes"),
                QgsProcessing.TypeVectorPoint)
        )

    # We add a path as output

    # QgsProcessingParameterTypeFolderDestination = QgsApplication.processingRegistry().parameterType('folderDestination')
    # outPar = QgsProcessingParameterTypeFolderDestination.create(self.OUTPUT)
    # outPar.name(self.tr('Output folder'))

    # self.addParameter(outPar)

    def name(self):
        """
		Returns the algorithm name, used for identifying the algorithm. This
		string should be fixed for the algorithm, and must not be localised.
		The name should be unique within each provider. Names should contain
		lowercase alphanumeric characters only and no spaces or other
		formatting characters.
		"""
        return 'gpap_to_vector_layers'

    def displayName(self):
        """
		Returns the translated algorithm name, which should be used for any
		user-visible display of the algorithm name.
		"""
        return self.tr('gpap to vector layers')

    def group(self):
        """
		Returns the name of the group this algorithm belongs to. This string
		should be localised.
		"""
        return self.tr('Import')

    def groupId(self):
        """
		Returns the unique ID of the group this algorithm belongs to. This
		string should be fixed for the algorithm, and must not be localised.
		The group id should be unique within each provider. Group id should
		contain lowercase alphanumeric characters only and no spaces or other
		formatting characters.
		"""
        return 'import_geopaparazzi'

    def tr(self, string):
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ImportGpapAlgorithm()

    def icon(self):
        """We return the default icon.
		"""
        return QIcon(osp.join(self.CURRENTPATH, 'icons', 'IOGeopaparazzi.png'))

    def resolveTemporaryOutputs(self):
        """Sets temporary outputs (output.value = None) with a
		empty string.
		"""
        for out in self.outputs:
            if not out.hidden and out.value is None:
                out.value = ''

    def processAlgorithm(self, parameters, context, feedback):
        """Here is where the processing itself takes place."""
        self.PARAM = parameters
        self.CONTEXT = context
        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        fullDBname = self.parameterAsFile(parameters, self.GPAP_FILE, context)
        if fullDBname == '':
            return

        par = parameters[self.IMAGESOUT]
        feedback.pushInfo(self.tr('par: %s') % par)

        outpath = self.parameterAsFileOutput(parameters, self.IMAGESOUT, context)
        feedback.pushInfo(self.tr('outpath is <%s> (type: %s)') % (outpath, type(outpath)))

        if outpath.startswith('memory:'):
            outpath = fullDBname
            feedback.pushInfo(self.tr('outpath is memory, images will be esported in %s') % outpath)

        if outpath.startswith('ogr:dbname='):
            # it is a geopackage
            outpath = re.search("ogr:dbname='(.*)' table=", outpath)
            outpath = outpath.group(1)
            feedback.pushInfo(self.tr('outpath is geopackage, images will be esported in %s') % outpath)

        outpath = osp.dirname(outpath)

        feedback.pushInfo(self.tr('export directory: %s') % outpath)

        # fullDBname = osp.join(pathToDB,DBname)
        feedback.pushInfo(self.tr('Connect to gpap file'))
        con = sqlite.connect(fullDBname)
        cur = con.cursor()
        feedback.setProgress(int(0))
        # export GPSlogs
        gpsVL = self.ExportGPSlogs(cur, feedback)
        feedback.pushInfo(self.tr('GPS log exported.'))
        feedback.setProgress(int(25))
        # export notes with form attributes
        formNotesVid = self.ExportFormNotes(cur)
        feedback.pushInfo(self.tr('Notes exported.'))
        feedback.setProgress(int(50))
        # export Images
        imagesVL = self.ExportImages(cur, outpath, feedback)
        feedback.pushInfo(self.tr('Images exported.'))
        feedback.setProgress(int(75))
        # export Bookmarks
        bookMarksVL = self.ExportBookmarks(cur)
        feedback.pushInfo(self.tr('Bookmarks exported.'))
        feedback.setProgress(int(100))
        # close connection
        cur.close()
        con.close()
        feedback.setProgress(int(0))

        return {self.IMAGESOUT: imagesVL, self.BOOKMARKSOUT: bookMarksVL, self.NOTESOUT: formNotesVid,
                self.GPSLOGSOUT: gpsVL}

    def exportPointToTempVector(self, pointTable, layName='pointlist', fields=None):
        # create layer
        fList = QgsFields()
        for f in fields:
            fList.append(f)

        (sink, dest_id) = self.parameterAsSink(self.PARAM, layName, self.CONTEXT, fList, QgsWkbTypes.Point25D, self.CRS)

        # add a features
        for r in range(0, pointTable.getNumOfRec()):
            lon = float(pointTable.getValue('lon', r))
            lat = float(pointTable.getValue('lat', r))
            alt = float(pointTable.getValue('altim', r))
            fet = QgsFeature()
            fet.setGeometry(QgsGeometry.fromWkt('POINTZ(%s %s %s)' % (lon, lat, alt)))
            fet.setAttributes(pointTable.getRecord(r))
            sink.addFeature(fet, QgsFeatureSink.FastInsert)

        return sink, dest_id

    # def convertToStringList(self, datalist, feedback=None):
    #     # TODO: no more required
    #     strList = []
    #     for e in datalist:
    #         if e == NULL: e = -1  # filter empty NULL values
    #         if isinstance(e, basestring):
    #             # strList.append(e.encode('utf8'))
    #             strList.append(str(e))
    #         else:
    #             strList.append(str(e))
	#
    #     return strList

    def ExportFormNotes(self, DBcursor):
        # select all record from notes table
        notes = DBcursor.execute("SELECT * FROM notes")
        notes = notes.fetchall()

        notesFieldNames = ["_id", "lon", "lat", "altim", "ts", "description", "text", "form", "style", "isdirty"]
        notesTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double),
                            QgsField("lat", QVariant.Double), QgsField("altim", QVariant.Double), \
                            QgsField("ts", QVariant.String), QgsField("description", QVariant.String), \
                            QgsField("text", QVariant.String), \
                            QgsField("form", QVariant.String), QgsField("style", QVariant.String), \
                            QgsField("isdirty", QVariant.Int)]
        notesTable = Table(notesFieldNames)
        for note in notes:
            # note = self.convertToStringList(note)
            notesTable.addRecordList(note)

        vl, vid = self.exportPointToTempVector(notesTable, self.NOTESOUT, notesTableFields)

        return vid

    def ExportFormNotes_OLD(self, DBcursor):
		# TODO: implement more form options
        # get the rough list of section names (rough means like: {"sectionname":"my name")
        sectionNames = DBcursor.execute("SELECT DISTINCT substr(form,0,instr(form,',')) AS formName FROM notes")
        sectionNames = sectionNames.fetchall()
        print('sectionNames', sectionNames)

        if len(sectionNames) == 0:
            sectionNames = [('', '')]

        # for each section name make a new vector file
        for sn in sectionNames:
            baseFieldNames = ["_id", "lon", "lat", "altim", "ts", "description", "text", "form", "style", "isdirty"]
            baseTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double),
                               QgsField("lat", QVariant.Double), QgsField("altim", QVariant.Double), \
                               QgsField("ts", QVariant.String), QgsField("description", QVariant.String), \
                               QgsField("text", QVariant.String), \
                               QgsField("form", QVariant.String), QgsField("style", QVariant.String), \
                               QgsField("isdirty", QVariant.Int)]
            baseTable = Table(baseFieldNames)

        if sn[0] == '':
            # select all record that are empty
            notes = DBcursor.execute("SELECT * FROM notes WHERE form LIKE ''")
            cleanName = 'notes'
            for note in notes:
                # note = self.convertToStringList(note)
                baseTable.addRecordList(note)
        else:
            # select all record that begins with sn[0]
            notes = DBcursor.execute("SELECT * FROM notes WHERE form LIKE '" + sn[0] + "%'")
            cleanName = sn[0].split(":")
            cleanName = cleanName[1].replace('"', '')
            i = 1
            for note in notes:
                # there are some more attributes to save ...
                parser = JSONparser(note[7])
                parser.parseKeyValue()
                if i == 1:
                    i += 1
                    # get section attribute key
                    key = parser.keys
                    baseFieldNames = baseFieldNames + key
                    baseTable = Table(baseFieldNames)
                    fields = parser.fields
                    baseTableFields = baseTableFields + fields

                vals = parser.values
                # note = self.convertToStringList(note)
                baseTable.addRecordList(note + vals)

        vl, vid = self.exportPointToTempVector(baseTable, self.NOTESOUT, baseTableFields)

        return vid

    def ExportImages(self, DBcursor, pathToDB, feedback):
        # create a table with image positions
        images = DBcursor.execute("SELECT * FROM images")
        imagesTable = Table(["_id", "lon", "lat", "altim", "azim", "imagedata_id", "ts", "text", "note_id", "isdirty"])
        imagesTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double),
                             QgsField("lat", QVariant.Double), QgsField("altim", QVariant.Double),
                             QgsField("azim", QVariant.Double), \
                             QgsField("imagedata_id", QVariant.Int), QgsField("ts", QVariant.String),
                             QgsField("text", QVariant.String), \
                             QgsField("note_id", QVariant.Int), QgsField("isdirty", QVariant.Int)]

        for img in images:
            # img = self.convertToStringList(img,feedback)
            imagesTable.addRecordList(img)

        vl, vid = self.exportPointToTempVector(imagesTable, self.IMAGESOUT, imagesTableFields)

        # create a new folder for images
        pathToImages = osp.join(pathToDB, 'images')
        if not osp.isdir(pathToImages):
            os.makedirs(pathToImages)

        # create a new folder for thunbnails
        pathToThunbnails = osp.join(pathToDB, 'thunbnails')
        if not osp.isdir(pathToThunbnails):
            os.makedirs(pathToThunbnails)

        # get the list of images
        imgIDs = imagesTable.getColumn("_id")
        imgNames = imagesTable.getColumn("text")

        # loop in the list and get BLOB
        i = 0
        for imgID in imgIDs:
            imgsData = DBcursor.execute("SELECT * FROM imagedata WHERE _id = " + str(imgID))
            imgName = str(imgNames[i])
            # print imgID, imgName

            for imgData in imgsData:
                with open(osp.join(pathToImages, imgName), "wb") as output_file:
                    output_file.write(imgData[1])

                with open(osp.join(pathToThunbnails, imgName), "wb") as output_file:
                    output_file.write(imgData[2])

                i += 1

        if self.CONTEXT.willLoadLayerOnCompletion(vid):
            pp = ImagePostProcessor.create()
            pp.setPaths(self.CURRENTPATH, pathToImages, pathToThunbnails)
            self.CONTEXT.layerToLoadOnCompletionDetails(vid).setPostProcessor(pp)

        return vid

    def ExportBookmarks(self, DBcursor):
        # create a table with bookmarks
        bookmarks = DBcursor.execute("SELECT * FROM bookmarks")
        bookmarksTable = Table(["_id", "lon", "lat", "zoom", "bnorth", "bsouth", "bwest", "beast", "text"])
        bookmarksTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double),
                                QgsField("lat", QVariant.Double), \
                                QgsField("zoom", QVariant.Double), QgsField("bnorth", QVariant.Double), \
                                QgsField("bsouth", QVariant.Double), QgsField("bwest", QVariant.Double), \
                                QgsField("beast", QVariant.Double), QgsField("text", QVariant.String)]

        for bkm in bookmarks:
            # bkm = self.convertToStringList(bkm)
            bookmarksTable.addRecordList(bkm)

        # create layer
        fList = QgsFields()
        for f in bookmarksTableFields:
            fList.append(f)

        (sink, dest_id) = self.parameterAsSink(self.PARAM, self.BOOKMARKSOUT, self.CONTEXT, fList, QgsWkbTypes.Polygon,
                                               self.CRS)

        # create a box for each logs
        for r in range(0, bookmarksTable.getNumOfRec()):
            n = float(bookmarksTable.getValue('bnorth', r))
            s = float(bookmarksTable.getValue('bsouth', r))
            w = float(bookmarksTable.getValue('bwest', r))
            e = float(bookmarksTable.getValue('beast', r))
            fet = QgsFeature()
            fet.setGeometry(
                QgsGeometry.fromWkt('POLYGON((%s %s, %s %s, %s %s, %s %s, %s %s))' % (w, n, e, n, e, s, w, s, w, n)))
            fet.setAttributes(bookmarksTable.getRecord(r))
            sink.addFeature(fet, QgsFeatureSink.FastInsert)

        # vl, vid = self.exportPointToTempVector(bookmarksTable, self.BOOKMARKSOUT, bookmarksTableFields)
        return dest_id

    def ExportGPSlogs(self, DBcursor, feedback=None):
        # create a table with logs
        gpslogs = DBcursor.execute("SELECT * FROM gpslogs")
        gpslogsTable = Table(["_id", "startts", "endts", "lengthm", "isdirty", "text"])
        gpslogsTableFields = [QgsField("_id", QVariant.Int), QgsField("startts", QVariant.Double),
                              QgsField("endts", QVariant.Double), \
                              QgsField("lengthm", QVariant.Double), QgsField("isdirty", QVariant.Int),
                              QgsField("text", QVariant.String)]
        # load the list of gpslogs
        for l in gpslogs:
            # l = self.convertToStringList(l)
            gpslogsTable.addRecordList(l)

        # create layer
        fList = QgsFields()
        for f in gpslogsTableFields:
            fList.append(f)

        (sink, dest_id) = self.parameterAsSink(self.PARAM, self.GPSLOGSOUT, self.CONTEXT, fList,
                                               QgsWkbTypes.LineStringZ, self.CRS)

        if feedback: feedback.pushInfo('GPSLOGSOUT: %s' % (self.GPSLOGSOUT))

        # create a line for each logs
        for r in range(0, gpslogsTable.getNumOfRec()):
            logID = str(gpslogsTable.getValue('_id', r))
            logname = str(gpslogsTable.getValue('text', r))
            # print logID, logname
            gpslogData = DBcursor.execute("SELECT * FROM gpslogsdata WHERE logid = " + logID + " ORDER BY _id")
            gpslogTable = Table(["_id", "lon", "lat", "altim", "ts", "logid"])

            for gpslogd in gpslogData:
                # gpslogd = self.convertToStringList(gpslogd)
                gpslogTable.addRecordList(gpslogd)

            # add a features
            pointList = []
            for g in range(0, gpslogTable.getNumOfRec()):
                # print pointTable.getValue('lon',r)
                lon = float(gpslogTable.getValue('lon', g))
                lat = float(gpslogTable.getValue('lat', g))
                alt = float(gpslogTable.getValue('altim', g))
                pointList.append('%s %s %s' % (lon, lat, alt))

            pointListStr = ', '.join(pointList)

            fet = QgsFeature()
            fet.setGeometry(QgsGeometry.fromWkt('LINESTRINGZ(%s)' % (pointListStr)))
            fet.setAttributes(gpslogsTable.getRecord(r))
            sink.addFeature(fet, QgsFeatureSink.FastInsert)

        return dest_id