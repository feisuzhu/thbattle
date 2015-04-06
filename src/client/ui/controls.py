# -*- coding: utf-8 -*-

# -- stdlib --
from collections import namedtuple
import logging

# -- third party --
from pyglet.gl import GL_CLIENT_VERTEX_ARRAY_BIT, GL_ENABLE_BIT, GL_LINES, GL_QUADS, GL_RGBA
from pyglet.gl import GL_SCISSOR_TEST, GL_T4F_V4F, GL_TEXTURE_2D, GLfloat, glBegin, glBindTexture
from pyglet.gl import glColor3f, glColor4f, glCopyTexImage2D, glDisable, glDrawArrays, glEnable
from pyglet.gl import glEnd, glInterleavedArrays, glLineWidth, glLoadIdentity, glPopAttrib
from pyglet.gl import glPopClientAttrib, glPopMatrix, glPushAttrib, glPushClientAttrib, glPushMatrix
from pyglet.gl import glRectf, glScissor, glTranslatef, glVertex2f
from pyglet.graphics import OrderedGroup
from pyglet.sprite import Sprite
from pyglet.window import key, mouse
import gevent
import pyglet
import requests

# -- own --
from client.core import Executive
from client.ui import ui_meta as client_ui_meta
from client.ui.base import Control, Overlay
from client.ui.base.interp import InterpDesc, LinearInterp
from client.ui.resloader import L
from utils import flatten, inpoly, instantiate, pyperclip, rectv2f, rrectv2f, textsnap

# -- code --
# -- code --
KEYMOD_MASK = key.MOD_CTRL | key.MOD_ALT | key.MOD_SHIFT
log = logging.getLogger('UI_Controls')


class Colors:
    @instantiate
    class green:
        # Frame
        frame          = 49,  69,  99
        heavy          = 66,  138, 115
        medium         = 140, 186, 140
        light          = 206, 239, 156
        caption        = 255, 255, 255
        caption_shadow = heavy
        close_btn      = L('c-buttons-close_green')

        # Button
        btn_frame      = heavy
        fill_up        = 173, 207, 140
        fill_medline   = 173, 223, 156
        fill_down      = 189, 223, 156
        fill_botline   = 222, 239, 206
        text           = frame

    @instantiate
    class red:
        # Frame
        frame          = 171,  68,   81
        medium         = 0xff, 0x9f, 0x8c
        heavy          = frame
        light          = 254,  221,  206
        caption        = 255,  255,  255
        caption_shadow = frame
        close_btn      = L('c-buttons-close_red')

        # Button
        btn_frame      = frame
        fill_up        = 0xee, 0x89, 0x78
        fill_medline   = fill_up
        fill_down      = 0xf7, 0x9c, 0x8c
        fill_botline   = fill_down
        text           = frame

    @instantiate
    class blue:
        # Frame
        frame          = 0x31, 0x55, 0x97
        medium         = 0x90, 0xbc, 0xed
        heavy          = 0x64, 0x8a, 0xd0
        light          = 0xa3, 0xd1, 0xfa
        caption        = frame
        caption_shadow = 0xe5, 0xef, 0xfb
        close_btn      = L('c-buttons-close_blue')

        # Button
        btn_frame      = 0x54, 0x67, 0xa6
        fill_up        = 0x90, 0xbf, 0xef
        fill_down      = 0xa3, 0xd1, 0xfa
        fill_medline   = 0x9a, 0xc8, 0xf5
        fill_botline   = 0xc5, 0xf2, 0xff
        text           = frame

    @instantiate
    class orange:
        # Frame
        frame          = 0x88, 0x66, 0x66
        medium         = 0xff, 0xcc, 0x77
        heavy          = frame
        light          = 0xff, 0xee, 0xaa
        caption        = 255,  255,  255
        caption_shadow = frame
        close_btn      = L('c-buttons-close_orange')

        # Button
        btn_frame      = frame
        fill_up        = medium
        fill_medline   = fill_up
        fill_down      = 0xff, 0xdd, 0x88
        fill_botline   = light
        text           = frame

    @instantiate
    class gray:
        # Frame
        close_btn      = L('c-buttons-close_blue')
        btn_frame      = 104, 104, 104
        caption        = 81,  81,  81
        caption_shadow = 237, 237, 237
        fill_botline   = 229, 229, 229
        fill_down      = 199, 199, 199
        fill_medline   = 191, 191, 191
        fill_up        = 182, 182, 182
        frame          = 81,  81,  81
        heavy          = 134, 134, 134
        light          = 199, 199, 199
        medium         = 180, 180, 180
        text           = 81,  81,  81

    @staticmethod
    def get4f(c):
        return c[0]/255.0, c[1]/255.0, c[2]/255.0, 1.0

    @staticmethod
    def get4i(c):
        return c + (255, )


class AbstractButton(Control):
    NORMAL   = 0
    HOVER    = 1
    PRESSED  = 2
    DISABLED = 3

    hover_alpha = InterpDesc('_hv')

    def __init__(self, max_hover_alpha=0.25, *a, **k):
        Control.__init__(self, *a, **k)
        self._state = Button.NORMAL
        self.hover_alpha = 0.0
        self.max_hover_alpha = max_hover_alpha

    def on_mouse_enter(self, x, y):
        if self.state != Button.DISABLED:
            self.state = Button.HOVER
        return pyglet.event.EVENT_HANDLED

    def on_mouse_leave(self, x, y):
        if self.state != Button.DISABLED:
            self.state = Button.NORMAL
        return pyglet.event.EVENT_HANDLED

    def on_mouse_press(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            if button == mouse.LEFT:
                self.state = Button.PRESSED
        return pyglet.event.EVENT_HANDLED

    def on_mouse_release(self, x, y, button, modifier):
        if self.state == Button.PRESSED:
            if button == mouse.LEFT:
                self.state = Button.HOVER
                self.dispatch_event('on_click')
        return pyglet.event.EVENT_HANDLED

    def on_mouse_click(self, x, y, button, modifier):
        return pyglet.event.EVENT_HANDLED

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, val):
        last = self._state
        self._state = val
        if val == Button.HOVER:
            self.hover_alpha = self.max_hover_alpha
        elif last == Button.HOVER and val == Button.NORMAL:
            self.hover_alpha = LinearInterp(
                self.max_hover_alpha, 0, .17
            )
        else:
            self.update()

    def update(self):
        pass


