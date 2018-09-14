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

import os
import platform

from qgis.core import (QgsProcessingLayerPostProcessorInterface,
									QgsVectorLayer,
									QgsAction)

class ImagePostProcessor(QgsProcessingLayerPostProcessorInterface):

	instance = None

	def postProcessLayer(self, layer, context, feedback):  # pylint: disable=unused-argument
		if not isinstance(layer, QgsVectorLayer):
			return
			
		# load default style
		layer.loadNamedStyle(os.path.join(self.CURRENTPATH,'styles','image_symb.qml'))

		# add action
		modPath = os.path.join(self.CURRENTPATH,'imageviewer','imageviewer.py')
		if platform.system() == 'Windows':
			modPath = modPath.replace("\\","/")
			
		
		SIact = 'import imp; foo = imp.load_source("ImageViewer", "'
		SIact += modPath
		SIact += '");'
		SIact += 'imv = foo.ImageViewer();'
		SIact += "fn = r'"+os.path.join(self.PATHTOIMAGES,'[% "text" %]')+"'"+";"
		SIact += 'imv.openImage(fn);'
		SIact += 'imv.show();'
		#SIact += 'myWV.setWindowTitle('+'"'+'[% "text" %]'+'"'+'); '
		#SIact += 'myWV.load(QUrl('
		#SIact += "'"+os.path.join(pathToImages,'[% "text" %]')+"'"+")); myWV.show()"
		actions = layer.actions()
		actions.addAction(QgsAction.GenericPython, "Show Image",SIact)
		#act = QgsAction(QgsAction.GenericPython, "Show Image",SIact, '', False, '', 'Layer')
		#actions.addAction(act)

		# add tip image
		#~ tipImg = '[% "text" %]'
		#~ tipImg += '<br><img src="'+os.path.join(self.PATHTOTHUNBNAILS,'[% "text" %]')+'" />'
		#~ layer.setDisplayExpression(tipImg)
		
	def setPaths(self,currentPath,pathToImages,pathToThunbnails):
		self.CURRENTPATH = currentPath
		self.PATHTOIMAGES = pathToImages
		self.PATHTOTHUNBNAILS = pathToThunbnails

	# Hack to work around sip bug!
	@staticmethod
	def create() -> 'ImagePostProcessor':
		"""
		Returns a new instance of the post processor, keeping a reference to the sip
		wrapper so that sip doesn't get confused with the Python subclass and call
		the base wrapper implementation instead... ahhh sip, you wonderful piece of sip
		"""
		ImagePostProcessor.instance = ImagePostProcessor()
		return ImagePostProcessor.instance