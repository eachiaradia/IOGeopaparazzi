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

from PyQt4 import QtCore, QtGui
import operator
import sys
import os.path as osp
import os

#setting the path variable for icon
currentpath = osp.dirname(sys.modules[__name__].__file__)

class ImageLabel(QtGui.QWidget):
  def __init__(self):
    super(ImageLabel, self).__init__()
    # add Qlabel
    self.label = QtGui.QLabel()
    self.label.setAlignment(QtCore.Qt.AlignCenter);
    # set size policy
    sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
    sizePolicy.setHeightForWidth(True)
    self.label.setSizePolicy(sizePolicy)
    self.label.setBackgroundRole(QtGui.QPalette.Base)
    # add label to a HLayout
    layout=QtGui.QHBoxLayout()
    layout.addWidget(self.label);
    self.setLayout(layout);


class ImageViewer(QtGui.QMainWindow):
  def __init__(self):
    super(ImageViewer, self).__init__()
    
    # add a place to load the image
    self.imageLabel = ImageLabel()
    self.setCentralWidget(self.imageLabel)
    
    # add a toolbar
    self.createActions()
    self.createToolBars()
    
    # set the title of the window
    self.setWindowTitle("Image Viewer")
    
    # set maximum mainwindow dimension
    self.resize(640, 480)
    
    # set the rotation
    self.rotation = 0
    
  def createToolBars(self):
    self.toolbar = self.addToolBar('View')
    self.toolbar.isFloatable = False
    self.toolbar.isMovable = False
    self.toolbar.addAction(self.rotL)
    self.toolbar.addAction(self.rotR)
    self.toolbar.addAction(self.save)
    
  def createActions(self):
    self.rotR = QtGui.QAction(QtGui.QIcon(currentpath+"/rotation_R.png"),"Rotate &Right (90%)", self,
            shortcut="Ctrl+R", enabled=True, triggered=self.rot90)

    self.rotL = QtGui.QAction(QtGui.QIcon(currentpath+"/rotation_L.png"),"Rotate &Left (-90%)", self,
            shortcut="Ctrl+L", enabled=True, triggered=self.invrot90)
    
    self.save = QtGui.QAction(QtGui.QIcon(currentpath+"/save.png"),"Save", self,
            shortcut="Ctrl+S", enabled=True, triggered=self.saveImage)
  
  def invrot90(self):
    self.rotate_pixmap(-90)
                              
  def rot90(self):
    self.rotate_pixmap(90)
    
  def rotate_pixmap(self, rotation):
    # credits: http://stackoverflow.com/questions/31892557/rotating-a-pixmap-in-pyqt4-gives-undesired-translation
    #---- rotate ----
    # Rotate from initial image to avoid cumulative deformation from
    # transformation
    pixmap = QtGui.QPixmap(self.image)
    transform = QtGui.QTransform().rotate(rotation)
    pixmap = pixmap.transformed(transform, QtCore.Qt.SmoothTransformation)
    #---- update label ----
    self.imageLabel.label.resize(pixmap.size())
    self.imageLabel.label.setPixmap(pixmap)
    self.image = QtGui.QImage(pixmap)
    self.rotation += rotation

  def rotate_image(self, image,rotation):
    # credits: http://stackoverflow.com/questions/31892557/rotating-a-pixmap-in-pyqt4-gives-undesired-translation
    #---- rotate ----
    # Rotate from initial image to avoid cumulative deformation from
    # transformation
    pixmap = QtGui.QPixmap(image)
    transform = QtGui.QTransform().rotate(rotation)
    pixmap = pixmap.transformed(transform, QtCore.Qt.SmoothTransformation)
    image = QtGui.QImage(pixmap)
    return image

  def saveImage(self):
    pathToImage = self.fileName
    pathToThumb = self.fileName.replace('images','thunbnails')
    # open image and rotate it
    img = QtGui.QImage(pathToImage)
    img = self.rotate_image(img,self.rotation)
    img.save(pathToImage,None,90)
    if os.path.exists(pathToThumb):
      tmb = QtGui.QImage(pathToThumb)
      tmb = self.rotate_image(tmb,self.rotation)
      tmb.save(pathToThumb,None,90)
    else:
      QtGui.QMessageBox.information(self, "Image Viewer",
                        "Cannot load %s." % pathToThumb)
      
    self.rotation = 0
  
  def openImage(self, filename = ''):
    self.fileName = filename
    if self.fileName != '':
      self.setWindowTitle(self.fileName)
      # load image
      self.image = QtGui.QImage(self.fileName)
      self.imagew = self.image.width()
      self.imageh = self.image.height()
      # scale image to the maximum frame size
      self.resFactor = min(640.0/self.imagew,640.0/self.imageh)
      self.image = self.image.scaled(int(self.resFactor*self.imagew), int(self.resFactor*self.imageh))
      if self.image.isNull():
        QtGui.QMessageBox.information(self, "Image Viewer",
                "Cannot load %s." % self.fileName)
        return

      
      # assign image to the Qlabel
      self.imageLabel.label.setPixmap(QtGui.QPixmap.fromImage(self.image))
      self.imageLabel.label.adjustSize()
      # set the window dimension to fit the image
      self.resize(int(self.resFactor*self.imagew), int(self.resFactor*self.imageh))
      
      
      