class ParameterGpap(ParameterDataObject):
  
  default_metadata = {
        'widget_wrapper': 'processing.gui.wrappers.GpapWidgetWrapper'
    }

    def __init__(self, name='', description='', isFolder=False, optional=True, ext=None):
        Parameter.__init__(self, name, description, None, parseBool(optional))
        self.ext = ext
        self.isFolder = parseBool(isFolder)

    def getValueAsCommandLineParameter(self):
        return '"' + str(self.value) + '"'

    def setValue(self, obj):
        if obj is None or obj.strip() == '':
            if not self.optional:
                return False
            self.value = None if obj is None else obj.strip()
            return True

        if self.ext is not None and obj != '' and not obj.endswith(self.ext):
            return False
        self.value = str(obj)
        return True
    
    def getFileFilter(self):
        exts = ['gpap']
        for i in range(len(exts)):
            exts[i] = self.tr('%s files(*.%s)', 'gpap DB') % (exts[i].upper(), exts[i].lower())
        return ';;'.join(exts)
        
    def getAsScriptCode(self):
        param_type = ''
        if self.optional:
            param_type += 'optional '
        param_type += 'file'
        return '##' + self.name + '=' + param_type

    def typeName(self):
        if self.isFolder:
            return 'directory'
        else:
            return 'file'

    def getAsScriptCode(self):
        param_type = ''
        if self.optional:
            param_type += 'optional '
        param_type += 'file'
        return '##' + self.name + '=' + param_type

    @classmethod
    def fromScriptCode(self, line):
        isOptional, name, definition = _splitParameterOptions(line)
        if definition.startswith("file"):
            descName = _createDescriptiveName(name)
        return ParameterFile(name, descName, definition.startswith("file"), isOptional)