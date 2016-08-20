#!/usr/bin/env python
# encoding: utf-8

# Copyright (C) 2015-2016 Davide Andreoli <dave@gurumeditation.it>
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

from __future__ import absolute_import, print_function

import os
import sys
import pickle
import gettext
from xdg.BaseDirectory import xdg_config_home

from efl import edje
from efl import elementary as elm
from efl.evas import EXPAND_BOTH, EXPAND_HORIZ, EXPAND_VERT, \
                     FILL_BOTH, FILL_HORIZ, FILL_VERT

import eluminance.utils as utils

__version__ = '0.9'

IMG_EXTS = ('.jpg','.jpeg','.png','.gif','.tiff','.bmp')

script_path = os.path.dirname(__file__)
install_prefix = script_path[0:script_path.find('/lib/python')]
data_path = os.path.join(install_prefix, 'share', 'eluminance')
config_file = os.path.join(xdg_config_home, 'eluminance', 'config.pickle')
THEME_FILE = os.path.join(data_path, 'themes', 'default.edj')

# install the _() and ngettext() functions in the main namespace
locale_dir = os.path.join(install_prefix, 'share', 'locale')
gettext.install('eluminance', names='ngettext', localedir=locale_dir)


class Options(object):
    """ Class for persistent application settings """
    def __init__(self):
        self.sshow_timeout = 5.0
        self.sshow_transition = 'fade_fast'
        self.sshow_loop = True
        self.favorites = []

    def load(self):
        try:
            # load only attributes (not methods) from the instance saved to disk
            saved = pickle.load(open(config_file, 'rb'))
            for attr in dir(self):
                if attr[0] != '_' and not callable(getattr(self, attr)):
                    if hasattr(saved, attr):
                        setattr(self, attr, getattr(saved, attr))
        except:
            pass

    def save(self):
        # create config folder if needed
        config_path = os.path.dirname(config_file)
        if not os.path.exists(config_path):
            os.makedirs(config_path)
        # save this whole class instance to file
        with open(config_file, 'wb') as f:
            pickle.dump(self, f, pickle.HIGHEST_PROTOCOL)

app = None
options = Options()


class StdButton(elm.Button):
    """ A Button with a standard fdo icon """
    def __init__(self, parent, icon, *args, **kargs):
        elm.Button.__init__(self, parent, *args, **kargs)
        self.icon = icon
        self.show()

    @property
    def icon(self):
        return self.content

    @icon.setter
    def icon(self, name):
        self.content = utils.SafeIcon(self, name, size_hint_min=(18,18))


