#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015 Davide Andreoli <dave@gurumeditation.it>
#
# This file is part of Eluminance.
#
# Eluminance is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3 of the License, or (at your option) any later version.
#
# Eluminance is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Eluminance. If not, see <http://www.gnu.org/licenses/>.

from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import re

from efl.evas import EXPAND_BOTH, EXPAND_HORIZ, FILL_BOTH, FILL_HORIZ, \
    EVAS_EVENT_FLAG_ON_HOLD
from efl.edje import Edje

from efl import elementary
from efl.elementary.background import Background
from efl.elementary.button import Button
from efl.elementary.box import Box
from efl.elementary.genlist import Genlist, GenlistItemClass, \
    ELM_GENLIST_ITEM_TREE
from efl.elementary.gengrid import Gengrid, GengridItemClass, \
    ELM_OBJECT_SELECT_MODE_ALWAYS
from efl.elementary.hoversel import Hoversel
from efl.elementary.icon import Icon
from efl.elementary.image import Image
from efl.elementary.label import Label
from efl.elementary.layout import Layout
from efl.elementary.menu import Menu
from efl.elementary.notify import Notify
from efl.elementary.photocam import Photocam, ELM_PHOTOCAM_ZOOM_MODE_AUTO_FIT, \
    ELM_PHOTOCAM_ZOOM_MODE_AUTO_FILL, ELM_PHOTOCAM_ZOOM_MODE_AUTO_FIT_IN, \
    ELM_PHOTOCAM_ZOOM_MODE_MANUAL
from efl.elementary.scroller import Scrollable, ELM_SCROLLER_POLICY_OFF
from efl.elementary.separator import Separator
from efl.elementary.slideshow import Slideshow, SlideshowItemClass
from efl.elementary.spinner import Spinner
from efl.elementary.thumb import Thumb, ETHUMB_THUMB_CROP
from efl.elementary.toolbar import Toolbar
from efl.elementary.window import StandardWindow


IMG_EXTS = ('.jpg','.jpeg','.png','.gif','.tiff','.bmp')

script_path = os.path.dirname(__file__)
install_prefix = script_path[0:script_path.find('/lib/python')]
data_path = os.path.join(install_prefix, 'share', 'eluminance')
THEME_FILE = os.path.join(data_path, 'themes', 'default.edj')

def _(string):
    return string

def clamp(low, val, high):
    if val < low: return low
    if val > high: return high
    return val

def file_hum_size(file_path):
    bytes = float(os.path.getsize(file_path))
    if bytes >= 1099511627776:
        terabytes = bytes / 1099511627776
        size = '%.1fT' % terabytes
    elif bytes >= 1073741824:
        gigabytes = bytes / 1073741824
        size = '%.1fG' % gigabytes
    elif bytes >= 1048576:
        megabytes = bytes / 1048576
        size = '%.1fM' % megabytes
    elif bytes >= 1024:
        kilobytes = bytes / 1024
        size = '%.1fK' % kilobytes
    else:
        size = '%.1fb' % bytes
    return size

def natural_sort(l): 
   convert = lambda text: int(text) if text.isdigit() else text.lower() 
   alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)] 
   return sorted(l, key=alphanum_key)


class StdButton(Button):
    """ A Button with a standard fdo icon """
    def __init__(self, parent, icon, *args, **kargs):
        Button.__init__(self, parent, *args, **kargs)
        self.icon = icon
        self.show()

    @property
    def icon(self):
        return self.content

    @icon.setter
    def icon(self, name):
        self.content = Icon(self, standard=name, resizable=(False, False))