class Button(AbstractButton):
    def __init__(self, caption='Button', color=Colors.green, *args, **kwargs):
        AbstractButton.__init__(self, *args, **kwargs)
        self._batch = None
        self.caption = caption

        self.need_update = True
        self.color = color

    def update(self):
        if self._batch:
            self._batch.need_update = True

    def _fill_batch(self, batch):
        ax, ay = self.abs_coords()
        w, h = self.width, self.height

        color = self.color

        up, down = Colors.get4f(color.fill_up), Colors.get4f(color.fill_down)
        heavy = Colors.get4f(self.color.heavy)
        color_array = flatten([
            down, down, up, up, [heavy]*4
        ])

        background = OrderedGroup(0)
        foreground = OrderedGroup(1)
        effect = OrderedGroup(2)

        batch.add(
            8, GL_QUADS, background,
            ('v2f', flatten([
                rectv2f(.5, .5, w-.5, h-.5, ax, ay),
                rrectv2f(.5, .5, w-.5, h-.5, ax, ay),
            ])),
            ('c4f', color_array),
        )

        pyglet.text.Label(
            self.caption, u'AncientPix', 9,
            color=color.text + (255,),
            x=(ax + self.width // 2), y=(ay + self.height // 2),
            anchor_x='center', anchor_y='center', batch=batch,
            group=foreground
        )

        self.hilight_vl = batch.add(
            4, GL_QUADS, effect,
            ('v2f', (ax, ay, ax + w, ay, ax + w, ay + h, ax, ay + h)),
            ('c4f/stream', [0.0] * (4 * 4)),
        )

    @staticmethod
    def batch_draw(btns):
        glPushMatrix()
        glLoadIdentity()
        batch_list = set([b._batch for b in btns])
        batch = list(batch_list)[0]
        if not (len(batch_list) == 1 and batch and not batch.need_update):
            for i in batch_list:
                if i:
                    for b in i.buttons:
                        b._batch = None

            batch = pyglet.graphics.Batch()
            batch.buttons = btns[:]
            batch.need_update = False
            for b in btns:
                b._batch = batch
                b._fill_batch(batch)

        for b in btns:
            if b.state == Button.DISABLED:
                continue

            hilight = (0., 0., 0., 0.)
            if b.state == Button.PRESSED:
                hilight = (0., 0., 0., .25)
            else:
                a = b.hover_alpha
                if a:  # HOVER, or HOVER -> NORMAL
                    hilight = (1.0, 1.0, .843, a)

            b.hilight_vl.colors[:] = hilight * 4

        batch.draw()
        glPopMatrix()

    def draw(self):
        glColor3f(1.0, 0.0, 0.0)
        glRectf(0, 0, self.width, self.height)

    def _get_color(self):
        if self._state == Button.DISABLED:
            return Colors.gray

        return self._color

    def _set_color(self, val):
        self._color = val
        self.update()

    color = property(_get_color, _set_color)


class ImageButton(AbstractButton):
    def __init__(self, images, *args, **kwargs):
        AbstractButton.__init__(self, *args, **kwargs)
        self.images = images
        self.width = images[0].width
        self.height = images[0].height

    @staticmethod
    def batch_draw(ibs):
        glPushMatrix()
        glLoadIdentity()
        glColor3f(1.0, 1.0, 1.0)

        glPushAttrib(GL_ENABLE_BIT)
        glEnable(GL_TEXTURE_2D)

        tex = [None]

        def blit(btn, idx):
            img = btn.images[idx]
            t = getattr(img, 'owner', img)
            if tex[0] != t:
                tex[0] = t
                glBindTexture(GL_TEXTURE_2D, t.id)
            img.blit_nobind(*btn.abs_coords())

        for btn in ibs:
            if btn.state == Button.DISABLED:
                blit(btn, 3)
            else:
                if btn.state == Button.PRESSED:
                    blit(btn, 2)
                else:
                    blit(btn, 0)
                    a = btn.hover_alpha
                    if a:  # HOVER, or HOVER -> NORMAL
                        glColor4f(1.0, 1.0, 1.0, a)
                        blit(btn, 1)
                        glColor3f(1, 1, 1)

        glPopAttrib()
        glPopMatrix()

AbstractButton.register_event_type('on_click')


def batch_drawlabel(lbls):
    s = set([l.batch for l in lbls])
    if len(s) == 1:
        batch = list(s)[0]
    else:
        batch = pyglet.graphics.Batch()
        for l in lbls:
            adj = getattr(l, '_loc_adjusted', False)
            l.begin_update()
            if not adj:
                p = l._parent
                x, y = p.abs_coords()
                l.x += x
                l.y += y
                l._loc_adjusted = True
            l._own_batch = False
            l.batch = batch
            l.end_update()
    batch.draw()


def batch_drawsprite(sprites):
    s = list(set([l.batch for l in sprites]))
    if len(s) == 1 and s[0]:
        batch = s[0]
    else:
        batch = pyglet.graphics.Batch()
        for sp in sprites:
            adj = getattr(sp, '_loc_adjusted', False)
            sp.batch = batch
            if not adj:
                p = sp._parent
                x, y = p.abs_coords()
                sp.set_position(sp.x + x, sp.y + y)
                sp._loc_adjusted = True
    batch.draw()


class Frame(Control):
    no_move = True
    zindex = 1
    bg_group = OrderedGroup(50)
    frame_group = OrderedGroup(100)
    labels_group = OrderedGroup(150)
    top_group = OrderedGroup(1000)

    def __init__(self, caption='Frame', color=Colors.green,
                 bot_reserve=10, bg=None, thin_shadow=False,
                 *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.caption = caption
        self._color = color
        self.bg = bg
        self._labels = []
        self.bot_reserve = bot_reserve
        self.thin_shadow = thin_shadow

        # HACK
        self._batch = pyglet.graphics.Batch()  # will be abandoned soon, acutally
        self._fill_batch(self._batch)
        self._batch.dialogs = [self]
        self._batch.need_update = False

        self.update()

    @property
    def color(self):
        return self._color

    @property
    def labels(self):
        raise AttributeError('Do not use labels! use add_label!')

    def update(self):
        self.set_caption(self.caption)

        # Frame.update_color(self)
        # Frame.update_position(self)
        # Frame.update_bg(self)

        self.update_color()
        self.update_position()
        self.update_bg()
        self._update_labels()

    def update_bg(self):
        bg = getattr(self, 'bg', None)
        r, w, h = self.bot_reserve, self.width, self.height
        _w = w - 2
        _h = h - 24 - r
        if bg:
            if bg.height > h - 24 - r or bg.width > w - 2:
                _w = min(bg.width, _w)
                _h = min(bg.height, _h)
                bg = bg.get_region(0, 0, _w, _h)
        else:
            # HACK
            white = L('c-white')
            bg = white.get_region(0, 0, _w, _h)
            bg.tex_coords = white.tex_coords

        self.bgsprite.image = bg

    def on_resize(self, w, h): self.update_bg()

    def _fill_batch(self, batch):
        ax, ay = self.abs_coords()
        self._batch = batch

        r = self.bot_reserve
        self.bgsprite = Sprite(L('c-white'), x=ax+2, y=ax+r, batch=batch, group=self.bg_group)
        self.update_bg()

        self.framevlist = batch.add(
            20, GL_QUADS, self.frame_group,
            'v2f', 'c4B',
        )

        for lbl in self._labels:
            if lbl.batch is not batch:
                lbl.batch = batch

        if self.thin_shadow:
            shadow = (1, ) + self.color.caption_shadow + (255,)
        else:
            shadow = (2, ) + self.color.caption_shadow + (255,)

        self.caption_lbl = pyglet.text.Label(
            u'', u'AncientPix', 9,
            color=self.color.caption + (255,),
            shadow=shadow,
            anchor_x='left', anchor_y='bottom',
            batch=batch, group=self.labels_group,
        )

        self.set_caption(self.caption)

        self.update()

    def _get_frame_v2f(self):
        ax, ay = self.abs_coords()
        w, h, r = self.width, self.height, self.bot_reserve
        return flatten([
            rectv2f(ax+.5, ay+h-24+.5, w-.5, 24-.5),  # title bar
            rectv2f(ax+.5, ay+.5, w-.5, r-.5),  # bot reserve
            rrectv2f(ax+.5, ay+r+.5, w-.5, h-24-r-.5),  # heavy line
            rrectv2f(ax+.5, ay+.5, w-.5, h-.5),  # border
            rrectv2f(ax+1.5, ay+1.5, w-2.5, h-2.5),
        ])

    def set_color(self, color):
        self._color = color
        Frame.update_color(self)

    def update_color(self):
        c = self.color
        C = Colors.get4i
        medium = C(c.medium)
        heavy = C(c.heavy)
        frame = C(c.frame)

        self.framevlist.colors[:] = flatten([
            [medium] * 4,  # title bar
            [medium] * 4,  # bot reserve
            [heavy] * 4,  # heavy line
            [frame] * 8,  # border
        ])

        t = 1 if self.thin_shadow else 2
        self.caption_lbl.shadow = (t,) + C(c.caption_shadow)
        self.caption_lbl.color = C(c.caption)

    def set_position(self, x, y):
        self.x, self.y = x, y
        self.update_position()

    def update_position(self):
        ax, ay = self.abs_coords()
        self.framevlist.vertices[:] = self._get_frame_v2f()
        self.bgsprite.set_position(ax+2, ay+self.bot_reserve)
        self._update_labels()

        cap = self.caption_lbl

        cap.begin_update()
        cap.x = ax + 20
        cap.y = ay + self.height - 20
        cap.end_update()

    def set_caption(self, cap):
        f = pyglet.font.load('AncientPix', 9)
        cap = textsnap(cap, f, self.width - 20 - 4)

        self.caption = cap
        self.caption_lbl.text = cap

    @staticmethod
    def batch_draw(dlgs):
        glColor3f(1, 1, 1)
        glPushMatrix()
        glLoadIdentity()

        batch_list = set([d._batch for d in dlgs])
        batch = list(batch_list)[0]
        if not (len(batch_list) == 1 and batch and not batch.need_update):
            for i in batch_list:
                if i:
                    for d in i.dialogs:
                        d._batch = None

            batch = pyglet.graphics.Batch()
            batch.dialogs = dlgs[:]
            batch.need_update = False
            for d in dlgs:
                d._batch = batch
                d._fill_batch(batch)

        batch.draw()

        glPopMatrix()

        cl = []
        map(cl.extend, [d.control_list for d in dlgs])
        Control.do_draw(cl)

    def add_label(self, text, x, y, *a, **k):
        ax, ay = self.abs_coords()
        l = pyglet.text.Label(
            text, x=ax+x, y=ay+y,
            font_name='AncientPix',
            batch=self._batch, group=self.labels_group,
            *a, **k
        )
        l._parent = self
        l._ox = x
        l._oy = y
        self._labels.append(l)

        return l

    def remove_label(self, l):
        self._labels.remove(l)
        l.delete()
        shadow = getattr(l, '_shadow', None)
        if shadow:
            self._labels.remove(shadow)
            shadow.delete()

    def set_label_position(self, l, x, y):
        l._ox = x
        l._oy = y
        self._update_labels()

    def _update_labels(self):
        ax, ay = self.abs_coords()
        for l in self._labels:
            l.begin_update()
            l.x = ax + l._ox
            l.y = ay + l._oy
            l.end_update()

    def delete(self):
        Control.delete(self)
        for l in self._labels:
            l.delete()
        self.bgsprite.delete()
        self.caption_lbl.delete()


class Dialog(Frame):
    no_move = False
    next_zindex = 20

    def __init__(self, *a, **k):
        Frame.__init__(self, *a, **k)
        self.zindex = Dialog.next_zindex
        Dialog.next_zindex += 1
        self.btn_close = ImageButton(
            images=self.color.close_btn,
            parent=self, font_size=12,
            x=self.width-18, y=self.height-19,
        )
        self.dragging = False

        @self.btn_close.event
        def on_click():
            self.close()

        timeout = getattr(self, 'timeout', None)
        self.close_later = timeout and gevent.spawn_later(timeout, self.close)

    def on_resize(self, w, h):
        super(Dialog, self).on_resize(w, h)
        self.btn_close.x, self.btn_close.y = w-18, h-19

    @staticmethod
    def batch_draw(dlgs):
        for d in dlgs:
            Frame.batch_draw([d])

    def on_mouse_press(self, x, y, button, modifier):
        w, h = self.width, self.height
        self.zindex = Dialog.next_zindex
        Dialog.next_zindex += 1
        if not self.no_move and button == mouse.LEFT and h-20 <= y <= h and x <= w-20:
            self.set_capture('on_mouse_drag', 'on_mouse_release')
            self.dragging = True

    def on_mouse_release(self, x, y, button, modifier):
        if self.dragging:
            self.release_capture('on_mouse_drag', 'on_mouse_release')
            self.dragging = False

    def on_mouse_drag(self, x, y, dx, dy, button, modifier):
        if self.dragging:
            self.set_position(self.x + dx, self.y + dy)
            self.dispatch_event('on_move', self.x, self.y)

    def close(self):
        self._cancel_close = False
        self.dispatch_event('on_close')
        if not self._cancel_close:
            self.delete()
            self.dispatch_event('on_destroy')

    def delete(self):
        if gevent.getcurrent() is not self.close_later:
            self.close_later and self.close_later.kill()

        Frame.delete(self)

    def cancel_close(self):
        self._cancel_close = True

Dialog.register_event_type('on_move')
Dialog.register_event_type('on_close')
Dialog.register_event_type('on_destroy')


class BalloonPrompt(object):
    def __init__(self, control, balloon_show_func=None):
        self.balloon_inited    = False
        self.balloon_panel     = None
        self.balloon_cursorloc = (0, 0)
        self.balloon_width     = 288
        self.balloon_state     = 'hidden'
        self.control           = control
        self.balloon_show_func = balloon_show_func or self.balloon_show

    def set_balloon(self, text, region=None, width=288, polygon=None):
        self.balloon_text = text
        if region:
            x, y, w, h = region
            x1, y1 = x + w, y + h
            self.balloon_polygon = ((x, y), (x1, y), (x1, y1), (x, y1))
        else:
            self.balloon_polygon = polygon

        self.balloon_width = width

        if not self.balloon_inited:
            self.balloon_inited = True
            self.control.push_handlers(
                on_mouse_motion=self.balloon_on_mouse_motion,
                on_mouse_drag=self.balloon_on_mouse_motion,
                on_mouse_enter=self.balloon_on_mouse_enter,
                on_mouse_leave=self.balloon_on_mouse_leave,
            )
        else:
            if self.balloon_state == 'shown':
                self.balloon_panel.delete()
                self.balloon_panel = None

        self.balloon_state = 'hidden'

    def balloon_on_mouse_motion(self, x, y, dx, dy, *a):
        ax, ay = self.control.abs_coords()
        ax += x
        ay += y

        self.balloon_cursorloc = (ax, ay)

        poly = self.balloon_polygon
        if poly:
            if inpoly(x, y, poly):
                self.balloon_on_mouse_enter(x, y)
            else:
                self.balloon_on_mouse_leave(x, y)

        b = self.balloon_panel
        b and self.balloon_setloc()

    def balloon_setloc(self):
        b = self.balloon_panel
        o = Overlay.cur_overlay
        x, y = self.balloon_cursorloc
        ow, oh = o.width, o.height
        bw, bh = b.width, b.height

        if x*2 <= ow:
            x += 10
            if x + bw > ow:
                x = ow - bw
        else:
            x -= bw + 10
            if x < 0:
                x = 0

        if y*2 <= oh:
            y += 10
            if y + bh > oh:
                y = oh - bh
        else:
            y -= bh + 10
            if y < 0:
                y = 0

        b.x = x
        b.y = y

    def balloon_on_mouse_enter(self, x, y):
        if self.balloon_state == 'hidden':
            self.balloon_state = 'ticking'
            self.balloon_overlay = Overlay.cur_overlay
            pyglet.clock.schedule_once(self._balloon_show, 0.8)

    def balloon_on_mouse_leave(self, x, y):
        if self.balloon_state == 'ticking':
            pyglet.clock.unschedule(self._balloon_show)
        elif self.balloon_state == 'shown':
            self.balloon_panel.delete()
            self.balloon_panel = None
        self.balloon_state = 'hidden'

    def _balloon_show(self, dt):
        if self.balloon_state == 'shown': return
        if Overlay.cur_overlay != self.balloon_overlay: return
        if not self.balloon_text: return

        self.balloon_state = 'shown'
        panel = self.balloon_show_func()
        self.balloon_panel = panel
        self.balloon_setloc()

        @panel.event
        def on_mouse_enter(x, y, panel=panel):
            panel.delete()

    def balloon_show(self):
        width = self.balloon_width
        ta = TextArea(parent=None, x=2, y=2, width=width, height=100)
        ta.append(self.balloon_text)
        h = ta.content_height
        ta.height = h

        panel = Panel(parent=Overlay.cur_overlay, x=0, y=0, width=width+4, height=h+4, zindex=999999)
        panel.add_control(ta)
        panel.fill_color = (1.0, 1.0, 0.9, 0.5)

        return panel


class TextBox(Control):
    DISABLE_NEWLINE = True

    def __init__(self, text='Yoooooo~', color=Colors.green, font_name='AncientPix', *args, **kwargs):
        Control.__init__(self, can_focus=True, *args, **kwargs)
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.document.set_style(0, len(self.document.text), dict(
            color=(0, 0, 0, 255),
            font_name=font_name,
            font_size=9,
        ))

        self.color = color

        width = self.width
        f = self.document.get_font()
        font_height = f.ascent - f.descent
        if self.height == 0:
            height = font_height
            self.height = height
        else:
            height = self.height

        l = self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width-9, font_height, multiline=False,
        )
        l.anchor_x, l.anchor_y = 'left', 'center'
        l.x, l.y = 4, height // 2 + 1
        self.caret = pyglet.text.caret.Caret(self.layout)

        self.set_handlers(self.caret)
        self.push_handlers(self)

        from base.baseclasses import main_window
        self.window = main_window
        self.text_cursor = self.window.get_system_mouse_cursor('text')
        self.on_lostfocus()

    def _gettext(self):
        return self.document.text

    def _settext(self, text):
        self.document.text = text

    text = property(_gettext, _settext)

    def draw(self):
        w, h = self.width, self.height
        border = [i/255.0 for i in self.color.heavy]
        fill = [i/255.0 for i in self.color.light]
        glColor3f(*fill)
        glRectf(0, 0, w, h)
        glColor3f(*border)
        glRectf(0, h, w, 0)
        self.layout.draw()

    def on_focus(self):
        self.caret.visible = True
        self.caret.mark = 0
        self.caret.position = len(self.document.text)
        self.focused = True

    def on_lostfocus(self):
        self.caret.visible = False
        self.caret.mark = self.caret.position = 0
        self.focused = False

    def on_mouse_enter(self, x, y):
        self.window.set_mouse_cursor(self.text_cursor)

    def on_mouse_leave(self, x, y):
        self.window.set_mouse_cursor(None)

    def on_mouse_drag(self, x, y, dx, dy, btn, modifier):
        # If I'm not focused, don't select texts
        if btn == mouse.LEFT and self.focused:
            x = max(4, x)
            self.caret.on_mouse_drag(x, y, dx, dy, btn, modifier)
        return pyglet.event.EVENT_HANDLED

    def on_mouse_press(self, x, y, btn, modifier):
        self.set_capture('on_mouse_release', 'on_mouse_drag')

    def on_mouse_release(self, x, y, btn, modifier):
        self.release_capture('on_mouse_release', 'on_mouse_drag')
        return True

    def on_key_press(self, symbol, modifiers):
        if modifiers & KEYMOD_MASK == key.MOD_CTRL:
            if symbol == key.A:
                self.caret.position = 0
                self.caret.mark = len(self.text)
                return pyglet.event.EVENT_HANDLED

            elif symbol == key.C:
                start = self.layout.selection_start
                end = self.layout.selection_end
                if start != end:
                    pyperclip.copy(self.text[start:end])
                return pyglet.event.EVENT_HANDLED

            elif symbol == key.ENTER:
                if self.DISABLE_NEWLINE: return
                self.dispatch_event('on_text', u'\n')
                return pyglet.event.EVENT_HANDLED

            elif symbol == key.V:
                content = unicode(pyperclip.paste())
                if self.DISABLE_NEWLINE:
                    for le in (u'\r\n', u'\r', u'\n'):
                        content = content.replace(le, u' ')
                self.dispatch_event('on_text', content)
                return pyglet.event.EVENT_HANDLED

            elif symbol == key.X:
                start = self.layout.selection_start
                end = self.layout.selection_end
                if start != end:
                    pyperclip.copy(self.text[start:end])
                    self.dispatch_event('on_text', u'')
                return pyglet.event.EVENT_HANDLED

    def on_text(self, text):
        if text == '\r':
            self.dispatch_event('on_enter')
            return pyglet.event.EVENT_HANDLED

TextBox.register_event_type('on_enter')


class PasswordTextBox(TextBox):
    def __init__(self, *a, **k):
        TextBox.__init__(self, font_name='AncientPixPassword', *a, **k)


class BadgeIcon(Control):
    def __init__(self, img, x, y, text, *a, **k):
        Control.__init__(self, x=x, y=y, width=20, height=20, *a, **k)
        self.image = img
        self.sprite = Sprite(img)
        balloon = BalloonPrompt(self)
        balloon.set_balloon(text)

    def draw(self):
        self.sprite.draw()

    def delete(self):
        Control.delete(self)
        self.sprite.delete()

    def set_position(self, x, y):
        self.x, self.y = x, y


class PlayerPortrait(Frame):
    def __init__(self, player_name, color=Colors.blue, *args, **kwargs):
        self.account = None
        self.ready = False
        from base.baseclasses import main_window
        self.window = main_window
        self.hand_cursor = self.window.get_system_mouse_cursor('hand')
        self.accinfo_labels = []
        self.badge_icons = []

        self.player_name = player_name
        Frame.__init__(
            self, caption=player_name, color=color,
            bot_reserve=50, width=128, height=245,
            thin_shadow=True,
            *args, **kwargs
        )
        sensor = SensorLayer(self)

        @sensor.event
        def on_mouse_enter(x, y):
            self.account or self.window.set_mouse_cursor(self.hand_cursor)

        @sensor.event
        def on_mouse_leave(x, y):
            self.window.set_mouse_cursor(None)

        @sensor.event
        def on_mouse_release(x, y, button, modifier):
            Executive.change_location(
                self.parent.portraits.index(self)
            )

        self.buttons = []

        def btn(caption, command, x, y, w, h):
            btn = Button(
                caption, parent=self,
                x=x, y=y, width=w, height=h,
                manual_draw=True,
                color=self.color
            )
            self.buttons.append(btn)

            @btn.event
            def on_click(btn=btn, cmd=command):
                cmd()

        btn(u'请离', lambda: self.userid and Executive.kick_user(self.userid), 90, 55, 32, 20)

    def update(self):
        acc = self.account
        self.avatar = None
        if acc:
            name = u'<' + acc.username + u'>'
            if self.ready: name = u'(准备)' + name
            self.userid = acc.userid
        else:
            name = u'空位置'
            self.userid = 0

        for l in self.accinfo_labels:
            self.remove_label(l)

        self.accinfo_labels = []

        for i in self.badge_icons:
            i.delete()

        self.badge_icons = []
        if self.avatar:
            self.avatar.delete()
        self.avatar = None
        self.set_caption(name)

        avurl = acc.other['avatar'] if acc else None
        if avurl:
            img = self.cached_avatar.get(avurl, None)
            if img:
                sprite = pyglet.sprite.Sprite(img, x=64, y=150)
                sprite.scale = min(1.0, 64.0*2/img.width, 170.0*2/img.height)
                sprite._parent = self
                self.avatar = sprite
            else:
                @gevent.spawn
                def callback(avurl=avurl):
                    resp = requests.get(avurl)
                    if not resp.ok:
                        log.warning('Avatar fetch not ok: %s -> %s', resp.status_code, avurl)
                        return

                    data = resp.content
                    if data.startswith('GIF'):
                        fn = 'foo.gif'
                    elif data.startswith('\xff\xd8') and data.endswith('\xff\xd9'):
                        fn = 'foo.jpg'
                    elif data.startswith('\x89PNG'):
                        fn = 'foo.png'

                    from StringIO import StringIO
                    f = StringIO(data)

                    try:
                        if fn == 'foo.gif':
                            from utils import gif_to_animation
                            img = gif_to_animation(f)
                        else:
                            img = pyglet.image.load(fn, file=f)
                            img.anchor_x, img.anchor_y = img.width // 2, img.height // 2
                    except:
                        log.exception('Loading avatar')
                        img = False

                    sprite = False
                    if img:
                        sprite = pyglet.sprite.Sprite(img, x=64, y=150)
                        sprite.scale = min(1.0, 64.0*2/img.width, 170.0*2/img.height)
                        sprite._parent = self

                    else:
                        img = sprite = False

                    self.cached_avatar[avurl] = img

                    if self.avatar:
                        self.avatar.delete()
                    self.avatar = sprite

                    sprite and self.update()

        Frame.update(self)

        if not acc:
            return

        f = pyglet.font.load('AncientPix', 9)

        def Lbl(text, loc):
            text = textsnap(text, f, self.width - 8 - 4)
            C = Colors.get4i
            ccap = C(self.color.caption)
            ccapshadow = (1,) + C(self.color.caption_shadow)

            self.accinfo_labels.append(self.add_label(
                text, x=8, y=47-15*loc,
                anchor_x='left', anchor_y='top',
                font_size=9, color=ccap,
                shadow=ccapshadow,
            ))

        Lbl(acc.other['title'], 0)
        Lbl(u'节操： %d' % acc.other['credits'], 1)
        g, d = acc.other['games'], acc.other['drops']
        dr = int(100*d/g) if d else 0
        Lbl(u'游戏数：%d(%d%%)' % (g, dr), 2)

        def B(loc, badge_name):
            badge = client_ui_meta.badges.get(badge_name)

            if not badge:
                log.warning('No such badge: %s', badge_name)
                return

            if loc > 2:
                loc += 2

            y, x = divmod(loc, 5)

            self.badge_icons.append(BadgeIcon(
                L(badge.badge_anim),
                128 - 30 - 22 * (4 - x), 55 + 22 * y,
                badge.badge_text,
                parent=self,
            ))

        [B(i, v) for i, v in enumerate(acc.other['badges'])]

    def draw(self):
        PlayerPortrait.draw(self)
        if self.avatar:
            self.avatar.draw()

        Button.batch_draw(self.buttons)

    def delete(self):
        Frame.delete(self)
        if self.avatar:
            self.avatar.delete()

    @staticmethod
    def batch_draw(pps):
        Frame.batch_draw(pps)
        sprites = [getattr(p, 'avatar', None) for p in pps]
        sprites = [s for s in sprites if s]
        batch_drawsprite(sprites)
        btns = []
        map(btns.extend, [p.buttons for p in pps])
        Button.batch_draw(btns)


class TextArea(Control):

    def __init__(self, font=u'AncientPix', font_size=9, default_attrib={}, *args, **kwargs):
        Control.__init__(self, can_focus=True, *args, **kwargs)

        width, height = self.width, self.height

        self.document = pyglet.text.document.FormattedDocument(u'')
        self.default_attrib = dict(
            font_size=font_size,
            font_name=font,
            bold=False,
            italic=False,
            underline=None,
            color=(0, 0, 0, 255),
            shadow=(0, 0, 0, 0, 0),
        )

        self.default_attrib.update(default_attrib)

        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width-8, height-8, multiline=True
        )

        self.layout.x = 4
        self.layout.y = 4

        self.pos_table = []
        self.loc_table = []

        self._text = u''

        self.caret = pyglet.text.caret.Caret(self.layout)

        self.set_handlers(self.caret)
        self.push_handlers(self)

        from base.baseclasses import main_window
        self.window = main_window
        self.text_cursor = self.window.get_system_mouse_cursor('text')
        self.on_lostfocus()

    def _gettext(self):
        return self._text

    def _settext(self, text):
        self._text = u''
        self.pos_table = []
        self.loc_table = []
        self.caret.mark = None
        l = self.layout
        l.begin_update()
        self.document.text = u''
        self.append(text)
        # l.end_update()  # self.append(text) will call it

    def append(self, text):
        attrib = dict(self.default_attrib)
        doc = self.document
        pos = len(self._text)

        def set_attrib(entry, val):
            def scanner_cb(s, tok):
                attrib[entry] = val
            return scanner_cb

        def shadowed_text(val):
            def scanner_cb(s, tok):
                attrib['color'] = (255, 255, 255, 255)
                attrib['shadow'] = (2, ) + val
            return scanner_cb

        def restore(s, tok):
            attrib.update(self.default_attrib)

        def instext(s, tok):
            tok = unicode(tok)
            if s:
                self.pos_table.append(pos + s.match.start())
            else:
                self.pos_table.append(pos + len(text) - len(tok))
            self.loc_table.append(len(doc.text))
            doc.insert_text(len(doc.text), tok, attrib)

        def color(s, tok):
            c = tok[2:]
            color = (
                int(c[0:2], 16),
                int(c[2:4], 16),
                int(c[4:6], 16),
                int(c[6:8], 16),
            )
            attrib['color'] = color

        def shadow(s, tok):
            c = tok[3:]
            shadow = (
                int(tok[2]),
                int(c[0:2], 16),
                int(c[2:4], 16),
                int(c[4:6], 16),
                int(c[6:8], 16),
            )
            attrib['shadow'] = shadow

        def hidden(s, tok):
            color(s, '|c000000ff')
            shadow(s, '|s2000000ff')

        def insert_pipe(s, tok):
            instext(s, '|')

        import re
        scanner = re.Scanner([
            (r'[^|]+', instext),
            (r'\|c[A-Fa-f0-9]{8}', color),
            (r'\|s[12][A-Fa-f0-9]{8}', shadow),
            (r'\|B', set_attrib('bold', True)),
            (r'\|b', set_attrib('bold', False)),
            (r'\|I', set_attrib('italic', True)),
            (r'\|i', set_attrib('italic', False)),
            (r'\|U', set_attrib('underline', (0, 0, 0, 255))),
            (r'\|u', set_attrib('underline', None)),
            (r'\|H', hidden),
            (r'\|\|', insert_pipe),
            (r'\|r', restore),

            # shortcuts
            (r'\|R', set_attrib('color', (0xff, 0x35, 0x35, 0xff))),
            (r'\|G', set_attrib('color', (0x20, 0x80, 0x20, 0xff))),
            (r'\|Y', set_attrib('color', (0xff, 0xff, 0x30, 0xff))),
            (r'\|LB', set_attrib('color', (0x90, 0xdc, 0xe8, 0xff))),
            (r'\|DB', set_attrib('color', (0x00, 0x00, 0x60, 0xff))),
            (r'\|W', set_attrib('color', (0xff, 0xff, 0xff, 0xff))),

            # for thbviewer
            (r'\|!R', shadowed_text((0xff, 0x35, 0x35, 0xff))),
            (r'\|!G', shadowed_text((0x20, 0x80, 0x20, 0xff))),
            (r'\|!O', shadowed_text((0xff, 0xcc, 0x77, 0xff))),
            (r'\|!B', shadowed_text((0x00, 0x00, 0x60, 0xff))),
        ])

        l = self.layout

        bottom = (-l.view_y + l.height >= l.content_height)
        view_y = l.view_y

        l.begin_update()
        toks, reminder = scanner.scan(text)
        if reminder:
            instext(None, reminder)

        l.end_update()
        if bottom:
            l.view_y = -l.content_height
        else:
            l.view_y = view_y
        self._text += text

    text = property(_gettext, _settext)

    def draw(self):
        self.layout.draw()

    def on_mouse_scroll(self, x, y, dx, dy):
        f = self.document.get_font(0)
        size = f.ascent - f.descent
        self.layout.view_y += dy * size*2

    def on_focus(self):
        self.focused = True
        self.caret.visible = False

    def on_lostfocus(self):
        self.caret.visible = False
        self.caret.mark = None
        self.focused = False

    def on_mouse_enter(self, x, y):
        self.window.set_mouse_cursor(self.text_cursor)

    def on_mouse_leave(self, x, y):
        self.window.set_mouse_cursor(None)

    def on_mouse_drag(self, x, y, dx, dy, btn, modifier):
        # If I'm not focused, don't select texts
        if btn == mouse.LEFT and self.focused:
            x = max(4, x)
            self.caret.on_mouse_drag(x, y, dx, dy, btn, modifier)
        return pyglet.event.EVENT_HANDLED

    def on_mouse_press(self, x, y, btn, modifier):
        self.set_capture('on_mouse_release', 'on_mouse_drag')

    def on_mouse_release(self, x, y, btn, modifier):
        self.release_capture('on_mouse_release', 'on_mouse_drag')
        return True

    def on_key_press(self, symbol, modifiers):
        def get_pos(loc, left=True):
            import bisect
            if left:
                bisect = bisect.bisect_left
            else:
                bisect = bisect.bisect_right

            idx = bisect(self.loc_table, loc) - 1
            if idx < 0: idx = 0

            loc_diff = loc - self.loc_table[idx]

            return self.pos_table[idx] + loc_diff, idx

        if modifiers & KEYMOD_MASK == key.MOD_CTRL:
            if symbol == key.A:
                self.caret.position = 0
                self.caret.mark = len(self.text)
                return pyglet.event.EVENT_HANDLED

            elif symbol == key.C:
                start = self.layout.selection_start
                end = self.layout.selection_end
                if start != end:
                    pyperclip.copy(self.document.text[start:end])
                return pyglet.event.EVENT_HANDLED

        elif modifiers & KEYMOD_MASK == (key.MOD_CTRL | key.MOD_SHIFT):
            if symbol == key.C:
                start = get_pos(self.layout.selection_start)[0]
                end = get_pos(self.layout.selection_end)[0]
                if start != end:
                    pyperclip.copy(self.text[start:end])
                return pyglet.event.EVENT_HANDLED

        return pyglet.event.EVENT_HANDLED

    def on_text(self, text):
        return pyglet.event.EVENT_HANDLED

    def on_text_motion(self, motion):
        if motion == key.MOTION_DELETE or motion == key.MOTION_BACKSPACE:
            return pyglet.event.EVENT_HANDLED

    @property
    def content_height(self):
        return self.layout.content_height + 8

    def on_resize(self, width, height):
        l = self.layout
        l.begin_update()
        l.width, l.height = width - 8, height - 8
        l.end_update()