class TreeView(elm.Table):
    def __init__(self, parent, select_cb):
        self._select_cb = select_cb

        elm.Table.__init__(self, parent, size_hint_expand=EXPAND_BOTH,
                           size_hint_fill=FILL_BOTH)

        bg = elm.Background(self, size_hint_expand=EXPAND_BOTH, 
                        size_hint_fill=FILL_BOTH)
        self.pack(bg, 0, 0, 1, 2)
        bg.show()

        self.sc = elm.SegmentControl(self)
        it = self.sc.item_add(None, 'Home') # TODO: translate
        it.data['path'] = os.path.expanduser('~')
        it = self.sc.item_add(None, 'Root')
        it.data['path'] = '/'
        it = self.sc.item_add(None, 'Favs')
        it.data['path'] = 'favs'
        self.sc.callback_changed_add(self._segment_changed_cb)
        pad = elm.Frame(self, style='pad_small', content=self.sc, 
                        size_hint_expand=EXPAND_HORIZ)
        self.pack(pad, 0, 0, 1, 1)
        pad.show()
        
        self.itc = elm.GenlistItemClass('one_icon',
                                        text_get_func=self._gl_text_get,
                                        content_get_func=self._gl_content_get)
        self.li = elm.Genlist(self, size_hint_expand=EXPAND_BOTH,
                                    size_hint_fill=FILL_BOTH)
        self.li.callback_selected_add(self._item_selected_cb)
        self.li.callback_expand_request_add(self._item_expand_request_cb)
        self.li.callback_expanded_add(self._item_expanded_cb)
        self.li.callback_contract_request_add(self._item_contract_request_cb)
        self.li.callback_contracted_add(self._item_contracted_cb)
        self.li.callback_clicked_double_add(self._item_expand_request_cb)
        self.li.callback_clicked_right_add(self._item_clicked_right_cb)
        self.li.callback_longpressed_add(self._item_clicked_right_cb)
        self.pack(self.li, 0, 1, 1, 1)
        self.li.show()

    def _gl_text_get(self, gl, part, item_data):
        if item_data is None: return _('No items to show')
        return os.path.basename(item_data)

    def _gl_content_get(self, gl, part, item_data):
        if item_data is not None:
            icon = 'starred' if item_data in options.favorites else 'folder'
            return utils.SafeIcon(gl, icon, resizable=(False,False))

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

    def _item_clicked_right_cb(self, gl, item):
        if item.disabled: return
        item.selected = True
        app.win.freeze()

        pop = elm.Ctxpopup(app.win, direction_priority=(
                elm.ELM_CTXPOPUP_DIRECTION_RIGHT, elm.ELM_CTXPOPUP_DIRECTION_DOWN,
                elm.ELM_CTXPOPUP_DIRECTION_LEFT, elm.ELM_CTXPOPUP_DIRECTION_UP))
        pop.callback_dismissed_add(self._popup_dismissed_cb)
        pop.item_append(_('Set as root'), None, 
                        self._popup_set_root_cb, item.data)
        if item.data in options.favorites:
            label = _('Remove from favorites')
            icon = utils.SafeIcon(pop, 'bookmark-remove')
        else:
            label = _('Add to favorites')
            icon = utils.SafeIcon(pop, 'bookmark-add')
        pop.item_append(label, icon, self._popup_toggle_fav_cb, item.data)
        
        x, y = self.evas.pointer_canvas_xy_get()
        pop.move(x, y)
        pop.show()

    def _popup_set_root_cb(self, pop, item, path):
        self.set_root(path)
        pop.dismiss()
    
    def _popup_toggle_fav_cb(self, pop, item, path):
        if path in options.favorites:
            options.favorites.remove(path)
        else:
            options.favorites.append(path)
        pop.dismiss()

    def _popup_dismissed_cb(self, pop):
        app.win.unfreeze()
        pop.delete()

    def _segment_changed_cb(self, sc, item):
        self.set_root(item.data['path'], update_sc=False)

    def set_root(self, path, update_sc=True):
        if update_sc:
            for idx in range(self.sc.item_count):
                it = self.sc.item_get(idx)
                if it.data['path'] == path:
                    it.selected = True
                    return
            if self.sc.item_selected is not None:
                self.sc.item_selected.selected = False

        self.li.clear()
        self.populate(path)
    
    def populate(self, path, parent=None):
        it = None
        if path == 'favs':
            for path in utils.natural_sort(options.favorites):
                it = self.li.item_append(self.itc, path, parent,
                                         flags=elm.ELM_GENLIST_ITEM_TREE)
        else:
            for f in utils.natural_sort(os.listdir(path)):
                if f[0] == '.': continue
                fullpath = os.path.join(path, f)
                if os.path.isdir(fullpath):
                    it = self.li.item_append(self.itc, fullpath, parent,
                                             flags=elm.ELM_GENLIST_ITEM_TREE)
        if it is None:
            it = self.li.item_append(self.itc, None, parent)
            it.disabled = True

    def expand_to_folder(self, path):
        if os.path.isfile(path):
            path = os.path.dirname(path)
        it = self.li.first_item
        while it:
            if it.data == path:
                it.expanded = True
                it.selected = True
                it.show()
                return
            if path.startswith(it.data + os.path.sep):
                it.expanded = True
                it = it.subitems_get()[0]
            else:
                it = it.next