class TreeView(Genlist):
    def __init__(self, parent, select_cb):
        self._select_cb = select_cb
        Genlist.__init__(self, parent, size_hint_expand=EXPAND_BOTH,
                         size_hint_fill=FILL_BOTH)
        self.callback_selected_add(self._item_selected_cb)
        self.callback_expand_request_add(self._item_expand_request_cb)
        self.callback_expanded_add(self._item_expanded_cb)
        self.callback_contract_request_add(self._item_contract_request_cb)
        self.callback_contracted_add(self._item_contracted_cb)
        self.callback_clicked_double_add(self._item_expand_request_cb)
        self.show()
        self.itc = GenlistItemClass('one_icon',
                                    text_get_func=self._gl_text_get,
                                    content_get_func=self._gl_content_get)

    def _gl_text_get(self, gl, part, item_data):
        return os.path.basename(item_data)

    def _gl_content_get(self, gl, part, item_data):
        return Icon(gl, standard='folder')

    def _item_selected_cb(self, gl, item):
        self._select_cb(item.data)

    def _item_expand_request_cb(self, gl, item):
        item.expanded = True

    def _item_expanded_cb(self, gl, item):
        self.populate(item.data, item)

    def _item_contract_request_cb(self, gl, item):
        item.expanded = False

    def _item_contracted_cb(self, gl, item):
        item.subitems_clear()

    def populate(self, path, parent=None):
        for f in natural_sort(os.listdir(path)):
            if f[0] == '.': continue
            fullpath = os.path.join(path, f)
            if os.path.isdir(fullpath):
                self.item_append(self.itc, fullpath, parent,
                                 flags=ELM_GENLIST_ITEM_TREE)

    def expand_to_folder(self, path):
        if os.path.isfile(path):
            path = os.path.dirname(path)
        it = self.first_item
        while it:
            if it.data == path:
                self.populate(it.data, it)
                it.expanded = True
                it.selected = True
                it.show()
                return
            if path.startswith(it.data + os.path.sep):
                self.populate(it.data, it)
                it.expanded = True
                it = it.subitems_get()[0]
            else:
                it = it.next


class PhotoGrid(Gengrid):
    def __init__(self, parent, select_cb):
        self._select_cb = select_cb

        Gengrid.__init__(self, parent, select_mode=ELM_OBJECT_SELECT_MODE_ALWAYS,
                         item_size=(128, 128), align=(0.5, 0.0))
        self.callback_selected_add(self._item_selected_cb)

        self.itc = GengridItemClass('default',
                                    text_get_func=self._gg_text_get,
                                    content_get_func=self._gg_content_get)

    def _gg_content_get(self, gg, part, item_data):
        if part == 'elm.swallow.icon':
            return Thumb(gg, style="noframe", aspect=ETHUMB_THUMB_CROP,
                         file=item_data)

    def _gg_text_get(self, gg, part, item_data):
        return os.path.basename(item_data)

    def _item_selected_cb(self, gg, item):
        self._select_cb(item.data)

    def populate(self, path):
        self.clear()
        for f in natural_sort(os.listdir(path)):
            if os.path.splitext(f)[-1].lower() in IMG_EXTS:
                self.item_append(self.itc, os.path.join(path, f))
        if self.first_item:
            self.first_item.selected = True
            self.first_item.show()

    def next_select(self):
        it = self.selected_item or self.first_item
        if it: it = it.next
        if it: it.selected = True

    def prev_select(self):
        it = self.selected_item or self.last_item
        if it: it = it.prev
        if it: it.selected = True

    def file_select(self, path):
        it = self.first_item
        while it:
            if it.data == path:
                it.selected = True
                it.show()
                return
            it = it.next