class ListItem(object):
    def __init__(self, p, i, color=(0, 0, 0, 255)):
        self.parent = p
        self.color = color
        n = len(p.columns)
        self.labels = [None] * n
        self._data = [''] * n
        self.idx = i

    def _set_data(self, val):
        val = list(val)
        p = self.parent
        n = len(p.columns)
        val = (val + n*[''])[:n]
        for i, v in enumerate(val):
            self[i] = unicode(v)
        self._update_labels()

    def _get_data(self):
        return self._data

    data = property(_get_data, _set_data)

    def _update_labels(self):
        p = self.parent
        p.need_refresh = True
        ox = 2
        for (_, w), lbl in zip(p.columns, self.labels):
            lbl.begin_update()
            lbl.x, lbl.y = ox, -2 - self.idx * self.parent.line_height
            lbl.color = self.color
            lbl.end_update()
            ox += w

    def __getitem__(self, index):
        if isinstance(index, basestring):
            index = self.parent.col_lookup[index]
        return self._data[index]

    def __setitem__(self, index, val):
        from pyglet.text import Label
        p = self.parent
        if isinstance(index, basestring):
            index = p.col_lookup[index]
        self._data[index] = val
        c = p.color.text + (255,)
        o = self.labels[index]
        if o: o.delete()
        self.labels[index] = Label(
            text=val, font_name='AncientPix', font_size=9,
            anchor_x='left', anchor_y='top', color=c,
            batch=p.batch,
        )