class PhotoGrid(elm.Gengrid):
    def __init__(self, parent, select_cb):
        self._select_cb = select_cb
        self.itc = elm.GengridItemClass('default',
                                        text_get_func=self._gg_text_get,
                                        content_get_func=self._gg_content_get)
        elm.Gengrid.__init__(self, parent,
                             item_size=(128, 128), align=(0.5, 0.0),
                             select_mode=elm.ELM_OBJECT_SELECT_MODE_ALWAYS)
        self.callback_selected_add(self._item_selected_cb)
        self.drag_item_container_add(0.2, 0.0,
                                     self._drag_item_get,
                                     self._drag_item_data_get)
    
    def _drag_item_get(self, obj, x, y):
        return self.at_xy_item_get(x, y)

    def _drag_item_data_get(self, obj, item, info):
        info.format = elm.ELM_SEL_FORMAT_TARGETS
        info.createicon = self._drag_create_icon
        info.createdata = item
        info.dragdone = self._drag_done
        info.donecbdata = item
        info.data = 'file://' + item.data
        return True

    def _drag_create_icon(self, win, xoff, yoff, item):
        item.cursor = 'fleur'
        ic = elm.Photo(win, file=item.data, aspect_fixed=True,
                       fill_inside=False, size=100)
        mx, my = self.evas.pointer_canvas_xy
        return (ic, mx - 60, my - 60)

    def _drag_done(self, obj, accepted, item):
        item.cursor = None

    def _gg_content_get(self, gg, part, item_data):
        if part == 'elm.swallow.icon':
            return elm.Thumb(gg, style='noframe', aspect=elm.ETHUMB_THUMB_CROP,
                             file=item_data)

    def _gg_text_get(self, gg, part, item_data):
        return os.path.basename(item_data)

    def _item_selected_cb(self, gg, item):
        self._select_cb(item.data, item.index - 1)

    def photo_add(self, path):
        self.item_append(self.itc, path)

    def file_select(self, path):
        if self.selected_item and self.selected_item.data == path:
            return
        it = self.first_item
        while it:
            if it.data == path:
                it.selected = True
                it.show() # XXX this is quite annoying if you are browsing the grid
                return
            it = it.next


