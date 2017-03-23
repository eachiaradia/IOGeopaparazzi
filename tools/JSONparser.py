#!/usr/bin/python
"""
/***************************************************************************
Name			 	 : JSONparser.py
Description : A JSON parser for ExportGeopaparazzi
Date          : 07/Jan/17 
copyright   : (C) 2017 by Enrico A. Chiaradia
email         : enrico.chiaradia@yahoo.it 
credits       :


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

import json
from qgis.core import *
from qgis.gui import *

from PyQt4.QtCore import QVariant  

class JSONparser: 
  """
  Geopaparazzi json string structure:

  section
  --> section['sectionname'] = the name of the section (alias "main form")
  --> section['sectiondescription'] = the description of the section
  --> section['forms'] = a list of forms
        --> form1
              --> form1['formname'] = the name of the form
              --> form1['formitems'] = a list of fields of the form
                    --> formitem1
                          --> formitem1['type'] = the type of field
                          --> formitem1['mandatory'] = yes/no
                          --> formitem1['values'] = suggested values (usefull for combobox)
                          --> formitem1['key'] = the name of the formitem (i.e. the name of the attribute)
                          --> formitem1['value'] = the value inserted by the user (i.e. the attribute)
                    --> formitem2
                    --> ...
        --> form2
        --> ...
        
  As DBF file limits field name to 10 character, keys are trimmed. Also white spaces are removed from the key.
  To prevent multiple copies of field names, an incresing number was added to replace the last chars from the key

  """

  def __init__(self,jsonText):
    self.keys = []
    self.values = []
    self.types = []
    self.fields = []
    self.section = json.loads(jsonText)
    self.sectionName = self.section['sectionname']
    self.sectionDescription = self.section['sectiondescription']
  
  def parseKeyValue(self):
    self.forms = self.section['forms']
    for form in self.forms:
      formitems = self.parseForm(form)[1]
      for fit in formitems:
        res = self.parseFormItem(fit)
        type = self.parseType(res[0])
        self.types.append(type)
        key = res[3]
        key = self.cleanKey(key)
        key = self.keyExist(key,self.keys)
        value = res[4]
        self.keys.append(key)
        self.fields.append(QgsField(key,type))
        self.values.append(value)

  def parseType(self,type):
      return {
        'string': QVariant.String,
        'dynamicstring': QVariant.String,
        'double':QVariant.Double,
        'integer':QVariant.Int,
        'date':QVariant.String,
        'time':QVariant.String,
        'label':QVariant.String,
        'labelwithline':QVariant.String,
        'boolean':QVariant.String,
        'stringcombo':QVariant.String,
        'multistringcombo':QVariant.String,
        'connectedstringcombo':QVariant.String,
        'pictures':QVariant.Int,
        'sketch':QVariant.Int,
        'map':QVariant.Int,
        'hidden':QVariant.String,
        'primary_key':QVariant.String,
      }[type]

  def parseForm(self, form):
    try:
      formname = form['formname']
      formitems = form['formitems']
    except:
      formname = self.parseFormItem(form)[3]
      formitems = [form]
      
    return formname, formitems

  def parseFormItem(self, formitem):
    formKeys = formitem.keys()
    type = ''
    mandatory = ''
    values = ''
    key = ''
    value = ''
    
    if 'type' in formKeys:
      type = formitem['type']
    
    if 'mandatory' in formKeys:
      mandatory = formitem['mandatory']
    
    if type[-5:] == 'combo':
      values = formitem['values']
    else:
      values = []
    
    if 'key' in formKeys:
      key = formitem['key']
    
    if 'value' in formKeys:
      value = formitem['value']
    
    return type,mandatory, values, key, value
  

  def cleanKey(self,key):
    # remove spaces and trim to 10 character
    key = key.strip()
    key = key.replace(' ','_')
    key = key[0:9]
    return key
    
  def keyExist(self,key, keylist):
    flag = True
    testkey = key
    nchar = len(key) 
    i = 0
    while flag:
      try:
          b=keylist.index(testkey)
      except ValueError:
          #exit loop
          flag = False
      else:
          #test a new value
          flag = True
          i+=1
          if i<10:
            testkey = key[0:nchar-1]+str(i)
          else:
            testkey = key[0:nchar-2]+str(i)
    
    return testkey
    
if __name__ == '__main__':
  # test with long keys with spaces
  #testTxt = '{"sectionname":"Museum","sectiondescription":"a rural village museum","forms":[{"formname":"General data","formitems":[{"value":"ul torc","type":"string","key":"name","islabel":"true","mandatory":"yes"},{"value":"piazza XI febbraio","type":"string","key":"street","mandatory":"no"},{"value":"1","type":"integer","key":"number","mandatory":"no"}]},{"formname":"Technical data","formitems":[{"value":"false","type":"boolean","key":"indoor","mandatory":"yes"},{"value":"<= 10","values":{"items":[{"item":""},{"item":"<= 10"},{"item":"10 < num. <= 20"},{"item":"> 20"}]},"type":"stringcombo","key":"number of objects","mandatory":"no"}]},{"formname":"Media","formitems":[{"value":"5","type":"pictures","key":"Images","mandatory":"no"}]}]}'
  # test with repeated keys
  #testTxt = '{"sectionname":"Museum","sectiondescription":"a rural village museum","forms":[{"formname":"General data","formitems":[{"value":"ul torc","type":"string","key":"name","islabel":"true","mandatory":"yes"},{"value":"piazza XI febbraio","type":"string","key":"street","mandatory":"no"},{"value":"1","type":"integer","key":"number","mandatory":"no"}]},{"formname":"Technical data","formitems":[{"value":"false","type":"boolean","key":"indoor","mandatory":"yes"},{"value":"<= 10","values":{"items":[{"item":""},{"item":"<= 10"},{"item":"10 < num. <= 20"},{"item":"> 20"}]},"type":"stringcombo","key":"number","mandatory":"no"}]},{"formname":"Media","formitems":[{"value":"5","type":"pictures","key":"Images","mandatory":"no"}]}]}'
  # test with white space and repeated keys
  #testTxt = '{"sectionname":"Museum","sectiondescription":"a rural village museum","forms":[{"formname":"General data","formitems":[{"value":"ul torc","type":"string","key":"name","islabel":"true","mandatory":"yes"},{"value":"piazza XI febbraio","type":"string","key":"street","mandatory":"no"},{"value":"1","type":"integer","key":"number","mandatory":"no"}]},{"formname":"Technical data","formitems":[{"value":"false","type":"boolean","key":"indoor","mandatory":"yes"},{"value":"<= 10","values":{"items":[{"item":""},{"item":"<= 10"},{"item":"10 < num. <= 20"},{"item":"> 20"}]},"type":"stringcombo","key":" number ","mandatory":"no"}]},{"formname":"Media","formitems":[{"value":"5","type":"pictures","key":"Images","mandatory":"no"}]}]}'
  # test with white space
  testTxt = '{"sectionname":"Museum","sectiondescription":"a rural village museum","forms":[{"formname":"General data","formitems":[{"value":"ul torc","type":"string","key":"name","islabel":"true","mandatory":"yes"},{"value":"piazza XI febbraio","type":"string","key":"street","mandatory":"no"},{"value":"1","type":"integer","key":"number","mandatory":"no"}]},{"formname":"Technical data","formitems":[{"value":"false","type":"boolean","key":"indoor","mandatory":"yes"},{"value":"<= 10","values":{"items":[{"item":""},{"item":"<= 10"},{"item":"10 < num. <= 20"},{"item":"> 20"}]},"type":"stringcombo","key":" number of  ","mandatory":"no"}]},{"formname":"Media","formitems":[{"value":"5","type":"pictures","key":"Images","mandatory":"no"}]}]}'

  parser = JSONparser(testTxt)
  print parser.sectionName
  parser.parseKeyValue()
  print parser.keys
  print parser.values
  print parser.fields
    