class ListHeader(object):
    def __init__(self, p):
        self.parent = p
        from pyglet.text import Label
        cols = p.columns
        batch = pyglet.graphics.Batch()
        _x = 2
        c = p.color.heavy + (255,)
        for name, width in cols:
            Label(
                name, anchor_x='left', anchor_y='bottom',
                x=_x, y=5, color=c, font_name='AncientPix', font_size=12,
                batch=batch
            )
            _x += width
        self.batch = batch

    def draw(self):
        p = self.parent
        c = [i/255.0 for i in p.color.light]
        glColor3f(*c)
        glRectf(0, 0, p.width, p.header_height)
        c = [i/255.0 for i in p.color.heavy]
        glColor3f(*c)
        glBegin(GL_LINES)
        glVertex2f(0, 0)
        glVertex2f(p.width, 0)
        glEnd()
        self.batch.draw()


class ListView(Control):
    li_class = ListItem
    lh_class = ListHeader
    header_height = 25
    line_height = 17

    def __init__(self, color=Colors.green, *a, **k):
        Control.__init__(self, *a, **k)
        self.color = color
        self.items = []
        self.columns = []
        self.col_lookup = {}
        self._view_y = 0
        self.batch = pyglet.graphics.Batch()
        self.cur_select = None
        self.need_refresh = True

    def set_columns(self, cols):
        # [('name1', 20), ('name2', 30)]
        self.columns = list(cols)
        self.col_lookup = {
            name: index
            for index, (name, width) in enumerate(cols)
        }
        self.header = self.lh_class(self)
        self.header.data = [n for n, w in cols]

    def append(self, val, color=(0, 0, 0, 255)):
        if isinstance(val, ListItem):
            li = val
            li.parent = self
        elif isinstance(val, (list, tuple)):
            li = self.li_class(self, len(self.items))
            li.color = color
            li.data = val
        self.items.append(li)
        return li

    def clear(self):
        self.items = []
        self.cur_select = None
        self.batch = pyglet.graphics.Batch()

    def _set_view_y(self, val):
        sum_h = len(self.items) * self.line_height
        h = self.height - self.header_height
        if val < 0: val = 0
        bot_lim = max(sum_h - h, 0)
        if val > bot_lim: val = bot_lim
        self._view_y = val

    def _get_view_y(self):
        return self._view_y

    view_y = property(_get_view_y, _set_view_y)

    def draw(self):
        glColor3f(1, 1, 1)

        hh = self.header_height
        client_height = self.height - hh
        vy = self.view_y

        # glPushMatrix()
        glTranslatef(0, client_height + vy, 0)
        glEnable(GL_SCISSOR_TEST)
        ax, ay = self.abs_coords()
        ax, ay, w, h = map(int, (ax, ay, self.width, client_height))
        glScissor(ax, ay, w, h)
        self.batch.draw()
        cs = self.cur_select
        if cs is not None:
            c = Colors.get4f(self.color.light)
            glColor4f(c[0], c[1], c[2], 0.5)
            glRectf(
                0, -16-cs*self.line_height,
                self.width, -cs*self.line_height
            )
        glDisable(GL_SCISSOR_TEST)
        glTranslatef(0, -vy, 0)
        self.header.draw()

        # glPopMatrix()

    def on_mouse_scroll(self, x, y, dx, dy):
        self.view_y -= dy * 40
        self.need_refresh = True

    def _mouse_click(self, evt_type, x, y, button, modifier):
        h = self.height - self.header_height
        lh, vy = self.line_height, self.view_y
        i = (h + vy - y) / lh
        n = len(self.items)
        if 0 <= i < n:
            # cs = self.cur_select
            # if cs is not None and 0 <= cs < n:
            #     item = self.items[cs]
            self.dispatch_event(evt_type, self.items[i])
            self.cur_select = i
            # item = self.items[i]
            self.need_refresh = True

    on_mouse_click = lambda self, *a: self._mouse_click('on_item_select', *a)
    on_mouse_dblclick = lambda self, *a: self._mouse_click('on_item_dblclick', *a)