class ScrollablePhoto(elm.Scroller):
    ZOOMS = [5, 7, 10, 15, 20, 30, 50, 75, 100, 150, 200, 300,
             500, 750, 1000, 1500, 2000, 3000, 5000, 7500, 10000]
    def __init__(self, parent, zoom_changed_cb):
        self._zoom_changed_cb = zoom_changed_cb
        self._zoom_mode = None # 'fill' or 'fit' on resize
        self.image_size = 0, 0 # original image pixel size

        elm.Scroller.__init__(self, parent, style="trans",
                policy=(elm.ELM_SCROLLER_POLICY_OFF, elm.ELM_SCROLLER_POLICY_OFF),
                movement_block=elm.ELM_SCROLLER_MOVEMENT_BLOCK_VERTICAL |
                               elm.ELM_SCROLLER_MOVEMENT_BLOCK_HORIZONTAL)
        self.on_mouse_wheel_add(self._on_mouse_wheel)
        self.on_mouse_down_add(self._on_mouse_down)
        self.on_mouse_up_add(self._on_mouse_up)
        self.on_resize_add(self._on_resize)

        self.img = elm.Image(self, preload_disabled=False)
        self.img.show()

        # table help to keep the image centered in the scroller
        tb = elm.Table(self, size_hint_expand=EXPAND_BOTH,
                             size_hint_fill=FILL_BOTH)
        tb.pack(self.img, 0, 0, 1, 1)
        self.content = tb

    def file_set(self, file):
        self.img.file_set(file)
        self.image_size = self.img.object_size
        if self.img.animated_available:
            self.img.animated = True
            self.img.animated_play = True

    def zoom_set(self, val):
        self._zoom_mode = None
        if val == 'fit' or val == 'fill':
            self._zoom_mode = val
            self._on_resize(self)
        elif val == '1:1':
            self.zoom = 100
        elif val == 'in':
            cur = self.zoom + 1
            for z in self.ZOOMS:
                if cur < z: break
            self.zoom_centered(z)
        elif val == 'out':
            cur = self.zoom - 1
            for z in reversed(self.ZOOMS):
                if cur > z: break
            self.zoom_centered(z)

    @property
    def zoom(self):
        return (float(self.img.size[0]) / float(self.image_size[0])) * 100

    @zoom.setter
    def zoom(self, val):
        z = utils.clamp(self.ZOOMS[0], val, self.ZOOMS[-1]) / 100.0
        w, h = self.image_size[0] * z, self.image_size[1] * z
        self.img.size_hint_min = w, h
        self.img.size_hint_max = w, h
        self._zoom_changed_cb(z * 100)

    def zoom_centered(self, val, center_on_mouse=False):
        iw, ih = self.img.size
        if ih > 0 and ih > 0:
            rx, ry, rw, rh = self.region
            cx, cy = self.evas.pointer_canvas_xy if center_on_mouse else \
                     (rw / 2, rh / 2)
            dy, dx = float(cy + ry) / ih, float(cx + rx) / iw

        self.zoom = val
        if ih > 0 and ih > 0:
            w, h = self.img.size_hint_min
            rx, ry = int(w * dx) - cx, int(h * dy) - cy
            self.region_show(rx, ry, rw, rh)
    
    # mouse wheel: zoom
    def _on_mouse_wheel(self, obj, event):
        self._zoom_mode = None
        val = self.zoom * (0.9 if event.z == 1 else 1.1)
        self.zoom_centered(val, center_on_mouse=True)

    # mouse drag: pan
    def _on_mouse_down(self, obj, event):
        if event.button in (1, 2):
            self._drag_start_region = obj.region
            self._drag_start_x, self._drag_start_y = event.position.canvas
            obj.on_mouse_move_add(self._on_mouse_move)
            obj.cursor = 'fleur'

    def _on_mouse_up(self, obj, event):
        if event.button in (1, 2):
            obj.on_mouse_move_del(self._on_mouse_move)
            obj.cursor = None

    def _on_mouse_move(self, obj, event):
        x, y = event.position.canvas
        dx, dy = self._drag_start_x - x, self._drag_start_y - y
        x, y, w, h = self._drag_start_region
        obj.region_show(x + dx, y + dy, w, h)

    # scroller resize: keep the image fitted or filled
    def _on_resize(self, obj):
        if self._zoom_mode is not None:
            cw, ch = self.region[2], self.region[3]
            iw, ih = self.image_size
            if cw > 0 and ch > 0 and iw > 0 and ih > 0:
                zx, zy = float(cw) / float(iw), float(ch) / float(ih)
                z = min(zx, zy) if self._zoom_mode == 'fit' else max(zx, zy)
                self.zoom_centered(z * 100)