class ScrollablePhotocam(Photocam, Scrollable):
    ZOOMS = [0.05, 0.07, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5,
             2.0, 3.0, 5.0, 7.5, 10, 15, 20, 30, 50, 75, 100]
    def __init__(self, parent, changed_cb):
        self._changed_cb = changed_cb
        Photocam.__init__(self, parent, paused=True,
                          zoom_mode=ELM_PHOTOCAM_ZOOM_MODE_AUTO_FIT)
        self.policy = ELM_SCROLLER_POLICY_OFF, ELM_SCROLLER_POLICY_OFF
        self.callback_zoom_change_add(self._zoom_change_cb)
        self.on_mouse_wheel_add(self._on_mouse_wheel)
        self.on_mouse_down_add(self._on_mouse_down)
        self.on_mouse_up_add(self._on_mouse_up)
        self.on_del_add(self._on_del)
        self._drag_start_geom = None
        self.sel = None

    def zoom_in(self):
        new = self.zoom ** -1
        for z in self.ZOOMS:
            if new < z: break
        self.zoom_set(z ** -1)

    def zoom_out(self):
        new = self.zoom ** -1
        for z in reversed(self.ZOOMS):
            if new > z: break
        self.zoom_set(z ** -1)

    def zoom_fit(self):
        self.zoom_mode = ELM_PHOTOCAM_ZOOM_MODE_AUTO_FIT

    def zoom_fill(self):
        self.zoom_mode = ELM_PHOTOCAM_ZOOM_MODE_AUTO_FILL

    def zoom_set(self, val):
        self.zoom_mode = ELM_PHOTOCAM_ZOOM_MODE_MANUAL
        self.zoom = clamp(self.ZOOMS[-1] ** -1, val, self.ZOOMS[0] ** -1)
        self._zoom_change_cb(self)
        
    def _on_del(self, obj):
        if self.sel: self.sel.delete()

    # mouse wheel: zoom
    def _on_mouse_wheel(self, obj, event):
        event.event_flags |= EVAS_EVENT_FLAG_ON_HOLD
        new = self.zoom * (1.1 if event.z == 1 else 0.9)
        self.zoom_set(new)

    def _zoom_change_cb(self, obj):
        self._changed_cb((self.zoom ** -1) * 100)

    # mouse drag: pan
    def _on_mouse_down(self, obj, event):
        self._drag_start_region = obj.region
        self._drag_start_x, self._drag_start_y = event.position.canvas
        obj.on_mouse_move_add(self._on_mouse_move)

    def _on_mouse_up(self, obj, event):
        obj.on_mouse_move_del(self._on_mouse_move)

    def _on_mouse_move(self, obj, event):
        if self._drag_start_geom is None:
            x, y = event.position.canvas
            dx, dy = self._drag_start_x - x, self._drag_start_y - y
            x, y, w, h = self._drag_start_region
            obj.region_show(x + dx, y + dy, w, h)

    # region selector stuff
    def region_selector_show(self):
        self.sel = Edje(self.evas, file=THEME_FILE, group='sel')
        self.sel.show()

        internal = self.internal_image
        internal.on_move_add(self._internal_on_move_resize)
        internal.on_resize_add(self._internal_on_move_resize)
        self._internal_on_move_resize(internal)

        for part in ('h1','h2','h3','h4','h5','h6','h7','h8','hm'):
            h = self.sel.part_object_get(part)
            h.on_mouse_down_add(self._on_handler_mouse_down, part)
            h.on_mouse_up_add(self._on_handler_mouse_up, part)

    def _internal_on_move_resize(self, obj):
        self.sel.geometry = obj.geometry

    def _on_handler_mouse_down(self, obj, event, part):
        self._drag_start_x, self._drag_start_y = event.position.canvas
        self._drag_start_geom = self.sel.part_object_get('selector').geometry
        obj.on_mouse_move_add(self._on_handler_mouse_move, part)

    def _on_handler_mouse_up(self, obj, event, part):
        obj.on_mouse_move_del(self._on_handler_mouse_move)
        self._drag_start_geom = None

    def _on_handler_mouse_move(self, obj, event, part):
        x, y = event.position.canvas
        dx, dy = x - self._drag_start_x, y - self._drag_start_y
        x, y, w, h = self._drag_start_geom
        px, py, pw, ph = self.internal_image.geometry

        # calc new selection gemetry
        if part == 'hm':
            x, y = x + dx, y + dy
        elif part == 'h1':
            x, y = x + dx, y + dy
            w, h = w - dx, h - dy
        elif part == 'h2':
            y = y + dy
            h = h - dy
        elif part == 'h3':
            y = y + dy
            w, h = w + dx, h - dy
        elif part == 'h4':
            w = w + dx
        elif part == 'h5':
            w, h = w + dx, h + dy
        elif part == 'h6':
            h = h + dy
        elif part == 'h7':
            x, y = x + dx, y
            w, h = w - dx, h + dy
        elif part == 'h8':
            x = x + dx
            w = w - dx

        w, h = max(50, w), max(50, h)

        # calc new relative pos
        rel1x = float(x - px) / pw
        rel1y = float(y - py) / ph
        rel2x = float(x + w - px) / pw
        rel2y = float(y + h - py) / ph

        # constrain inside photo geometry
        rel1x = clamp(0.0, rel1x, 1.0)
        rel1y = clamp(0.0, rel1y, 1.0)
        rel2x = clamp(0.0, rel2x, 1.0)
        rel2y = clamp(0.0, rel2y, 1.0)

        # send signal to edje with new rels
        self.sel.message_send(1, (rel1x, rel1y, rel2x, rel2y))


