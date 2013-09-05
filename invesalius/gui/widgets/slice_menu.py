#!/usr/bin/env python
# -*- coding: UTF-8 -*-

#--------------------------------------------------------------------------
# Software:     InVesalius - Software de Reconstrucao 3D de Imagens Medicas
# Copyright:    (C) 2001  Centro de Pesquisas Renato Archer
# Homepage:     http://www.softwarepublico.gov.br
# Contact:      invesalius@cti.gov.br
# License:      GNU - GPL 2 (LICENSE.txt/LICENCA.txt)
#--------------------------------------------------------------------------
#    Este programa e software livre; voce pode redistribui-lo e/ou
#    modifica-lo sob os termos da Licenca Publica Geral GNU, conforme
#    publicada pela Free Software Foundation; de acordo com a versao 2
#    da Licenca.
#
#    Este programa eh distribuido na expectativa de ser util, mas SEM
#    QUALQUER GARANTIA; sem mesmo a garantia implicita de
#    COMERCIALIZACAO ou de ADEQUACAO A QUALQUER PROPOSITO EM
#    PARTICULAR. Consulte a Licenca Publica Geral GNU para obter mais
#    detalhes.
#--------------------------------------------------------------------------
import sys
from collections import OrderedDict

import wx
from wx.lib.pubsub import pub as Publisher

import constants as const
import data.slice_ as sl
import presets

from gui.dialogs import ClutImagedataDialog

PROJECTIONS_ID = OrderedDict(((_('Normal'), const.PROJECTION_NORMAL),
                              (_('MaxIP'), const.PROJECTION_MaxIP),
                              (_('MinIP'), const.PROJECTION_MinIP),
                              (_('MeanIP'), const.PROJECTION_MeanIP),
                              (_('MIDA'), const.PROJECTION_MIDA),
                              (_('Contour MaxIP'), const.PROJECTION_CONTOUR_MIP),
                              (_('Contour MIDA'), const.PROJECTION_CONTOUR_MIDA),) ) 
                