class ScrollablePhotocam(elm.Photocam, elm.Scrollable):
    ZOOMS = [0.05, 0.07, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5,
             2.0, 3.0, 5.0, 7.5, 10, 15, 20, 30, 50, 75, 100]
    def __init__(self, parent, changed_cb):
        self._changed_cb = changed_cb
        elm.Photocam.__init__(self, parent, paused=True,
                              zoom_mode=elm.ELM_PHOTOCAM_ZOOM_MODE_AUTO_FIT)
        self.policy = elm.ELM_SCROLLER_POLICY_OFF, elm.ELM_SCROLLER_POLICY_OFF
        self.callback_zoom_change_add(self._zoom_change_cb)
        self.on_mouse_wheel_add(self._on_mouse_wheel)
        self.on_mouse_down_add(self._on_mouse_down)
        self.on_mouse_up_add(self._on_mouse_up)
        # self.on_del_add(self._on_del) # UNUSED region selector
        # self._drag_start_geom = None  # UNUSED region selector
        # self.sel = None               # UNUSED region selector

    def zoom_set(self, val):
        if isinstance(val, float):
            self.zoom_mode = elm.ELM_PHOTOCAM_ZOOM_MODE_MANUAL
            self.zoom = utils.clamp(self.ZOOMS[-1] ** -1, val, self.ZOOMS[0] ** -1)
            self._zoom_change_cb(self)
        elif val == '1:1':
            self.zoom_set(1.0)
        elif val == 'fill':
            self.zoom_mode = elm.ELM_PHOTOCAM_ZOOM_MODE_AUTO_FILL
        elif val == 'fit':
            self.zoom_mode = elm.ELM_PHOTOCAM_ZOOM_MODE_AUTO_FIT
        elif val == 'in':
            old = self.zoom ** -1
            for z in self.ZOOMS:
                if old < z: break
            self.zoom_set(z ** -1)
        elif val == 'out':
            old = self.zoom ** -1
            for z in reversed(self.ZOOMS):
                if old > z: break
            self.zoom_set(z ** -1)

    # def _on_del(self, obj): # UNUSED region selector
        # if self.sel: self.sel.delete()

    # mouse wheel: zoom
    def _on_mouse_wheel(self, obj, event):
        new = self.zoom * (1.1 if event.z == 1 else 0.9)
        self.zoom_set(new)

    def _zoom_change_cb(self, obj):
        self._changed_cb((self.zoom ** -1) * 100)

    # mouse drag: pan
    def _on_mouse_down(self, obj, event):
        if event.button in (1, 2):
            self._drag_start_region = obj.region
            self._drag_start_x, self._drag_start_y = event.position.canvas
            self.on_mouse_move_add(self._on_mouse_move)
            self.cursor = 'fleur'

    def _on_mouse_up(self, obj, event):
        if event.button in (1, 2):
            self.on_mouse_move_del(self._on_mouse_move)
            self.cursor = None

    def _on_mouse_move(self, obj, event):
        # if self._drag_start_geom is None: # UNUSED region selector
        x, y = event.position.canvas
        dx, dy = self._drag_start_x - x, self._drag_start_y - y
        x, y, w, h = self._drag_start_region
        obj.region_show(x + dx, y + dy, w, h)

    """ UNUSED region selector stuff
    def region_selector_show(self):
        # from efl.edje import Edje
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
        rel1x = utils.clamp(0.0, rel1x, 1.0)
        rel1y = utils.clamp(0.0, rel1y, 1.0)
        rel2x = utils.clamp(0.0, rel2x, 1.0)
        rel2y = utils.clamp(0.0, rel2y, 1.0)

        # send signal to edje with new rels
        self.sel.message_send(1, (rel1x, rel1y, rel2x, rel2y))
    """


class StatusBar(elm.Box):
    def __init__(self, parent):
        elm.Box.__init__(self, parent, horizontal=True,
                         size_hint_expand=EXPAND_HORIZ,
                         size_hint_fill=FILL_HORIZ)

        self.lb_name = elm.Label(self, ellipsis=True,
                    size_hint_expand=EXPAND_HORIZ, size_hint_fill=FILL_HORIZ,
                    text='<align=left>{}</align>'.format(_('No image selected')))
        self.pack_end(self.lb_name)
        self.lb_name.show()
        
        self.lb_info = elm.Label(self)
        self.pack_end(self.lb_info)
        self.lb_info.show()

        # edit button
        # bt = StdButton(self, icon='edit')
        # bt.callback_clicked_add(lambda b: ImageEditor(self.app))
        # self.pack_end(bt)
        # self.btn_edit = bt

    def update(self, img_path, img_num, tot_imgs, img_size, zoom):
        self.lb_name.text = '<align=left><b>{}:</b> {}</align>'.format(
                                _('File {0} of {1}').format(img_num, tot_imgs),
                                os.path.basename(img_path))
        self.lb_info.text = \
            '<b>{}:</b> {}x{}    <b>{}:</b> {}    <b>{}:</b> {:.0f}%'.format(
                _('Resolution'), img_size[0], img_size[1],
                _('Size'), utils.file_hum_size(img_path),
                _('Zoom'), zoom)