ListView.register_event_type('on_item_select')
ListView.register_event_type('on_item_dblclick')


class ProgressBar(Control):
    value = InterpDesc('_value')

    def __init__(self, *a, **k):
        Control.__init__(self, *a, **k)
        self.value = 1.0
        self.height = self.pic_frame[0].height

    def _drawit(self, x, y, w, l, m, r):
        wl, wr = l.width, r.width
        if wl + wr < w:
            l.blit_nobind(x, y)
            r.blit_nobind(x + w - wr, y)
            m.get_region(0, 0, w - wl - wr, m.height).blit_nobind(x + wl, y)
        else:
            w /= 2
            l.get_region(0, 0, w, l.height).blit_nobind(x, y)
            _x = r.width - w
            r.get_region(_x, 0, w, r.height).blit_nobind(x + w, y)

    def draw(self):
        value = self.value
        width = self.width

        glColor3f(1, 1, 1)
        tex = self.pic_frame[0].owner
        with tex:
            self._drawit(0, 0, width, *self.pic_frame)
            w = (width - self.core_w_correct) * value
            if w: self._drawit(self.offs_x, self.offs_y, w, *self.pic_core)


class BigProgressBar(ProgressBar):
    offs_x, offs_y = 9, 9
    core_w_correct = 18

    @property
    def pic_frame(self):
        return [
            L('c-pbar-bfl'),
            L('c-pbar-bfm'),
            L('c-pbar-bfr'),
        ]

    @property
    def pic_core(self):
        return [
            L('c-pbar-bl'),
            L('c-pbar-bm'),
            L('c-pbar-br'),
        ]


