#!/usr/bin/python
"""
/***************************************************************************
Name			 	 : ExportDataset.py
Description : Just another Geopaparazzi database exporter
Date          : 12/Oct/15 
copyright   : (C) 2015 by Enrico A. Chiaradia
email         : enrico.chiaradia@yahoo.it 
credits       :
http://geospatialpython.com/2015/05/geolocating-photos-in-qgis.html
http://linfiniti.com/2012/03/a-python-layer-action-to-open-a-wikipedia-page-in-qgis/
http://gis.stackexchange.com/questions/60473/how-can-i-programatically-create-and-add-features-to-a-memory-layer-in-qgis-1-9


 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General self.License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import sqlite3 as sqlite
import os
import optparse
from osgeo import ogr
from Table import Table
from JSONparser import JSONparser

import os.path as osp
import sys
import platform

from qgis.core import *
from qgis.gui import *

from PyQt4.QtCore import QVariant  

currentpath = osp.dirname(sys.modules[__name__].__file__)

def exportPointToTempVector(pointTable,layName='pointlist', fields = None):
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
  
def exportLineToTempVector(pointTable,layName='line', fields = None):
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

  
def convertToStringList(datalist):
  strList = []
  for e in datalist:
    if isinstance(e, basestring):
      strList.append(e.encode('utf8'))
    else:
      strList.append(str(e))
  
  return strList
  
def ExportFormNotes(DBcursor,currentPath):
  # get the rough list of section names (rough means like: {"sectionname":"my name")
  sectionNames = DBcursor.execute("SELECT DISTINCT substr(form,0,instr(form,',')) AS formName FROM notes")
  sectionNames = sectionNames.fetchall()
  print sectionNames
  # for each section name make a new vector file
  for sn in sectionNames:
    print sn
    baseFieldNames = ["_id","lon","lat","altim","ts","description","text","form","style","isdirty"]
    baseTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double), QgsField("lat", QVariant.Double),QgsField("altim", QVariant.Double), \
                                        QgsField("ts", QVariant.String),QgsField("description", QVariant.String), \
                                        QgsField("text", QVariant.String), \
                                        QgsField("form", QVariant.String),QgsField("style", QVariant.String), \
                                        QgsField("isdirty", QVariant.Int)]
                                          
    notes = DBcursor.execute("SELECT * FROM notes WHERE form LIKE '"+sn[0]+"%'")
    i = 1
    for note in notes:
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
      note = convertToStringList(note)
      baseTable.addRecordList(note+vals)
      
    cleanName = sn[0].split(":")
    cleanName = cleanName[1].replace('"','')
    if cleanName == '':
      cleanName = 'notes'
    
    vl = exportPointToTempVector(baseTable, layName=cleanName, fields = baseTableFields)
    vl.setDisplayField('[% "text" %]')
    
    if cleanName == 'notes':
      vl.loadNamedStyle(os.path.join(currentPath,'styles','note_symb.qml'))
    # add to the TOC
    QgsMapLayerRegistry.instance().addMapLayer(vl)
    
    
  
def ExportNotes(DBcursor,currentPath):
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
    note = convertToStringList(note)
    notesTable.addRecordList(note)
    
  vl = exportPointToTempVector(notesTable, layName='notes', fields = notesTableFields)
  vl.setDisplayField('[% "text" %]')
  vl.loadNamedStyle(os.path.join(currentPath,'styles','note_symb.qml'))
  # add to the TOC
  QgsMapLayerRegistry.instance().addMapLayer(vl)

  
def ExportImages(DBcursor,currentPath,pathToDB):
  #create a table with image positions
  images = DBcursor.execute("SELECT * FROM images")
  imagesTable = Table(["_id","lon","lat","altim","azim","imagedata_id","ts","text","note_id","isdirty"])
  imagesTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double), QgsField("lat", QVariant.Double),QgsField("altim", QVariant.Double),QgsField("azim", QVariant.Double), \
                                      QgsField("imagedata_id", QVariant.Int),QgsField("ts", QVariant.String),QgsField("text", QVariant.String), \
                                      QgsField("note_id", QVariant.Int), QgsField("isdirty", QVariant.Int)]
 
  for img in images:
    img = convertToStringList(img)
    imagesTable.addRecordList(img)
    
  vl = exportPointToTempVector(imagesTable, layName='image positions', fields = imagesTableFields)
  vl.loadNamedStyle(os.path.join(currentPath,'styles','image_symb.qml'))
  
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
  modPath = os.path.join(os.path.join(currentpath, os.pardir),'imageviewer','ImageViewer.py')
  if platform.system() == 'Windows':
    modPath = modPath.replace("\\","/")
  
  SIact = 'from PyQt4.QtCore import QUrl; from PyQt4.QtWebKit import QWebView; import imp; foo = imp.load_source("ImageViewer", "'
  SIact += modPath
  SIact += '");'
  SIact += 'imv = foo.ImageViewer();'
  SIact += "fn = '"+os.path.join(pathToImages,'[% "text" %]')+"'"+";"
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
  
def ExportBookmarks(DBcursor,currentPath):
  #create a table with bookmarks
  bookmarks = DBcursor.execute("SELECT * FROM bookmarks")
  bookmarksTable = Table(["_id","lon","lat","zoom","bnorth","bsouth","bwest","beast","text"])
  bookmarksTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double), QgsField("lat", QVariant.Double), \
                                      QgsField("zoom", QVariant.Double),QgsField("bnorth", QVariant.Double), \
                                      QgsField("bsouth", QVariant.Double),QgsField("bwest", QVariant.Double), \
                                      QgsField("beast", QVariant.Double),QgsField("text", QVariant.String)]
 
  for bkm in bookmarks:
    bkm = convertToStringList(bkm)
    bookmarksTable.addRecordList(bkm)
    
  vl = exportPointToTempVector(bookmarksTable, layName='bookmarks', fields = bookmarksTableFields)
  vl.setDisplayField('[% "text" %]')
  vl.loadNamedStyle(os.path.join(currentPath,'styles','bookmark_symb.qml'))
  # add to the TOC
  QgsMapLayerRegistry.instance().addMapLayer(vl)

  
def ExportGPSlogs(DBcursor,currentPath):
  #create a table with logs
  gpslogs = DBcursor.execute("SELECT * FROM gpslogs") 
  gpslogsTable = Table(["_id","startts","endts","lengthm","isdirty","text"])
  gpslogsTableFields = [QgsField("_id", QVariant.Int), QgsField("startts", QVariant.Double), QgsField("endts", QVariant.Double), \
                                      QgsField("lengthm", QVariant.Double),QgsField("isdirty", QVariant.Int),QgsField("text", QVariant.String)]
  # load the list of gpslogs
  for l in gpslogs:
    l = convertToStringList(l)
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
      gpslogd = convertToStringList(gpslogd)
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
    vl.loadNamedStyle(os.path.join(currentPath,'styles','tracklog_symb.qml'))
    # add to the TOC
    QgsMapLayerRegistry.instance().addMapLayer(vl)

  
def ExportDataset(pathToDB, DBname,currentPath):
  # connect to database
  fullDBname = os.path.join(pathToDB,DBname)
  con = sqlite.connect(fullDBname)
  cur = con.cursor()
  # export GPSlogs
  ExportGPSlogs(cur,currentPath)
  #export notes with form attributes
  ExportFormNotes(cur,currentPath)
  # export Images
  ExportImages(cur,currentPath,pathToDB)
  # export Bookmarks
  ExportBookmarks(cur,currentPath)
  #close connection
  cur.close()
  con.close()


def ExportDataset_old(pathToDB, DBname,currentPath):
  # connect to database
  fullDBname = os.path.join(pathToDB,DBname)
  print fullDBname
  con = sqlite.connect(fullDBname)
  cur = con.cursor()
  #create a table with notes
  # "_id","lon","lat","altim","ts","description","text","form","style","isdirty"
  notes = cur.execute("SELECT * FROM notes")
  notesTable = Table(["_id","lon","lat","altim","ts","description","text","form","style","isdirty"])
  notesTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double), QgsField("lat", QVariant.Double),QgsField("altim", QVariant.Double), \
                                      QgsField("ts", QVariant.String),QgsField("description", QVariant.String), \
                                      QgsField("form", QVariant.String),QgsField("style", QVariant.String), \
                                      QgsField("isdirty", QVariant.Int)]
                                      
  for note in notes:
    note = convertToStringList(note)
    notesTable.addRecordList(note)
    
  vl = exportPointToTempVector(notesTable, layName='notes', fields = notesTableFields)
  vl.loadNamedStyle(os.path.join(currentPath,'styles','note_symb.qml'))
  # add to the TOC
  QgsMapLayerRegistry.instance().addMapLayer(vl)

  #create a table with image positions
  images = cur.execute("SELECT * FROM images")
  imagesTable = Table(["_id","lon","lat","altim","azim","imagedata_id","ts","text","note_id","isdirty"])
  imagesTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double), QgsField("lat", QVariant.Double),QgsField("altim", QVariant.Double),QgsField("azim", QVariant.Double), \
                                      QgsField("imagedata_id", QVariant.Int),QgsField("ts", QVariant.String),QgsField("text", QVariant.String), \
                                      QgsField("note_id", QVariant.Int), QgsField("isdirty", QVariant.Int)]
 
  for img in images:
    img = convertToStringList(img)
    imagesTable.addRecordList(img)
    
  vl = exportPointToTempVector(imagesTable, layName='image positions', fields = imagesTableFields)
  vl.loadNamedStyle(os.path.join(currentPath,'styles','image_symb.qml'))
  
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
    imgsData = cur.execute("SELECT * FROM imagedata WHERE _id = " + str(imgID))
    imgName = imgNames[i]
    #print imgID, imgName
    
    for imgData in imgsData:
      with open(os.path.join(pathToImages,imgName), "wb") as output_file:
        output_file.write(imgData[1])
      with open(os.path.join(pathToThunbnails,imgName), "wb") as output_file:
        output_file.write(imgData[2])
    i +=1

  
  # add Show Image Action
  SIact = 'from PyQt4.QtCore import QUrl; from PyQt4.QtWebKit import QWebView;  myWV = QWebView(None); '
  SIact += 'myWV.setWindowTitle('+'"'+'[% "text" %]'+'"'+'); '
  SIact += 'myWV.load(QUrl('
  SIact += "'"+os.path.join(pathToImages,'[% "text" %]')+"'"+")); myWV.show()"
  actions = vl.actions()
  actions.addAction(QgsAction.GenericPython, "Show Image",SIact)
  
  # add tip image
  tipImg = '[% "text" %]'
  tipImg += '<br><img src="'+os.path.join(pathToThunbnails,'[% "text" %]')+'" />'
  vl.setMapTipTemplate(tipImg)
  
  # add to the TOC
  QgsMapLayerRegistry.instance().addMapLayer(vl)

  #create a table with bookmarks
  bookmarks = cur.execute("SELECT * FROM bookmarks")
  bookmarksTable = Table(["_id","lon","lat","zoom","bnorth","bsouth","bwest","beast","text"])
  bookmarksTableFields = [QgsField("_id", QVariant.Int), QgsField("lon", QVariant.Double), QgsField("lat", QVariant.Double), \
                                      QgsField("zoom", QVariant.Double),QgsField("bnorth", QVariant.Double), \
                                      QgsField("bsouth", QVariant.Double),QgsField("bwest", QVariant.Double), \
                                      QgsField("beast", QVariant.Double),QgsField("text", QVariant.String)]
 
  for bkm in bookmarks:
    bkm = convertToStringList(bkm)
    bookmarksTable.addRecordList(bkm)
    
  vl = exportPointToTempVector(bookmarksTable, layName='bookmarks', fields = bookmarksTableFields)
  vl.loadNamedStyle(os.path.join(currentPath,'styles','bookmark_symb.qml'))
  # add to the TOC
  QgsMapLayerRegistry.instance().addMapLayer(vl)

  #create a table with logs
  gpslogs = cur.execute("SELECT * FROM gpslogs") 
  gpslogsTable = Table(["_id","startts","endts","lengthm","isdirty","text"])
  gpslogsTableFields = [QgsField("_id", QVariant.Int), QgsField("startts", QVariant.Double), QgsField("endts", QVariant.Double), \
                                      QgsField("lengthm", QVariant.Double),QgsField("isdirty", QVariant.Int),QgsField("text", QVariant.String)]
  # load the list of gpslogs
  for l in gpslogs:
    l = convertToStringList(l)
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
    gpslogData  = cur.execute("SELECT * FROM gpslogsdata WHERE logid = " + logID + " ORDER BY _id")
    gpslogTable = Table(["_id","lon","lat","altim","ts","logid"])
    
    for gpslogd in gpslogData:
      gpslogd = convertToStringList(gpslogd)
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
    vl.loadNamedStyle(os.path.join(currentPath,'styles','tracklog_symb.qml'))
    # add to the TOC
    QgsMapLayerRegistry.instance().addMapLayer(vl)
    
  #close connection
  cur.close()
  con.close()