class SlideShow(elm.Slideshow):
    TRANSITIONS = ('fade', 'fade_fast', 'black_fade', 'horizontal', 'vertical',
                   'square', 'immediate')
    def __init__(self, parent, photo_changed_cb, zoom_changed_cb):
        self._photo_changed_cb = photo_changed_cb
        self._zoom_changed_cb = zoom_changed_cb

        self.itc = elm.SlideshowItemClass(self._item_get_func)
        elm.Slideshow.__init__(self, parent, style='eluminance',
                               loop=options.sshow_loop, 
                               transition=options.sshow_transition)
        self.callback_changed_add(self._changed_cb)

        buttons = [ # (mode, tooltip, icon, action)
            (None, _('Zoom in'), 'zoom-in', 'in'),
            (None, _('Zoom out'), 'zoom-out', 'out'),
            (None, _('Zoom 1:1'), 'zoom-original', '1:1'),
            (None, _('Zoom fit'), 'zoom-fit', 'fit'),
            (None, _('Zoom fill'), 'zoom-fill', 'fill'),
            ('sep', None, None, None),
            (None, _('Previous photo'), 'go-previous', 'prev'),
            (None, _('Next photo'), 'go-next', 'next'),
            ('toggle', _('Start/Stop slideshow'), None, None),
            ('spinner', _('Transition time'), None, None),
            ('hover', _('Transition style'), None, None),
            ('sep', None, None, None),
            (None, _('Toggle fullscreen mode'), 'view-fullscreen', 'fs'),
            (None, _('Eluminance info'), 'help-about', 'info'),
        ]

        for mode, tooltip, icon, action in buttons:
            if mode == 'sep':
                w = elm.Separator(self)
            # Play/Pause toggle button
            elif mode == 'toggle':
                w = StdButton(self, icon='media-playback-start', text=_('Play'))
                w.callback_clicked_add(self._buttons_cb, 'slideshow')
                self.toggle_btn = w
            # timeout spinner
            elif mode == 'spinner': 
                w = elm.Spinner(self, label_format="%2.0f secs.",
                                step=1, min_max=(3, 60),
                                value=options.sshow_timeout)
                w.callback_changed_add(self._spinner_cb)
                self.spinner = w
            # Transition selector
            elif mode == 'hover':
                w = elm.Hoversel(self, hover_parent=parent,
                                 text=_(options.sshow_transition))
                w.callback_clicked_add(lambda h: app.win.freeze())
                w.callback_dismissed_add(lambda h: app.win.unfreeze())
                for t in self.TRANSITIONS:
                    w.item_add(t, None, 0, self._transition_cb, t)
                self.hs_transition = w
            # normal buttons
            else: 
                w = StdButton(self, icon=icon)
                w.callback_clicked_add(self._buttons_cb, action)

            parent.layout.box_append('controls.box', w)
            if tooltip: w.tooltip_text_set(tooltip)
            w.show()

    def photo_add(self, path):
        item_data = (path, self.count + 1)
        item = self.item_add(self.itc, item_data)
        # XXX the first added item get the changed_cb called before
        # python-efl can do the _set_obj, so we get a null item.object in the cb
        if self.count == 1 and item.object:
            self._photo_changed_cb(path)

    def photo_nth_show(self, index):
        self.nth_item_get(index).show()

    def play(self):
        self.timeout = options.sshow_timeout
        self.toggle_btn.text = _('Pause')
        self.toggle_btn.icon = 'media-playback-pause'
        self.signal_emit('eluminance,play', 'eluminance')
        app.win.layout.signal_emit('eluminance,play', 'eluminance')

    def pause(self):
        self.timeout = 0.0
        self.toggle_btn.text = _('Play')
        self.toggle_btn.icon = 'media-playback-start'
        self.signal_emit('eluminance,pause', 'eluminance')
        app.win.layout.signal_emit('eluminance,pause', 'eluminance')

    @property
    def photo(self):
        return self.current_item.object

    @property
    def index(self):
        path, index = self.current_item.data
        return index

    def _item_get_func(self, obj, item_data):
        path, index = item_data
        # img = ScrollablePhotocam(self, self._zoom_changed_cb)
        img = ScrollablePhoto(self, self._zoom_changed_cb)
        img.file_set(path)
        img.zoom_set('fit')
        return img

    def _changed_cb(self, obj, item):
        if item.object: # XXX see below note in photo_add()
            path, index = item.data
            self._photo_changed_cb(path)

    def _buttons_cb(self, bt, action):
        if action == 'next':
            self.next()
        elif action == 'prev':
            self.previous()
        elif action == 'slideshow':
            self.play() if self.timeout == 0 else self.pause()
        elif action == 'fs':
            app.win.fullscreen = not app.win.fullscreen
        elif action == 'info':
            InfoWin(app.win)
        elif action in ('in', 'out', 'fit', 'fill', '1:1'):
            self.photo.zoom_set(action)

    def _spinner_cb(self, spinner):
        options.sshow_timeout = spinner.value
        if self.timeout != 0:
            self.timeout = options.sshow_timeout

    def _transition_cb(self, hoversel, item, transition):
        self.transition = options.sshow_transition = transition
        self.hs_transition.text = _(transition)