class SliceMenu(wx.Menu):
    def __init__(self):
        wx.Menu.__init__(self)
        self.ID_TO_TOOL_ITEM = {}
        self.cdialog = None

        #------------ Sub menu of the window and level ----------
        submenu_wl = wx.Menu()

        self._gen_event = True

        #Window and level from DICOM
        new_id = self.id_wl_first = wx.NewId()
        wl_item = wx.MenuItem(submenu_wl, new_id,\
                            _('Default'), kind=wx.ITEM_RADIO)
        submenu_wl.AppendItem(wl_item)
        self.ID_TO_TOOL_ITEM[new_id] = wl_item

        #Case the user change window and level
        new_id = self.other_wl_id = wx.NewId()
        wl_item = wx.MenuItem(submenu_wl, new_id,\
                            _('Manual'), kind=wx.ITEM_RADIO)
        submenu_wl.AppendItem(wl_item)
        self.ID_TO_TOOL_ITEM[new_id] = wl_item

        for name in sorted(const.WINDOW_LEVEL):
            if not(name == _('Default') or name == _('Manual')):
                new_id = wx.NewId()
                wl_item = wx.MenuItem(submenu_wl, new_id,\
                                    name, kind=wx.ITEM_RADIO)
                submenu_wl.AppendItem(wl_item)
                self.ID_TO_TOOL_ITEM[new_id] = wl_item



        #----------- Sub menu of the save and load options ---------
        #submenu_wl.AppendSeparator()
        #options = [_("Save current values"),
        #           _("Save current values as..."),_("Load values")]

        #for name in options:
        #    new_id = wx.NewId()
        #    wl_item = wx.MenuItem(submenu_wl, new_id,\
        #                    name)
        #    submenu_wl.AppendItem(wl_item)
        #    self.ID_TO_TOOL_ITEM[new_id] = wl_item


        #------------ Sub menu of the pseudo colors ----------------
        self.pseudo_color_items = {}
        submenu_pseudo_colours = wx.Menu()
        self.pseudo_color_items = {}
        new_id = self.id_pseudo_first = wx.NewId()
        color_item = wx.MenuItem(submenu_pseudo_colours, new_id,\
                            _("Default "), kind=wx.ITEM_CHECK)
        submenu_pseudo_colours.AppendItem(color_item)
        self.ID_TO_TOOL_ITEM[new_id] = color_item
        self.pseudo_color_items[new_id] = color_item

        for name in sorted(const.SLICE_COLOR_TABLE):
            if not(name == _("Default ")):
                new_id = wx.NewId()
                color_item = wx.MenuItem(submenu_wl, new_id,\
                                    name, kind=wx.ITEM_CHECK)
                submenu_pseudo_colours.AppendItem(color_item)
                self.ID_TO_TOOL_ITEM[new_id] = color_item
                self.pseudo_color_items[new_id] = color_item

        self.plist_presets = presets.get_wwwl_presets()
        for name in sorted(self.plist_presets):
            new_id = wx.NewId()
            color_item = wx.MenuItem(submenu_wl, new_id, name, kind=wx.ITEM_CHECK)
            submenu_pseudo_colours.AppendItem(color_item)
            self.ID_TO_TOOL_ITEM[new_id] = color_item
            self.pseudo_color_items[new_id] = color_item

        new_id = wx.NewId()
        color_item = wx.MenuItem(submenu_wl, new_id, _('Custom'))
        submenu_pseudo_colours.AppendItem(color_item)
        self.ID_TO_TOOL_ITEM[new_id] = color_item
        self.pseudo_color_items[new_id] = color_item

        # --------------- Sub menu of the projection type ---------------------
        submenu_projection = wx.Menu()
        for name in PROJECTIONS_ID:
            new_id = wx.NewId()
            projection_item = wx.MenuItem(submenu_projection, new_id, name,
                                          kind=wx.ITEM_RADIO)
            submenu_projection.AppendItem(projection_item)
            self.ID_TO_TOOL_ITEM[new_id] = projection_item
        
        flag_tiling = False
        #------------ Sub menu of the image tiling ---------------
        submenu_image_tiling = wx.Menu()
        for name in sorted(const.IMAGE_TILING):
            new_id = wx.NewId()
            image_tiling_item = wx.MenuItem(submenu_image_tiling, new_id,\
                                name, kind=wx.ITEM_RADIO)
            submenu_image_tiling.AppendItem(image_tiling_item)
            self.ID_TO_TOOL_ITEM[new_id] = image_tiling_item
            
            #Save first id item
            if not(flag_tiling):
                self.id_tiling_first = new_id
                flag_tiling = True

        # Add sub itens in the menu
        self.AppendMenu(-1, _("Window width and level"), submenu_wl)
        self.AppendMenu(-1, _("Pseudo color"), submenu_pseudo_colours)
        self.AppendMenu(-1, _("Projection type"), submenu_projection)
        ###self.AppendMenu(-1, _("Image Tiling"), submenu_image_tiling)

        # It doesn't work in Linux
        self.Bind(wx.EVT_MENU, self.OnPopup)
        # In Linux the bind must be putted in the submenu
        if sys.platform == 'linux2' or sys.platform == 'darwin':
            submenu_wl.Bind(wx.EVT_MENU, self.OnPopup)
            submenu_pseudo_colours.Bind(wx.EVT_MENU, self.OnPopup)
            submenu_image_tiling.Bind(wx.EVT_MENU, self.OnPopup)
            submenu_projection.Bind(wx.EVT_MENU, self.OnPopup)

        self.__bind_events()

    def __bind_events(self):
        Publisher.subscribe(self.CheckWindowLevelOther, 'Check window and level other')
        Publisher.subscribe(self.FirstItemSelect, 'Select first item from slice menu')
        Publisher.subscribe(self._close, 'Close project data')
    
    def FirstItemSelect(self, pusub_evt):
        item = self.ID_TO_TOOL_ITEM[self.id_wl_first]
        item.Check(1)
        
        for i in self.pseudo_color_items:
            it = self.pseudo_color_items[i]
            if it.IsChecked():
                it.Toggle()
        item = self.ID_TO_TOOL_ITEM[self.id_pseudo_first]
        item.Check(1)
    
        item = self.ID_TO_TOOL_ITEM[self.id_tiling_first]
        item.Check(1)    
        
    def CheckWindowLevelOther(self, pubsub_evt):
        item = self.ID_TO_TOOL_ITEM[self.other_wl_id]
        item.Check()

    def OnPopup(self, evt):
        id = evt.GetId()
        item = self.ID_TO_TOOL_ITEM[evt.GetId()]
        key = item.GetLabel()
        print 'Key', key
        if(key in const.WINDOW_LEVEL.keys()):
            window, level = const.WINDOW_LEVEL[key]
            Publisher.sendMessage('Bright and contrast adjustment image',
                    (window, level))
            Publisher.sendMessage('Update window level value',\
               (window, level))
            Publisher.sendMessage('Update window and level text',\
                           "WL: %d  WW: %d"%(level, window))
            Publisher.sendMessage('Update slice viewer')

            #Necessary update the slice plane in the volume case exists
            Publisher.sendMessage('Render volume viewer')

        elif(key in const.SLICE_COLOR_TABLE.keys()):
            values = const.SLICE_COLOR_TABLE[key]
            Publisher.sendMessage('Change colour table from background image', values)
            Publisher.sendMessage('Update slice viewer')

            for i in self.pseudo_color_items:
                it = self.pseudo_color_items[i]
                if it.IsChecked():
                    it.Toggle()

            item.Toggle()
            self.HideClutDialog()
            self._gen_event = True


        elif key in self.plist_presets:
            values = presets.get_wwwl_preset_colours(self.plist_presets[key])
            Publisher.sendMessage('Change colour table from background image from plist', values)
            Publisher.sendMessage('Update slice viewer')

            for i in self.pseudo_color_items:
                it = self.pseudo_color_items[i]
                if it.IsChecked():
                    it.Toggle()

            item.Toggle()
            self.HideClutDialog()
            self._gen_event = True

        elif(key in const.IMAGE_TILING.keys()):
            values = const.IMAGE_TILING[key]
            Publisher.sendMessage('Set slice viewer layout', values)
            Publisher.sendMessage('Update slice viewer')

        elif key in PROJECTIONS_ID:
            print 'Key', key
            pid = PROJECTIONS_ID[key]
            Publisher.sendMessage('Set projection type', pid)
            Publisher.sendMessage('Reload actual slice')

        elif key == _('Custom'):
            if self.cdialog is None:
                slc = sl.Slice()
                histogram = slc.histogram
                init = slc.matrix.min()
                end = slc.matrix.max()
                nodes = slc.nodes
                self.cdialog = ClutImagedataDialog(histogram, init, end, nodes)
                self.cdialog.Show()
            else:
                self.cdialog.Show(self._gen_event)

            for i in self.pseudo_color_items:
                it = self.pseudo_color_items[i]
                if it.IsChecked():
                    it.Toggle()

            item.Toggle()
            self._gen_event = False

        evt.Skip()

    def HideClutDialog(self):
        if self.cdialog:
            self.cdialog.Hide()

    def _close(self, pubsub_evt):
        if self.cdialog:
            self.cdialog.Destroy()
            self.cdialog = None