class StatusBar(Box):
    def __init__(self, parent):
        Box.__init__(self, parent, horizontal=True,
                     size_hint_expand=EXPAND_HORIZ, size_hint_fill=FILL_HORIZ)

        self.lb_name = Label(self, ellipsis=True,
                    size_hint_expand=EXPAND_HORIZ, size_hint_fill=FILL_HORIZ,
                    text='<align=left>{}</align>'.format(_('No image selected')))
        self.pack_end(self.lb_name)
        self.lb_name.show()
        
        self.lb_info = Label(self)
        self.pack_end(self.lb_info)
        self.lb_info.show()

        # edit button
        # bt = StdButton(self, icon='edit')
        # bt.callback_clicked_add(lambda b: ImageEditor(self.app))
        # self.pack_end(bt)
        # self.btn_edit = bt

    def update(self, img_path, img_size, zoom):
        self.lb_name.text = '<align=left><b>{0}:</b> {1}</align>'.format(
                                _('File'), os.path.basename(img_path))
        self.lb_info.text = \
            '<b>{}:</b> {}x{}    <b>{}:</b> {}    <b>{}:</b> {:.0f}%'.format(
                _('Resolution'), img_size[0], img_size[1],
                _('Size'), file_hum_size(img_path),
                _('Zoom'), zoom)


class Controls(Box):
    def __init__(self, parent, action_cb):
        Box.__init__(self, parent, horizontal=True)

        # zoom orig
        bt = StdButton(self, icon='zoom-original')
        bt.callback_clicked_add(lambda b: action_cb('zoomorig'))
        bt.tooltip_text_set(_("Zoom 1:1"))
        self.pack_end(bt)

        # zoom in
        bt = StdButton(self, icon='zoom-in')
        bt.callback_clicked_add(lambda b: action_cb('zoomin'))
        bt.tooltip_text_set(_("Zoom in"))
        self.pack_end(bt)

        # zoom out
        bt = StdButton(self, icon='zoom-out')
        bt.callback_clicked_add(lambda b: action_cb('zoomout'))
        bt.tooltip_text_set(_("Zoom out"))
        self.pack_end(bt)

        # zoom fit
        bt = StdButton(self, icon='zoom-fit-best')
        bt.callback_clicked_add(lambda b: action_cb('zoomfit'))
        bt.tooltip_text_set(_("Zoom fit"))
        self.pack_end(bt)

        # zoom fill
        bt = StdButton(self, icon='zoom-fit-best')
        bt.callback_clicked_add(lambda b: action_cb('zoomfill'))
        bt.tooltip_text_set(_("Zoom fill"))
        self.pack_end(bt)

        sep = Separator(self)
        self.pack_end(sep)
        
        # prev button
        bt = StdButton(self, icon='go-previous')
        bt.callback_clicked_add(lambda b: action_cb('prev'))
        bt.tooltip_text_set(_("Previous photo"))
        self.pack_end(bt)
        self.btn_prev = bt

        # next button
        bt = StdButton(self, icon='go-next')
        bt.callback_clicked_add(lambda b:action_cb('next'))
        bt.tooltip_text_set(_("Next photo"))
        self.pack_end(bt)
        self.btn_next = bt

        # slideshow play button
        bt = StdButton(self, icon='media-playback-start')
        bt.callback_clicked_add(lambda b: action_cb('slideshow'))
        bt.tooltip_text_set(_("Slideshow"))
        self.pack_end(bt)
        self.btn_play = bt

        self.show()

    def update(self, items_count):
        if items_count > 1:
            self.btn_next.disabled = False
            self.btn_prev.disabled = False
            self.btn_play.disabled = False
        else:
            self.btn_next.disabled = True
            self.btn_prev.disabled = True
            self.btn_play.disabled = True