class SmallProgressBar(ProgressBar):
    offs_x, offs_y = 8, 8
    core_w_correct = 16

    @property
    def pic_frame(self):
        return [
            L('c-pbar-sfl'),
            L('c-pbar-sfm'),
            L('c-pbar-sfr'),
        ]

    @property
    def pic_core(self):
        return [
            L('c-pbar-sl'),
            L('c-pbar-sm'),
            L('c-pbar-sr'),
        ]


class ButtonArray(Control):
    def __init__(self, buttons=((u'确定', True), (u'取消', False)),
                 color=Colors.green, delay=0, min_width=0, *a, **k):
        Control.__init__(self, *a, **k)
        self.buttons = bl = []
        self.min_width = min_width

        wl = self._get_widths(buttons)

        loc = 0
        for p, v in buttons:
            w = wl.pop(0)
            btn = Button(
                parent=self, x=loc, y=0,
                width=w, height=24,
                caption=p, color=color,
            )
            btn.retval = v

            @btn.event
            def on_click(btn=btn):
                self.on_button_click(btn)

            bl.append(btn)
            loc += w + 6

        if delay:
            self.disable()
            gevent.spawn_later(delay, self.enable)

        self.width, self.height = loc - 6, 24

    def on_button_click(self, btn, v):
        pass

    def draw(self):
        self.draw_subcontrols()

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

    def update(self):
        for b in self.buttons:
            b.update()

    def disable(self):
        for b in self.buttons:
            b.state = Button.DISABLED

    def enable(self):
        for b in self.buttons:
            b.state = Button.NORMAL

    def _get_widths(self, buttons):
        w = self.min_width
        wl = [max(len(b[0]) * 16 + 20, w) for b in buttons]
        return wl

    def calc_width(self, buttons):
        wl = self._get_widths(buttons)
        n = len(wl)
        return sum(wl) + (n-1)*6