class InfoWin(elm.DialogWindow):
    def __init__(self, parent):
        elm.DialogWindow.__init__(self, parent, 'eluminance-info', 'Eluminance',
                                  autodel=True)

        fr = elm.Frame(self, style='pad_large', size_hint_expand=EXPAND_BOTH,
                       size_hint_align=FILL_BOTH)
        self.resize_object_add(fr)
        fr.show()

        hbox = elm.Box(self, horizontal=True, padding=(12,12))
        fr.content = hbox
        hbox.show()

        vbox = elm.Box(self, align=(0.0,0.0), padding=(6,6),
                       size_hint_expand=EXPAND_VERT, size_hint_fill=FILL_VERT)
        hbox.pack_end(vbox)
        vbox.show()

        # icon + version
        ic = utils.SafeIcon(self, 'eluminance', size_hint_min=(64,64))
        vbox.pack_end(ic)
        ic.show()

        lb = elm.Label(self, text=_('Version: %s') % __version__)
        vbox.pack_end(lb)
        lb.show()

        sep = elm.Separator(self, horizontal=True)
        vbox.pack_end(sep)
        sep.show()

        # buttons
        bt = elm.Button(self, text=_('Eluminance'), size_hint_fill=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: self.entry.text_set(utils.INFO))
        vbox.pack_end(bt)
        bt.show()

        bt = elm.Button(self, text=_('Website'),size_hint_align=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: utils.xdg_open(utils.HOMEPAGE))
        vbox.pack_end(bt)
        bt.show()

        bt = elm.Button(self, text=_('Authors'), size_hint_align=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: self.entry.text_set(utils.AUTHORS))
        vbox.pack_end(bt)
        bt.show()

        bt = elm.Button(self, text=_('License'), size_hint_align=FILL_HORIZ)
        bt.callback_clicked_add(lambda b: self.entry.text_set(utils.LICENSE))
        vbox.pack_end(bt)
        bt.show()

        # main text
        self.entry = elm.Entry(self, editable=False, scrollable=True,
                               text=utils.INFO, size_hint_expand=EXPAND_BOTH,
                               size_hint_fill=FILL_BOTH)
        self.entry.callback_anchor_clicked_add(lambda e,i: utils.xdg_open(i.name))
        hbox.pack_end(self.entry)
        self.entry.show()

        self.resize(400, 200)
        self.show()