class SlideShow(Slideshow):
    NOTIFY_TIMEOUT = 3.0
    def __init__(self, app):
        Slideshow.__init__(self, app.win, timeout=5.0,
                           size_hint_expand=EXPAND_BOTH)
        app.win.resize_object_add(self)
        self.show()

        itc = SlideshowItemClass(self._item_get_func)
        grid_item = app.grid.first_item
        while grid_item:
            self.item_add(itc, grid_item.data)
            grid_item = grid_item.next

        box = Box(self, horizontal=True)

        notify = Notify(self, align=(0.5, 1.0), content=box,
                        timeout=self.NOTIFY_TIMEOUT,
                        size_hint_expand=EXPAND_BOTH)
        notify.on_mouse_in_add(self._notify_mouse_in_cb)
        notify.on_mouse_out_add(self._notify_mouse_out_cb)
        self.on_mouse_move_add(self._sshow_mouse_move_cb, notify)

        bt = StdButton(box, icon='go-previous')
        bt.callback_clicked_add(lambda b: self.previous())
        box.pack_end(bt)

        bt = StdButton(box, icon='go-next')
        bt.callback_clicked_add(lambda b: self.next())
        box.pack_end(bt)

        hv = Hoversel(box, hover_parent=app.win, text=self.transitions[0])
        for t in list(self.transitions) + [None]:
            hv.item_add(t or "None", None, 0, self._transition_cb, t)
        box.pack_end(hv)
        hv.show()

        spinner = Spinner(box, label_format="%2.0f secs.", step=1,
                          min_max=(3, 60), value=3)
        spinner.callback_changed_add(lambda s: setattr(self, 'timeout', s.value))
        box.pack_end(spinner)
        spinner.show()

        bt = StdButton(box, icon='media-playback-pause', text='Pause')
        bt.callback_clicked_add(self._play_pause_cb)
        box.pack_end(bt)

        bt = StdButton(box, icon='close', text='Close')
        bt.callback_clicked_add(lambda b: self.delete())
        box.pack_end(bt)

    def _item_get_func(self, obj, file_path):
        return Image(obj, file=file_path)

    def _sshow_mouse_move_cb(self, obj, event, notify):
        notify.timeout = self.NOTIFY_TIMEOUT
        notify.show()

    def _notify_mouse_in_cb(self, notify, event):
        notify.timeout = 0.0
        notify.show()

    def _notify_mouse_out_cb(self, notify, event):
        notify.timeout = self.NOTIFY_TIMEOUT

    def _transition_cb(self, hoversel, item, transition):
        self.transition = transition
        hoversel.text = transition or "None"

    def _play_pause_cb(self, btn):
        if self.timeout == 0:
            self.timeout = 3 # TODO FIXME
            btn.text = 'Pause'
            btn.icon = 'media-playback-pause'
        else:
            self.timeout = 0
            btn.text = 'Play'
            btn.icon = 'media-playback-start'