class OptionButtonGroup(ButtonArray):
    def __init__(self, buttons, delay=0, *a, **k):
        ButtonArray.__init__(self, buttons, color=Colors.blue, delay=delay, *a, **k)
        self.value = buttons[0][1]
        self.buttons[0].color = Colors.orange

    def on_button_click(self, btn):
        self.dispatch_event('on_option', btn.retval)

    def on_option(self, v):
        self.set_value(v)

    def set_value(self, v):
        for b in self.buttons:
            b.color = Colors.blue

        for b in self.buttons:
            if b.retval == v:
                self.value = v
                b.color = Colors.orange
                break
        else:
            raise ValueError


OptionButtonGroup.register_event_type('on_option')


class ConfirmButtons(ButtonArray):
    def __init__(self, *a, **k):
        k.setdefault('min_width', 80)
        ButtonArray.__init__(self, *a, **k)

    def on_button_click(self, btn):
        self.value = btn.retval
        self.dispatch_event('on_confirm', self.value)

ConfirmButtons.register_event_type('on_confirm')


class ConfirmBox(Dialog):
    class Presets:
        OK       = ((u'确定', True), )
        OKCancel = ((u'确定', True), (u'取消', False))

    _default_value = object()

    def __init__(self, text=u'Yoo~', caption=u'信息',
                 buttons=Presets.OK, default=_default_value, *a, **k):
        Dialog.__init__(
            self, caption, width=300,
            bot_reserve=33, *a, **k
        )

        lbl = self.add_label(
            text, 0, 33 + 20, anchor_x='center', anchor_y='bottom',
            font_size=9, width=10000, multiline=True, color=(0, 0, 0, 255)
        )
        self.confirm_btns = btn = ConfirmButtons(buttons, parent=self, color=self.color)
        self.value = buttons[0][1] if default is self._default_value else default

        @btn.event
        def on_confirm(val):
            self.value = val
            self.delete()

        w, h = lbl.content_width + 1, lbl.content_height
        dw, dh = max(w, btn.calc_width(buttons))+50, h+24+33+20*2
        self.width, self.height = dw, dh
        lbl.begin_update()
        lbl.width = w
        self.set_label_position(lbl, dw//2, 33 + 20)
        lbl.end_update()

        p = self.parent
        pw, ph = p.width, p.height
        self.set_position((pw - dw)/2, (ph - dh)/2)

        btn.x, btn.y = (dw - btn.width)/2, 5

    def delete(self):
        self.dispatch_event('on_confirm', self.value)
        Dialog.delete(self)

    def on_move(self, x, y):
        self.confirm_btns.update()


ConfirmBox.register_event_type('on_confirm')


class LoadingWindow(Dialog):
    def __init__(self, text=u'Yoo~', caption=u'请稍候...',
                 *a, **k):
        Dialog.__init__(
            self, caption, width=300, bot_reserve=0, *a, **k
        )

        self._done = False
        self.btn_close.delete()

        lbl = self.add_label(
            text, 0, 20, anchor_x='center', anchor_y='bottom',
            font_size=9, width=10000, multiline=True, color=(0, 0, 0, 255)
        )

        w, h = lbl.content_width + 1, lbl.content_height
        dw, dh = w+50, h+24+20*2
        self.width, self.height = dw, dh
        lbl.begin_update()
        lbl.width = w
        self.set_label_position(lbl, dw//2, 20)
        lbl.end_update()

        p = self.parent
        pw, ph = p.width, p.height
        self.set_position((pw - dw)/2, (ph - dh)/2)

    def done(self):
        if not self._done:
            self._done = True
            self.delete()

    def is_done(self):
        return self._done

    def on_move(self, x, y):
        pass


class Panel(Control):
    fill_color = (1.0, 1.0, 0.8, 0.0)

    def __init__(self, color=Colors.green, *a, **k):
        Control.__init__(self, *a, **k)
        self.color = color
        self.tick = 0
        self.update()

    def update(self):
        w, h = int(self.width), int(self.height)

        from .base.shader import HAVE_SHADER
        if HAVE_SHADER:
            blurtex = pyglet.image.Texture.create(w, h)

            self.blurtex = blurtex

            t = blurtex.tex_coords
            x1 = 0
            y1 = 0
            x2 = blurtex.width
            y2 = blurtex.height

            array = (GLfloat * 32)(
                t[0],  t[1],  t[2],  1.,
                x1,    y1,    0,     1.,
                t[3],  t[4],  t[5],  1.,
                x2,    y1,    0,     1.,
                t[6],  t[7],  t[8],  1.,
                x2,    y2,    0,     1.,
                t[9],  t[10], t[11], 1.,
                x1,    y2,    0,     1.,
            )
            self._blurtex_array = array
        else:
            self.blurtex = None

    def draw(self):
        blurtex = self.blurtex
        w, h = int(self.width), int(self.height)

        if blurtex:
            from shaders import GaussianBlurHorizontal as GBH, GaussianBlurVertical as GBV, ShaderProgram

            ax, ay = self.abs_coords()
            ax, ay = int(ax), int(ay)

            t = getattr(blurtex, 'owner', blurtex)
            _w, _h = t.width, t.height

            glColor3f(1, 1, 1)

            glEnable(blurtex.target)
            glPushClientAttrib(GL_CLIENT_VERTEX_ARRAY_BIT)
            glInterleavedArrays(GL_T4F_V4F, 0, self._blurtex_array)
            glBindTexture(blurtex.target, blurtex.id)

            glCopyTexImage2D(blurtex.target, 0, GL_RGBA, ax, ay, _w, _h, 0)
            GBV.use()
            GBV.uniform.size = (_w, _h)
            glDrawArrays(GL_QUADS, 0, 4)

            glCopyTexImage2D(blurtex.target, 0, GL_RGBA, ax, ay, _w, _h, 0)
            GBH.use()
            GBH.uniform.size = (_w, _h)
            glDrawArrays(GL_QUADS, 0, 4)

            ShaderProgram.restore()

            glBindTexture(blurtex.target, 0)
            glPopClientAttrib()
            glDisable(blurtex.target)

        c = self.fill_color
        if c[3] != 0.0:
            glColor4f(*c)
            glRectf(0, 0, w, h)

        glLineWidth(3.0)
        glColor4f(1, 1, 1, .3)
        glRectf(1.5, 1.5, -1.5+w, -1.5+h)
        glColor3f(*[i/255.0 for i in self.color.frame])
        glRectf(-1.5+w, 1.5, 1.5, -1.5+h)
        glLineWidth(1.0)

        self.draw_subcontrols()


class ImageSelector(Control):
    hover_alpha = InterpDesc('_hover_alpha')

    def __init__(self, image, group, hover_pic=None, *a, **k):
        Control.__init__(
            self, width=145, height=98,
            *a, **k
        )

        self.selected = False
        self.disabled = False
        self.hover_alpha = 0.0
        self.image = image
        self.group = group
        self.balloon = BalloonPrompt(self)
        self.hover_pic = hover_pic

    def on_mouse_enter(self, x, y):
        self.hover_alpha = 0.4

    def on_mouse_leave(self, x, y):
        self.hover_alpha = LinearInterp(
            0.4, 0, 0.3
        )

    def on_mouse_click(self, x, y, button, modifier):
        if self.disabled: return
        for gs in self.group:
            gs.selected = False
        self.selected = True
        self.dispatch_event('on_select')

    def on_mouse_dblclick(self, x, y, button, modifier):
        if self.disabled: return
        self.dispatch_event('on_dblclick')

    def draw(self):
        glColor3f(1, 1, 1)
        if self.disabled:
            self.image.grayed.blit(0, 0)
        else:
            self.image.blit(0, 0)

        glColor3f(0.757, 1.0, 0.384)
        glRectf(0, self.height, self.width, 0)

        if self.selected:
            L('c-imagesel_shine').blit(-11, -11)

        a = self.hover_alpha
        if a:
            if self.hover_pic:
                glColor4f(1, 1, 1, a)
                self.hover_pic.blit(0, 0)
            else:
                glColor4f(1, 1, 0.8, a)
                glRectf(0, 0, self.width, self.height)

    def disable(self):
        self.disabled = True
        self.selected = False

    def enable(self):
        self.disabled = False

    @staticmethod
    def get_selected(group):
        for c in group:
            if c.selected:
                return c
        return None

ImageSelector.register_event_type('on_select')
ImageSelector.register_event_type('on_dblclick')


class SensorLayer(Control):
    def __init__(self, parent, *a, **k):
        Control.__init__(
            self, parent=parent, x=0, y=0,
            width=parent.width, height=parent.height,
            *a, **k
        )


class VolumeTuner(Control):
    def __init__(self, *a, **k):
        Control.__init__(self, width=32, height=32, zindex=99999, *a, **k)
        balloon = BalloonPrompt(self)
        balloon.set_balloon(
            u'|DB调节音量的图标|r\n'
            u'\n'
            u'单击切换静音和有声音\n'
            u'鼠标滚轮调整BGM音量大小\n'
            u'按住Ctrl+鼠标滚轮调整效果音大小'
        )

    def draw(self):
        glColor4f(1, 1, 1, 1)
        bgm_volume = L('c-bgm_volume')
        with bgm_volume.owner:
            from client.ui.soundmgr import SoundManager
            if SoundManager.muted:
                vol_mute = L('c-vol_mute')
                glColor4f(1, 1, 1, 1)
                vol_mute.blit_nobind(0, 0)
            else:
                se_volume = L('c-se_volume')
                vol_icon = L('c-vol_icon')
                glColor4f(1, 1, 1, SoundManager.bgm_volume)
                bgm_volume.blit_nobind(0, 0)
                glColor4f(1, 1, 1, SoundManager.se_volume)
                se_volume.blit_nobind(0, 0)
                glColor4f(1, 1, 1, 1)
                vol_icon.blit_nobind(0, 0)

    def on_mouse_click(self, x, y, button, modifier):
        from client.ui.soundmgr import SoundManager
        if SoundManager.muted:
            SoundManager.unmute()
        else:
            SoundManager.mute()

    def on_mouse_scroll(self, x, y, dx, dy):
        from client.ui.soundmgr import SoundManager
        key_state = self.overlay.key_state

        is_se = key_state[key.LCTRL] or key_state[key.RCTRL]

        vol = SoundManager.se_volume if is_se else SoundManager.bgm_volume
        vol += 0.1 * dy / abs(dy)
        vol = min(1.0, vol)
        vol = max(0.0, vol)

        if vol:
            SoundManager.unmute()
            if is_se:
                SoundManager.se_volume = vol
            else:
                SoundManager.bgm_volume = vol


class OptionButton(Button):
    Conf = namedtuple('OptionButtonConfiguration', 'caption color value')
    DEFAULT_CONF = (
        (u'关闭', Colors.blue, False),
        (u'打开', Colors.orange, True),
    )
    _DEFAULT = object()

    def __init__(self, conf=None, value=_DEFAULT, *a, **k):
        self.conf = conf = [self.Conf(*i) for i in conf or self.DEFAULT_CONF]
        self.confidx = confidx = {c.value: i for i, c in enumerate(conf)}
        i = confidx.get(value, conf[0].value)
        self.index = i
        c = conf[i]
        self._value = c.value
        Button.__init__(self, c.caption, c.color, *a, **k)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if value == self._value:
            return

        self._value = value
        self.option_update()
        self.dispatch_event('on_value_changed', value)

    def option_update(self):
        i = self.confidx[self.value]
        c = self.conf[i]
        self.caption = c.caption
        self.color = c.color
        self.index = i
        self.update()

    def on_click(self):
        i = (self.index + 1) % len(self.conf)
        self.index = i
        self.value = self.conf[i].value

OptionButton.register_event_type('on_value_changed')


class NoInviteButton(OptionButton):
    def __init__(self, *a, **k):
        from user_settings import UserSettings
        conf = (
            (u'邀请已关闭', Colors.blue,   True),
            (u'邀请已开启', Colors.orange, False),
        )
        OptionButton.__init__(self, conf=conf, value=UserSettings.no_invite, *a, **k)
        UserSettings.setting_change += self

    def __call__(self, k, v):
        if k == 'no_invite':
            self.value = v

    def on_value_changed(self, value):
        from user_settings import UserSettings as us
        us.no_invite = value

    def delete(self):
        from user_settings import UserSettings
        UserSettings.setting_change -= self
        OptionButton.delete(self)


class CheckBox(Control):
    def __init__(self, value=False, *a, **k):
        conf = (
            (u'', Colors.blue, False),
            (u'', Colors.orange, True),
        )
        Control.__init__(self, width=28, height=22, *a, **k)

        self.label = label = pyglet.text.Label(
            self.caption, u'AncientPix', 9,
            color=(0, 0, 0, 255),
            x=24, y=2,
            anchor_x='left', anchor_y='bottom',
        )

        self.width = 30 + label.content_width

        self.opt = OptionButton(
            parent=self, conf=conf, x=0, y=0,
            width=16, height=16, value=value
        )
        self.image = L('c-check')

        sensor = SensorLayer(self, zindex=1)
        sensor.event(self.opt.on_mouse_enter)
        sensor.event(self.opt.on_mouse_leave)
        sensor.event(self.opt.on_mouse_click)
        sensor.event(self.opt.on_mouse_press)
        sensor.event(self.opt.on_mouse_release)

    @property
    def value(self):
        return self.opt.value

    def draw(self):
        self.draw_subcontrols()
        if self.opt.value:
            a = 1 - self.opt.hover_alpha
        else:
            a = 2 * self.opt.hover_alpha
        glColor4f(1, 1, 1, a)
        self.image.blit(-4, -3)
        self.label.draw()
