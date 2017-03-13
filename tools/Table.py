"""
/***************************************************************************
Name			 	 : Table.py
Description          : Just another Geopaparazzi database exporter
Date                 : 12/Oct/15 
copyright            : (C) 2015 by Enrico A. Chiaradia
email                : enrico.chiaradia@yahoo.it 
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

class Table: 
  def __init__(self,fldNames):
    self.lod = [] # "list of lists"
    self.fldNames = fldNames # a list of field Name
    # add as many columns as fldNames
    for f in self.fldNames:
      self.lod.append([])
    
  def addRecordList(self, newRecord):
    #print 'IN addRecordList:'
    #print newRecord
    for i in range(0,len(self.fldNames)):
      #print newRecord[i]
      self.lod[i].append(newRecord[i])
      
    #print self.lod
    
  def addRecordDict(self, newRecord):
    #print 'IN addRecordDict:'
    #print newRecord
    i = 0
    for fld in self.fldNames:
      self.lod[i].append(newRecord[fld])
      i+=1
    
  def saveLod(self, csv_fp):
    pass    
  
  def getNumOfRec(self):
    return len(self.lod[0])
    
  def getRecord(self,rowidx):
    rowvals = []
    for i in range(0,len(self.fldNames)):
      rowvals.append(self.lod[i][rowidx])
      
    return rowvals
    
  def getColumn(self,colname):
    colidx = self.fldNames.index(colname)
    return self.lod[colidx]
    
  def getValue(self,colname,rowidx):
    colidx = self.fldNames.index(colname)
    return self.lod[colidx][rowidx]