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

from PyQt4.QtCore import QSettings
from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterFile
from processing.core.outputs import OutputVector,OutputDirectory
from processing.tools import dataobjects, vector
from processing.tools.vector import VectorWriter

import sqlite3 as sqlite
import os
import optparse
from osgeo import ogr

from tools.Table import Table
from tools.JSONparser import JSONparser

import os.path as osp
import sys
import platform

from qgis.core import *
from qgis.gui import *

from PyQt4.QtCore import QVariant  

from PyQt4.QtGui import *


class ImportGpapAlgorithm(GeoAlgorithm):
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

    OUTPATH = ''
    GPAP_FILE = 'GPAP_FILE'
    CURRENTPATH = osp.dirname(sys.modules[__name__].__file__)
    CRS = QgsCoordinateReferenceSystem()
    CRS.createFromId(4326)
    
    
    def defineCharacteristics(self):
        """Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # The name that the user will see in the toolbox
        self.name = 'gpap to vector layers'

        # The branch of the toolbox under which the algorithm will appear
        self.group = 'Import from Geopaparazzi'

        # We add the input vector layer. It can have any kind of geometry
        # It is a mandatory (not optional) one, hence the False argument
        self.addParameter(ParameterFile(self.GPAP_FILE, self.tr('Input gpap'), False, False))
        
        # We add a vector layer as output
        self.addOutput(OutputDirectory(self.OUTPATH,self.tr('Output folder')))
        
    def getIcon(self):
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

    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place."""

        # The first thing to do is retrieve the values of the parameters
        # entered by the user
        fullDBname = self.getParameterValue(self.GPAP_FILE)
        if fullDBname == '':
            return
        
        pathToDB = osp.dirname(fullDBname)
        
        outpath = self.getOutputValue(self.OUTPATH)
        
        if outpath == '':
          outpath = pathToDB
        
        #fullDBname = os.path.join(pathToDB,DBname)
        progress.setText('Connect to gpap file')
        con = sqlite.connect(fullDBname)
        cur = con.cursor()
        progress.setPercentage(int(0))
        # export GPSlogs
        self.ExportGPSlogs(cur)
        progress.setText('GPS log exported ...')
        progress.setPercentage(int(25))
        #export notes with form attributes
        self.ExportFormNotes(cur)
        progress.setText('Notes exported ...')
        progress.setPercentage(int(50))
        # export Images
        self.ExportImages(cur,outpath)
        progress.setText('Images exported ...')
        progress.setPercentage(int(75))
        # export Bookmarks
        self.ExportBookmarks(cur)
        progress.setText('Bookmarks exported ...')
        progress.setPercentage(int(100))
        #close connection
        cur.close()
        con.close()
        progress.setPercentage(int(0))
        
    def exportPointToTempVector(self,pointTable,layName='pointlist', fields = None):
      # create layer
      vl = QgsVectorLayer("Point?crs=EPSG:4326", layName, "memory")
      pr = vl.dataProvider()

      # changes are only possible when editing the layer
      vl.startEditing()
      # add fields
      pr.addAttributes(fields)

      # add a features
      for r in range(0,pointTable.getNumOfRec()):
        lon = float(pointTable.getValue('lon',r))
        lat = float(pointTable.getValue('lat',r))
        fet = QgsFeature()
        fet.setGeometry(QgsGeometry.fromPoint(QgsPoint(lon,lat)))
        fet.setAttributes(pointTable.getRecord(r))
        pr.addFeatures([fet])

      # commit to stop editing the layer
      vl.commitChanges()

      # update layer's extent when new features have been added
      # because change of extent in provider is not propagated to the layer
      vl.updateExtents()
      
      return vl
      
    def exportLineToTempVector(self,pointTable,layName='line', fields = None):
      # create layer
      vl = QgsVectorLayer("LineString?crs=EPSG:4326", layName, "memory")
      pr = vl.dataProvider()

      # changes are only possible when editing the layer
      vl.startEditing()
      # add fields
      pr.addAttributes(fields)

      # add a features
      pointList = []
      for r in range(0,pointTable.getNumOfRec()):
        #print pointTable.getValue('lon',r)
        lon = float(pointTable.getValue('lon',r))
        lat = float(pointTable.getValue('lat',r))
        pointList.append(QgsPoint(lon,lat))
      
      fet = QgsFeature()
      fet.setGeometry(QgsGeometry.fromPolyline(pointList))
      #fet.setAttributes(pointTable.getRecord(r))
      pr.addFeatures([fet])

      # commit to stop editing the layer
      vl.commitChanges()

      # update layer's extent when new features have been added
      # because change of extent in provider is not propagated to the layer
      vl.updateExtents()
      
      return vl

      
    def convertToStringList(self,datalist):
      strList = []
      for e in datalist:
        if isinstance(e, basestring):
          strList.append(e.encode('utf8'))
        else:
          strList.append(str(e))
      
      return strList
      
    def ExportFormNotes(self,DBcursor):
      # get the rough list of section names (rough means like: {"sectionname":"my name")
      sectionNames = DBcursor.execute("SELECT DISTINCT substr(form,0,instr(form,',')) AS formName FROM notes")
      sectionNames = sectionNames.fetchall()
      
      if len(sectionNames)==0:
        sectionNames = [('','')]
        
      # for each section name make a new vector file
      for sn in sectionNames:
        baseFieldNames = ["_id","lon","lat","altim","ts","description","text","form","style","isdirty"]
        baseTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double), QgsField("lat", QVariant.Double),QgsField("altim", QVariant.Double), \
                                            QgsField("ts", QVariant.String),QgsField("description", QVariant.String), \
                                            QgsField("text", QVariant.String), \
                                            QgsField("form", QVariant.String),QgsField("style", QVariant.String), \
                                            QgsField("isdirty", QVariant.Int)]
        baseTable = Table(baseFieldNames)
                
        if sn[0] == '':
          # select all record that are empty
          notes = DBcursor.execute("SELECT * FROM notes WHERE form LIKE ''")
          cleanName = 'notes'
          for note in notes:
            note = self.convertToStringList(note)
            baseTable.addRecordList(note)
        else:
          # select all record that begins with sn[0]
          notes = DBcursor.execute("SELECT * FROM notes WHERE form LIKE '"+sn[0]+"%'")
          cleanName = sn[0].split(":")
          cleanName = cleanName[1].replace('"','')
          i = 1
          for note in notes:
            # there are some more attributes to save ...
            parser = JSONparser(note[7])
            parser.parseKeyValue()
            if i==1:
              i += 1
              # get section attribute key
              key = parser.keys
              baseFieldNames = baseFieldNames+key
              baseTable = Table(baseFieldNames)
              fields = parser.fields
              baseTableFields = baseTableFields+fields
              
            vals = parser.values
            note = self.convertToStringList(note)
            baseTable.addRecordList(note+vals)
            
        vl = self.exportPointToTempVector(baseTable, layName=cleanName, fields = baseTableFields)
        vl.setDisplayField('[% "text" %]')
        
        if cleanName == 'notes':
          vl.loadNamedStyle(os.path.join(self.CURRENTPATH,'styles','note_symb.qml'))
        # add to the TOC
        QgsMapLayerRegistry.instance().addMapLayer(vl)
        
      
    def ExportNotes(self,DBcursor):
      #create a table with notes
      # "_id","lon","lat","altim","ts","description","text","form","style","isdirty"
      notes = DBcursor.execute("SELECT * FROM notes")
      notesTable = Table(["_id","lon","lat","altim","ts","description","text","form","style","isdirty"])
      notesTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double), QgsField("lat", QVariant.Double),QgsField("altim", QVariant.Double), \
                                          QgsField("ts", QVariant.String),QgsField("description", QVariant.String), \
                                          QgsField("text", QVariant.String), \
                                          QgsField("form", QVariant.String),QgsField("style", QVariant.String), \
                                          QgsField("isdirty", QVariant.Int)]
                                          
      for note in notes:
        note = self.convertToStringList(note)
        notesTable.addRecordList(note)
        
      vl = self.exportPointToTempVector(notesTable, layName='notes', fields = notesTableFields)
      vl.setDisplayField('[% "text" %]')
      vl.loadNamedStyle(os.path.join(self.CURRENTPATH,'styles','note_symb.qml'))
      # add to the TOC
      QgsMapLayerRegistry.instance().addMapLayer(vl)

      
    def ExportImages(self,DBcursor,pathToDB):
      #create a table with image positions
      images = DBcursor.execute("SELECT * FROM images")
      imagesTable = Table(["_id","lon","lat","altim","azim","imagedata_id","ts","text","note_id","isdirty"])
      imagesTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double), QgsField("lat", QVariant.Double),QgsField("altim", QVariant.Double),QgsField("azim", QVariant.Double), \
                                          QgsField("imagedata_id", QVariant.Int),QgsField("ts", QVariant.String),QgsField("text", QVariant.String), \
                                          QgsField("note_id", QVariant.Int), QgsField("isdirty", QVariant.Int)]
     
      for img in images:
        img = self.convertToStringList(img)
        imagesTable.addRecordList(img)
        
      vl = self.exportPointToTempVector(imagesTable, layName='image positions', fields = imagesTableFields)
      vl.loadNamedStyle(os.path.join(self.CURRENTPATH,'styles','image_symb.qml'))
      
      #create a new folder for images
      pathToImages = os.path.join(pathToDB,'images')
      if not os.path.isdir(pathToImages):
        os.makedirs(pathToImages)
      
      #create a new folder for thunbnails
      pathToThunbnails = os.path.join(pathToDB,'thunbnails')
      if not os.path.isdir(pathToThunbnails):
        os.makedirs(pathToThunbnails)
      
      # get the list of images
      imgIDs = imagesTable.getColumn("_id")
      imgNames = imagesTable.getColumn("text")
      
      # loop in the list and get BLOB
      i = 0
      for imgID in imgIDs:
        imgsData = DBcursor.execute("SELECT * FROM imagedata WHERE _id = " + str(imgID))
        imgName = imgNames[i]
        #print imgID, imgName
        
        for imgData in imgsData:
          with open(os.path.join(pathToImages,imgName), "wb") as output_file:
            output_file.write(imgData[1])
          with open(os.path.join(pathToThunbnails,imgName), "wb") as output_file:
            output_file.write(imgData[2])
        i +=1

      
      # add Show Image Action
      #SIact = 'from PyQt4.QtCore import QUrl; from PyQt4.QtWebKit import QWebView;  myWV = QWebView(None); '
      modPath = os.path.join(self.CURRENTPATH,'imageviewer','imageviewer.py')
      if platform.system() == 'Windows':
        modPath = modPath.replace("\\","/")
      
      SIact = 'import imp; foo = imp.load_source("ImageViewer", "'
      SIact += modPath
      SIact += '");'
      SIact += 'imv = foo.ImageViewer();'
      SIact += "fn = r'"+os.path.join(pathToImages,'[% "text" %]')+"'"+";"
      SIact += 'imv.openImage(fn);'
      SIact += 'imv.show();'
      #SIact += 'myWV.setWindowTitle('+'"'+'[% "text" %]'+'"'+'); '
      #SIact += 'myWV.load(QUrl('
      #SIact += "'"+os.path.join(pathToImages,'[% "text" %]')+"'"+")); myWV.show()"
      actions = vl.actions()
      actions.addAction(QgsAction.GenericPython, "Show Image",SIact)
      
      # add tip image
      tipImg = '[% "text" %]'
      tipImg += '<br><img src="'+os.path.join(pathToThunbnails,'[% "text" %]')+'" />'
      vl.setDisplayField(tipImg)
      
      # add to the TOC
      QgsMapLayerRegistry.instance().addMapLayer(vl)
      
    def ExportBookmarks(self,DBcursor):
      #create a table with bookmarks
      bookmarks = DBcursor.execute("SELECT * FROM bookmarks")
      bookmarksTable = Table(["_id","lon","lat","zoom","bnorth","bsouth","bwest","beast","text"])
      bookmarksTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double), QgsField("lat", QVariant.Double), \
                                          QgsField("zoom", QVariant.Double),QgsField("bnorth", QVariant.Double), \
                                          QgsField("bsouth", QVariant.Double),QgsField("bwest", QVariant.Double), \
                                          QgsField("beast", QVariant.Double),QgsField("text", QVariant.String)]
     
      for bkm in bookmarks:
        bkm = self.convertToStringList(bkm)
        bookmarksTable.addRecordList(bkm)
        
      vl = self.exportPointToTempVector(bookmarksTable, layName='bookmarks', fields = bookmarksTableFields)
      vl.setDisplayField('[% "text" %]')
      vl.loadNamedStyle(os.path.join(self.CURRENTPATH,'styles','bookmark_symb.qml'))
      # add to the TOC
      QgsMapLayerRegistry.instance().addMapLayer(vl)

      
    def ExportGPSlogs(self,DBcursor):
      #create a table with logs
      gpslogs = DBcursor.execute("SELECT * FROM gpslogs") 
      gpslogsTable = Table(["_id","startts","endts","lengthm","isdirty","text"])
      gpslogsTableFields = [QgsField("_id", QVariant.Int), QgsField("startts", QVariant.Double), QgsField("endts", QVariant.Double), \
                                          QgsField("lengthm", QVariant.Double),QgsField("isdirty", QVariant.Int),QgsField("text", QVariant.String)]
      # load the list of gpslogs
      for l in gpslogs:
        l = self.convertToStringList(l)
        gpslogsTable.addRecordList(l)
      
      # create layer
      vl = QgsVectorLayer("LineString?crs=EPSG:4326", 'tracklogs', "memory")
      pr = vl.dataProvider()

      # changes are only possible when editing the layer
      vl.startEditing()
      # add fields
      pr.addAttributes(gpslogsTableFields)
      
      #create a line for each logs
      for r in range(0,gpslogsTable.getNumOfRec()):
        logID = str(gpslogsTable.getValue('_id',r))
        logname = str(gpslogsTable.getValue('text',r))
        #print logID, logname
        gpslogData  = DBcursor.execute("SELECT * FROM gpslogsdata WHERE logid = " + logID + " ORDER BY _id")
        gpslogTable = Table(["_id","lon","lat","altim","ts","logid"])
        
        for gpslogd in gpslogData:
          gpslogd = self.convertToStringList(gpslogd)
          gpslogTable.addRecordList(gpslogd)
        
        # add a features
        pointList = []
        for g in range(0,gpslogTable.getNumOfRec()):
          #print pointTable.getValue('lon',r)
          lon = float(gpslogTable.getValue('lon',g))
          lat = float(gpslogTable.getValue('lat',g))
          pointList.append(QgsPoint(lon,lat))
        
        fet = QgsFeature()
        fet.setGeometry(QgsGeometry.fromPolyline(pointList))
        fet.setAttributes(gpslogsTable.getRecord(r))
        pr.addFeatures([fet])

        # commit to stop editing the layer
        vl.commitChanges()

        # update layer's extent when new features have been added
        # because change of extent in provider is not propagated to the layer
        vl.updateExtents()
        vl.loadNamedStyle(os.path.join(self.CURRENTPATH,'styles','tracklog_symb.qml'))
        # add to the TOC
        QgsMapLayerRegistry.instance().addMapLayer(vl)