class MainWin(elm.StandardWindow):
    def __init__(self):
        elm.StandardWindow.__init__(self, 'eluminance', 'Eluminance',
                                    autodel=True, size=(800,600),
                                    tree_focus_allow=False)
        self.callback_delete_request_add(lambda o: elm.exit())

        self.layout = elm.Layout(self, file=(THEME_FILE, 'eluminance/main'),
                                 size_hint_expand=EXPAND_BOTH,
                                 tree_focus_allow=False)
        self.resize_object_add(self.layout)
        self.layout.show()

    def swallow_all(self, app):
        self.layout.content_set('photo.swallow', app.sshow)
        self.layout.content_set('grid.swallow', app.grid)
        self.layout.content_set('tree.swallow', app.tree)
        self.layout.content_set('status.swallow', app.status)
    
    def freeze(self):
        self.layout.edje.play_set(False)

    def unfreeze(self):
        self.layout.edje.play_set(True)


class EluminanceApp(object):
    def __init__(self):
        self.win = MainWin()
        self.sshow = SlideShow(self.win, self.photo_changed, self.zoom_changed)
        self.grid = PhotoGrid(self.win, self.grid_selected)
        self.tree = TreeView(self.win, self.tree_selected)
        self.status = StatusBar(self.win)
        self.win.swallow_all(self)

        home = os.path.expanduser('~')
        self.current_path = home
        self.current_file = None
        request = None

        if len(sys.argv) > 1:
            request = os.path.abspath(sys.argv[1])
            if not os.path.exists(request):
                request = None

        if request:
            if request.startswith(home):
                self.tree.set_root(home)
            else:
                self.tree.set_root('/')
            self.tree.expand_to_folder(request)
            if os.path.isfile(request):
                self.grid.file_select(request)
        else:
            self.tree.set_root(home)

        self.win.show()

    def tree_selected(self, path):
        self.current_path = path
        self.sshow.clear()
        self.grid.clear()
        for f in utils.natural_sort(os.listdir(path)):
            if os.path.splitext(f)[-1].lower() in IMG_EXTS:
                full_path = os.path.join(path, f)
                self.grid.photo_add(full_path)
                self.sshow.photo_add(full_path)
        self.win.title = 'eluminance - ' + self.current_path

    def grid_selected(self, path, index):
        self.sshow.photo_nth_show(index)

    def photo_changed(self, path):
        self.current_file = path
        self.grid.file_select(path)
        self.status.update(self.current_file, self.sshow.index, self.sshow.count,
                           self.sshow.photo.image_size, 0)

    def zoom_changed(self, zoom):
        # TODO update only the zoom
        self.status.update(self.current_file, self.sshow.index, self.sshow.count,
                           self.sshow.photo.image_size, zoom)


def main():
    options.load()
    elm.need_ethumb()
    elm.theme_extension_add(THEME_FILE)

    global app
    app = EluminanceApp()
    elm.run()
    options.save()

if __name__ == '__main__':
    sys.exit(main())


"""
class ImageEditor(object):
    def __init__(self, app):
        self.bg = Background(app.win, size_hint_expand=EXPAND_BOTH)
        app.win.resize_object_add(self.bg)
        self.bg.show()

        box = elm.Box(self.bg, size_hint_expand=EXPAND_BOTH,
                      size_hint_fill=FILL_BOTH)
        app.win.resize_object_add(box)
        box.show()

        tb = elm.Toolbar(app.win, homogeneous=True, menu_parent=app.win,
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
"""