class ImageEditor(object):
    def __init__(self, app):
        self.bg = Background(app.win, size_hint_expand=EXPAND_BOTH)
        app.win.resize_object_add(self.bg)
        self.bg.show()

        box = Box(self.bg, size_hint_expand=EXPAND_BOTH,
                  size_hint_fill=FILL_BOTH)
        app.win.resize_object_add(box)
        box.show()

        tb = Toolbar(app.win, homogeneous=True, menu_parent=app.win,
                     size_hint_expand=EXPAND_HORIZ,
                     size_hint_fill=FILL_HORIZ)

        item = tb.item_append('rotate', 'Rotate')
        item.menu = True
        item.menu.item_add(None, 'Rotate Right', 'object-rotate-right')
        item.menu.item_add(None, 'Rotate Left', 'object-rotate-left')
        item.menu.item_add(None, 'Mirror', 'object-flip-horizontal')
        item.menu.item_add(None, 'Flip', 'object-flip-vertical')

        tb.item_append('edit-cut', 'Crop', self._crop_item_cb)
        tb.item_append('resize', 'Resize')

        sep = tb.item_append(None, None)
        sep.separator = True

        tb.item_append('document-save', 'Save')
        tb.item_append('document-save-as', 'Save as')
        tb.item_append('document-close', 'Close', self._close_item_cb)

        box.pack_end(tb)
        tb.show()

        self.photo = ScrollablePhotocam(app, box, file=app.photo.file,
                                        size_hint_expand=EXPAND_BOTH,
                                        size_hint_fill=FILL_BOTH)
        box.pack_end(self.photo)
        self.photo.show()

    def _crop_item_cb(self, tb, item):
        self.photo.region_selector_show()

    def _close_item_cb(self, tb, item):
        self.bg.delete()


class MainWin(StandardWindow):
    def __init__(self):
        StandardWindow.__init__(self, 'eluminance', 'Eluminance',
                                autodel=True, size=(800,600))
        self.callback_delete_request_add(lambda o: elementary.exit())

        self.layout = Layout(self, file=(THEME_FILE, 'eluminance/main'),
                             size_hint_expand=EXPAND_BOTH)
        self.resize_object_add(self.layout)
        self.layout.show()

    def swallow_all(self, app):
        self.layout.content_set('photo.swallow', app.photo)
        self.layout.content_set('controls.swallow', app.controls)
        self.layout.content_set('grid.swallow', app.grid)
        self.layout.content_set('tree.swallow', app.tree)
        self.layout.content_set('status.swallow', app.status)


class EluminanceApp(object):
    def __init__(self):

        self.win = MainWin()
        self.photo = ScrollablePhotocam(self.win, self.photo_changed)
        self.controls = Controls(self.win, self.controls_action)
        self.grid = PhotoGrid(self.win, self.grid_selected)
        self.tree = TreeView(self.win, self.tree_selected)
        self.status = StatusBar(self.win)
        self.win.swallow_all(self)

        self.current_path = os.path.expanduser('~')
        self.current_file = None
        self.tree.populate(self.current_path)

        if len(sys.argv) > 1:
            path = os.path.abspath(sys.argv[1])
            if os.path.exists(path):
                self.tree.expand_to_folder(path)
                if os.path.isfile(path):
                    self.grid.file_select(path)
        else:
            self.grid.populate(self.current_path)

        self.win.show()

    def tree_selected(self, path):
        self.current_path = path
        self.grid.populate(path)

    def grid_selected(self, path):
        self.current_file = path
        self.photo.file_set(path)
        self.photo.zoom_fit()

    def photo_changed(self, zoom):
        self.win.title = 'eluminance - ' + self.current_path
        self.status.update(self.current_file, self.photo.image_size, zoom)
        self.controls.update(self.grid.items_count)

    def controls_action(self, action):
        if action == 'next':
            self.grid.next_select()
        elif action == 'prev':
            self.grid.prev_select()
        elif action == 'slideshow':
            SlideShow(self)
        elif action == 'zoomin':
            self.photo.zoom_in()
        elif action == 'zoomout':
            self.photo.zoom_out()
        elif action == 'zoomfit':
            self.photo.zoom_fit()
        elif action == 'zoomfill':
            self.photo.zoom_fill()
        elif action == 'zoomorig':
            self.photo.zoom_set(1.0)


def main():
    elementary.init()
    elementary.need_ethumb()
    elementary.theme.theme_extension_add(THEME_FILE)
    EluminanceApp()
    elementary.run()
    elementary.shutdown()

if __name__ == '__main__':
    sys.exit(main())
