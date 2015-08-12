#!/usr/bin/env python
import os
from PySide import QtCore, QtGui
from SceneGraph.core import log


class Settings(QtCore.QSettings):

    def __init__(self, filename, frmt=QtCore.QSettings.IniFormat, parent=None, max_files=10):
        QtCore.QSettings.__init__(self, filename, frmt, parent)

        self._max_files     = max_files
        self._parent        = parent
        self._groups        = ['MainWindow', 'RecentFiles', 'Preferences']
        self.initialize()

    def initialize(self):
        """
        Setup the file for the first time.
        """
        if 'MainWindow' not in self.childGroups():
            if self._parent is not None:
                self.setValue('MainWindow/geometry/default', self._parent.saveGeometry())
                self.setValue('MainWindow/windowState/default', self._parent.saveState())                

        if 'RecentFiles' not in self.childGroups():
            self.beginWriteArray('RecentFiles', 0)
            self.endArray()

        while self.group():
            self.endGroup()
        self.initializePreferences()

    def initializePreferences(self):
        """
        Set up the default preferences from global options.
        """
        if 'Preferences' not in self.childGroups():
            self.beginGroup("Preferences")
            # query the defauls from options.
            for option in options.SCENEGRAPH_PREFERENCES:
                if 'default' in options.SCENEGRAPH_PREFERENCES.get(option):
                    self.setValue('default/%s' % option, options.SCENEGRAPH_PREFERENCES.get(option).get('default'))

            while self.group():
                self.endGroup()

    def window_keys(self):
        """
        Resturns a list of all window keys to save for layouts, or rebuilding last
        layout on launch.

        :returns: list of keys to query/save.
        :rtype: list
        """
        if self._parent is None:
            return []
        result = ['MainWindow']
        for dock in self._parent.findChildren(QtGui.QDockWidget):
            dock_name = dock.objectName()
            result.append(str(dock_name))
        return result

    def get_layouts(self):
        """
        Returns a list of window layout names.

        :returns: list of window layout names.
        :rtype: list
        """
        layout_names = []
        layout_keys = ['%s/geometry' % x for x in self.window_keys()]
        

        for k in self.allKeys():
            if 'geometry' in k:
                attrs = k.split('/geometry/')
                if len(attrs) > 1:
                    layout_names.append(str(attrs[-1]))

        return sorted(list(set(layout_names)))

    def saveLayout(self, layout):
        """
        Save a named layout.

        :param str layout: layout name to save.
        """
        log.info('saving layout: "%s"' % layout)
        self.setValue("MainWindow/geometry/%s" % layout, self._parent.saveGeometry())
        self.setValue("MainWindow/windowState/%s" % layout, self._parent.saveState())

        for dock in self._parent.findChildren(QtGui.QDockWidget):
            dock_name = dock.objectName()
            self.setValue("%s/geometry/%s" % (dock_name, layout), dock.saveGeometry())

    def restoreLayout(self, layout):
        """
        Restore a named layout.

        :param str layout: layout name to restore.
        """
        log.info('restoring layout: "%s"' % layout)
        window_keys = self.window_keys()

        for widget_name in window_keys:            
            key_name = '%s/geometry/%s' % (widget_name, layout)
            if widget_name != 'MainWindow':
                dock = self._parent.findChildren(QtGui.QDockWidget, widget_name)
                if dock:
                    dock[0].restoreGeometry(value)
            else:
                if key_name in self.allKeys():                    
                    value = self.value(key_name)
                    self._parent.restoreGeometry(value)

                window_state = '%s/windowState/%s' % (widget_name, layout)
                if window_state in self.allKeys():                    
                    self._parent.restoreState(self.value(window_state))

    def deleteLayout(self, layout):
        """
        Delete a named layout.

        :param str layout: layout name to restore.
        """
        log.info('deleting layout: "%s"' % layout)
        window_keys = self.window_keys()

        for widget_name in window_keys:            
            key_name = '%s/geometry/%s' % (widget_name, layout)
            if key_name in self.allKeys():                    
                self.remove(key_name)        

            if widget_name == 'MainWindow':
                window_state = '%s/windowState/%s' % (widget_name, layout)
                if window_state in self.allKeys():
                    self.remove(window_state)


    def getDefaultValue(self, key, *groups):
        """
        Return the default values for a group.

        :param str key: key to search for.
        :returns: default value of key (None if not found)
        """
        if self.group():
            try:
                self.endGroup()
            except:
                pass

        result = None
        group_name = groups[0]
        for group in groups[1:]:
            group_name += "/%s" % group

        group_name += "/%s" % "default"
        group_name += "/%s" % key

        if group_name in self.allKeys():
            result = self.value(group_name)
        return result

    def save(self, key='default'):
        """
        Save, with optional category.

         * unused
        """
        self.beginGroup("Mainwindow/%s" % key)
        self.setValue("size", QtCore.QSize(self._parent.width(), self._parent.height()))
        self.setValue("pos", self._parent.pos())
        self.setValue("windowState", self._parent.saveState())
        self.endGroup()

    def deleteFile(self):
        """
        Delete the preferences file on disk.
        """
        log.info('deleting settings: "%s"' % self.fileName())
        return os.remove(self.fileName())

    #- Recent Files ----
    @property
    def recent_files(self):
        """
        Returns a tuple of recent files, no larger than the max 
        and reversed (for usage in menus).

         * unused
        """
        files = self.getRecentFiles()
        tmp = []
        for f in reversed(files):
            tmp.append(f)
        return tuple(tmp[:self._max_files])

    def getRecentFiles(self):
        """
        Get a tuple of the most recent files.
        """
        recent_files = []
        cnt = self.beginReadArray('RecentFiles')
        for i in range(cnt):
            self.setArrayIndex(i)
            fn = self.value('file')
            recent_files.append(fn)
        self.endArray()
        return tuple(recent_files)

    def addRecentFile(self, filename):
        """
        Adds a recent file to the stack.
        """
        recent_files = self.getRecentFiles()
        if filename in recent_files:
            recent_files = tuple(x for x in recent_files if x != filename)

        recent_files = recent_files + (filename,)
        self.beginWriteArray('RecentFiles')
        for i in range(len(recent_files)):
            self.setArrayIndex(i)
            self.setValue('file', recent_files[i])
        self.endArray()

    def clearRecentFiles(self):
        self.remove('RecentFiles')