# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import Control
from client.ui.base.interp import *
from client.ui import resource as common_res, ui_utils
from utils import Rect, ScissorBox

from math import ceil

import logging
log = logging.getLogger('UI_Controls')

class Button(Control):
    NORMAL=0
    HOVER=1
    PRESSED=2
    DISABLED=3

    def __init__(self, caption='Button', font_name='Arial', font_size=9, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.caption = caption
        self.font_name = font_name
        self.font_size = font_size
        self.state = Button.NORMAL
        self.label = pyglet.text.Label(caption, font_name, font_size,
                                       color=(0,0,0,255),
                                       x=self.width//2, y=self.height//2,
                                       anchor_x='center', anchor_y='center')
        self.color_now = (0.0, 0.0, 0.0)

    def draw(self, dt):
        srccolor = self.color_now
        dstcolor = (
            (0.8, 0.8, 0.8),
            (0.5, 0.5, 0.5),
            (0.2, 0.2, 0.2),
            (1.0, 0.2, 0.2),
        )[self.state]
        anim_time = 0.17
        cur_time = 0.0
        while anim_time - cur_time > 0:
            cur_time += dt
            delta = [(dst - cur)*(dt/anim_time) for cur, dst in zip(srccolor, dstcolor)]
            self.color_now = [
                (now+dc if (dst-now-dc)*(dst-now)>0 else dst)
                for now, dst, dc in zip(self.color_now, dstcolor, delta)
            ]
            glPushAttrib(GL_POLYGON_BIT)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glColor3f(*self.color_now)
            glRecti(0, 0, self.width, self.height)
            glPopAttrib()
            self.label.draw()
            #self.draw_subcontrols()
            dt = (yield)

    def on_mouse_enter(self, x, y):
        if self.state != Button.DISABLED:
            self.state = Button.HOVER
            self.stop_drawing()

    def on_mouse_leave(self, x, y):
        if self.state != Button.DISABLED:
            self.state = Button.NORMAL
            self.stop_drawing()

    def on_mouse_press(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            if button == mouse.LEFT:
                self.state = Button.PRESSED
                self.stop_drawing()

    def on_mouse_release(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            if button == mouse.LEFT:
                self.state = Button.HOVER
                self.stop_drawing()

    def on_mouse_click(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            self.dispatch_event('on_click')

Button.register_event_type('on_click')

class Dialog(Control):
    '''
    Dialog, can move
    '''
    next_zindex = 1
    def __init__(self, caption='Dialog', *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.zindex = Dialog.next_zindex
        Dialog.next_zindex += 1
        self.label = pyglet.text.Label(caption, 'Arial', 9,
                               color=(0,0,0,255),
                               x=self.width//2, y=self.height-8,
                               anchor_x='center', anchor_y='center')
        self.btn_close = Button(caption=u'', parent=self, font_size=12,
                                x=self.width-20, y=self.height-19,
                                width=19, height=19, manual_draw=True)
        self.dragging = False
        @self.btn_close.event
        def on_click():
            self.close()

    def on_resize(self, width, height):
        self.label.x = width // 2
        self.label.y = height - 8
        self.btn_close.x = width - 20
        self.btn_close.y = height - 19

    def draw(self, dt):
        w, h = self.width, self.height
        ax, ay = self.abs_coords()
        ax, ay = int(ax), int(ay)

        ob = (GLint*4)()
        glGetIntegerv(GL_SCISSOR_BOX, ob)
        ob = list(ob)
        nb = Rect(*ob).intersect(Rect(ax, ay, w, h))
        if nb:
            glScissor(nb.x, nb.y, nb.width, nb.height)
            glClear(GL_COLOR_BUFFER_BIT)
            if nb.height > 21:
                glScissor(nb.x, nb.y, nb.width, nb.height-20)
                self.draw_subcontrols(dt)
            glScissor(*ob)

        glColor3f(0, 0, 0)
        self.label.draw()
        self.btn_close.do_draw(dt)
        glColor3f(0, 0, 0)
        glPushAttrib(GL_POLYGON_BIT)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRecti(0, 0, w, h)
        graphics.draw(5, GL_LINE_STRIP,('v2i', (
            0, h-20,
            w, h-20,
            w-20, h,
            w-20, h-20,
            w, h,
        )))
        glPopAttrib()

    def on_mouse_press(self, x, y, button, modifier):
        w, h = self.width, self.height
        self.zindex = Dialog.next_zindex
        Dialog.next_zindex += 1
        if button == mouse.LEFT and h-20 <= y <= h and x <= w-20:
            self.set_capture('on_mouse_drag', 'on_mouse_release')
            self.dragging = True

    def on_mouse_release(self, x, y, button, modifier):
        if self.dragging:
            self.release_capture('on_mouse_drag', 'on_mouse_release')
            self.dragging = False

    def on_mouse_drag(self, x, y, dx, dy, button, modifier):
        if self.dragging:
            self.x += dx
            self.y += dy
            self.dispatch_event('on_move', self.x, self.y)

    def close(self):
        self._cancel_close = False
        self.dispatch_event('on_close')
        if not self._cancel_close:
            self.delete()
            self.dispatch_event('on_destroy')

    def cancel_close(self):
        self._cancel_close = True

Dialog.register_event_type('on_move')
Dialog.register_event_type('on_close')
Dialog.register_event_type('on_destroy')

class TextBox(Control):
    def __init__(self, font='Arial', font_size=12, text='Yoooooo~', *args, **kwargs):
        Control.__init__(self, can_focus=True, *args, **kwargs)
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.document.set_style(0, len(self.document.text), dict(
                color=(0, 0, 0, 255),
                font_name=font,
                font_size=font_size,
        ))

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
        self.focused = False

    def _gettext(self):
        return self.document.text

    def _settext(self, text):
        self.document.text = text

    text = property(_gettext, _settext)

    def draw(self, dt):
        '''
        glPushAttrib(GL_POLYGON_BIT)
        glColor3f(1.0, 1.0, 1.0)
        glRecti(0, 0, self.width, self.height)
        glColor3f(0.0, 0.0, 0.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRecti(0, 0, self.width, self.height)
        glPopAttrib()'''
        ui_utils.border(0, 0, self.width, self.height)
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
        if not self.focused:
            return pyglet.event.EVENT_HANDLED

    #def on_key_press(...): #handle Ctrl+C Ctrl+V Ctrl+A
    def on_text(self, text):
        from pyglet.window import key
        if text == '\r': # Why this??
            self.dispatch_event('on_enter')
            return pyglet.event.EVENT_HANDLED

TextBox.register_event_type('on_enter')

class PlayerPortrait(Control):
    def __init__(self, player_name, color=[0,0,0], *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.width, self.height = 128, 245
        self.player_name = player_name
        self.color = color
        self.refresh()

    def refresh(self):
        from pyglet.text import Label
        self.batch = pyglet.graphics.Batch()
        self.label = Label(
            text=self.player_name, font_size=9, bold=True, color=(0,0,0,255),
            x=128//2, y=245//2, anchor_x='center', anchor_y='center',
            batch=self.batch
        )
        r = Rect(0, 0, 128, 245)
        self.batch.add(
            5, GL_LINE_STRIP, None,
            ('v2i', r.glLineStripVertices()),
            ('c3i', self.color * 5)
        )

    def draw(self, dt):
        self.batch.draw()

class GameCharacterPortrait(Control):
    def __init__(self, name='Proton', *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 149, 195
        self.name = pyglet.text.Label(
            text=name, font_size=9,
            x=9, y=175, anchor_x='left', anchor_y='bottom'
        )
        self.selected = False
        self.maxlife = 8
        self.life = 0

    def draw(self, dt):
        glColor3f(1, 1, 1)
        common_res.char_portrait.blit(0, 0)
        if self.selected:
            glColor4f(1, 1, 1, .3)
            glRecti(0, 0, self.width, self.height)
        self.name.draw()

        hp, hp_bg = common_res.hp, common_res.hp_bg

        tw, th = self.maxlife, 1
        vw, vh = hp_bg.width * self.maxlife, hp_bg.height

        glPushMatrix()
        glTranslatef(5., 55., 0)

        glEnable(hp_bg.target)
        glBindTexture(hp_bg.target, hp_bg.id)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(tw, 0); glVertex2f(vw, 0)
        glTexCoord2f(tw, th); glVertex2f(vw, vh)
        glTexCoord2f(0, th); glVertex2f(0, vh)
        glEnd()
        #glDisable(hp_bg.target) # both GL_TEXTURE_2D, save the calls

        tw, th = self.life, 1
        vw, vh = hp.width * self.life, hp.height
        #glEnable(hp.target)
        glBindTexture(hp.target, hp.id)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(tw, 0); glVertex2f(vw, 0)
        glTexCoord2f(tw, th); glVertex2f(vw, vh)
        glTexCoord2f(0, th); glVertex2f(0, vh)
        glEnd()
        glDisable(hp.target)
        glPopMatrix()

class TextArea(Control):
    def __init__(self, font='Arial', font_size=9, *args, **kwargs):
        Control.__init__(self, can_focus=True, *args, **kwargs)

        width, height = self.width, self.height

        self.document = doc = pyglet.text.document.FormattedDocument(u'')
        self.default_attrib = dict(
            font_size=font_size, font_name=font,
            bold=False, italic=False,
            underline=None, color=(0, 0, 0, 255),
        )

        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width-8, height-8, multiline=True)

        self.layout.x = 4
        self.layout.y = 4

        self._text = u''

    def _gettext(self):
        return self._text

    def _settext(self, text):
        self._text = u''
        self.document.text = u''
        self.append(text)

    def append(self, text):
        attrib = dict(self.default_attrib)
        doc = self.document

        def set_attrib(entry, val):
            def scanner_cb(s, tok):
                attrib[entry] = val
            return scanner_cb

        def restore(s, tok):
            attrib.update(self.default_attrib)

        def instext(s, tok):
            # *MEGA* HACK:
            # pyglet's layout won't snap long words,
            # and this is unacceptable for chinese characters!!!!
            # so inserting ZeroWidthSpace[ZWSP] here.
            tok = unicode(tok)
            tok = u'\u200b'.join(tok) + u'\u200b'
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

        def insert_pipe(s, tok):
            instext(s, '|')

        import re
        scanner = re.Scanner([
            (r'[^|]+', instext),
            (r'\|c[A-Fa-f0-9]{8}', color),
            (r'\|B', set_attrib('bold', True)),
            (r'\|b', set_attrib('bold', False)),
            (r'\|I', set_attrib('italic', True)),
            (r'\|i', set_attrib('italic', False)),
            (r'\|U', set_attrib('underline', (0,0,0,255))),
            (r'\|u', set_attrib('underline', None)),
            (r'\|\|', insert_pipe),
            (r'\|r', restore),
        ])

        self.layout.begin_update()
        toks, reminder = scanner.scan(text)
        if reminder:
            instext(None, reminder)
        # *MEGA* HACK:
        # make the ZeroWidthSpace(ZWSP) char invisible
        for start, end, font in doc.get_font_runs().ranges(0, 999999):
            zwsp = font.get_glyphs(u'\u200b')[0]
            zwsp.vertices = (0, 0, 0, 0)
            zwsp.advance = 0
        self.layout.end_update()
        self.layout.view_y = -self.layout.content_height
        self._text += text

    text = property(_gettext, _settext)

    def draw(self, dt):
        '''
        glPushAttrib(GL_POLYGON_BIT)
        glColor3f(1.0, 1.0, 1.0)
        glRecti(0, 0, self.width, self.height)
        glColor3f(0.0, 0.0, 0.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRecti(0, 0, self.width, self.height)
        glPopAttrib()'''
        ui_utils.border(0, 0, self.width, self.height)
        self.layout.draw()

    def on_mouse_scroll(self, x, y, dx, dy):
        f = self.document.get_font(0)
        size = f.ascent - f.descent
        self.layout.view_y += dy * size*2

class CardSprite(Control):
    x = InterpDesc('_x')
    y = InterpDesc('_y')
    shine_alpha = InterpDesc('_shine_alpha')
    alpha = InterpDesc('_alpha')
    img_shinesoft = common_res.card_shinesoft
    width, height = 91, 125
    def __init__(self, x=0.0, y=0.0, img=None, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 91, 125
        self.shine = False
        self.gray = False
        self.x, self.y,  = x, y
        self.shine_alpha = 0.0
        self.alpha = 1.0
        self.img = img

    def draw(self, dt):
        if self.gray:
            glColor4f(.66, .66, .66, self.alpha)
        else:
            glColor4f(1., 1., 1., self.alpha)
        self.img.blit(0, 0)
        glColor4f(1., 1., 1., self.shine_alpha)
        self.img_shinesoft.blit(-6, -6)

    def on_mouse_enter(self, x, y):
        self.shine_alpha = 1.0

    def on_mouse_leave(self, x, y):
        self.shine_alpha = SineInterp(1.0, 0.0, 0.3)

class HandCardArea(Control):
    width, height = 93*5+42, 145
    def __init__(self, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 93*5+42, 145

    def draw(self, dt):
        glColor4f(1,1,1,1)
        self.draw_subcontrols(dt)

    def update(self):
        n = len(self.control_list)
        width = min(5*93.0+42, n*93.0)
        step = (width - 91)/(n-1) if n > 1 else 0
        for i, c in enumerate(self.control_list):
            c.zindex = i
            try:
                sel = c.hca_selected
            except AttributeError:
                sel = c.hca_selected = False
            c.x = SineInterp(c.x, 2 + int(step * i), 0.3)
            c.y = SineInterp(c.y, 20 if sel else 0, 0.3)

    def on_mouse_click(self, x, y, button, modifier):
        c = self.control_frompoint1(x, y)
        if c:
            s = c.hca_selected = not c.hca_selected
            c.y = SineInterp(c.y, 20 if s else 0, 0.1)
            self.dispatch_event('on_selection_change')

    cards = property(
        lambda self: self.control_list,
        lambda self, x: setattr(self, 'control_list', x)
    )

HandCardArea.register_event_type('on_selection_change')

class DropCardArea(Control):
    width, height = 820, 125
    def __init__(self, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self._w, self._h = 820, 125

    def draw(self, dt):
        glColor4f(1,1,1,1)
        self.draw_subcontrols(dt)

    def update(self):
        for cs in self.control_list:
            try:
                if cs.dca_tag:
                    continue
            except AttributeError:
                pass

            cs.dca_tag = True
            cs.alpha = ChainInterp(
                FixedInterp(1.0, 3),
                CosineInterp(1.0, 0.0, 1),
                on_done=self._on_cardanimdone,
            )

        n = len(self.control_list)
        x = (820-n*93)/2
        step = 93
        for i, c in enumerate(self.control_list):
            c.zindex = i
            c.x = SineInterp(c.x, x + int(step * i), 0.3)
            c.y = SineInterp(c.y, 0, 0.3)

    def _on_cardanimdone(self, card, desc):
        card.delete()
        self.update()

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

class Ray(Control):
    img_ray = common_res.ray
    scale = InterpDesc('_scale')
    alpha = InterpDesc('_alpha')

    def __init__(self, x0, y0, x1, y1, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        # f, t should be [GameCharacterPortrait]s
        from math import sqrt, atan2, pi
        self.x, self.y = x0, y0
        dx, dy = x1 - x0, y1 - y0
        scale = sqrt(dx*dx+dy*dy) / self.img_ray.width
        self.angle = atan2(dy, dx) / pi * 180
        self.scale = SineInterp(0.0, scale, 0.4)
        self.alpha = ChainInterp(
            FixedInterp(1.0, 1),
            CosineInterp(1.0, 0.0, 0.5),
            on_done=lambda self, desc: self.delete()
        )

    def draw(self, dt):
        glPushMatrix()
        glRotatef(self.angle, 0., 0., 1.)
        glScalef(self.scale, 1., 1.)
        glTranslatef(0., -self.img_ray.height/2, 0.)
        glColor4f(1., 1., 1., self.alpha)
        self.img_ray.blit(0,0)
        glPopMatrix()

    def hit_test(self, x, y):
        return False

class ListItem(object):
    def __init__(self, p):
        self.parent = p
        n = len(p.columns)
        self.labels = [None] * n
        self._data = [''] * n
        self.data = ['Yoo~'] * n
        self.selected = False

    def _set_data(self, val):
        val = list(val)
        p = self.parent
        n = len(p.columns)
        val = (val + n*[''])[:n]
        for i, v in enumerate(val):
            self[i] = unicode(v)

    def _get_data(self):
        return self._data

    data = property(_get_data, _set_data)

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
        self.labels[index] = Label(
            text=val, font_name=p.font, font_size=p.font_size,
            anchor_x='left', anchor_y = 'bottom', color=(0,0,0,255),
        )

    def draw(self, bx, by, w):
        p = self.parent
        lh = p.line_height
        #w = p.width
        glColor3f(1,1,1)
        glRectf(bx, by, bx+w, by+lh)
        glColor3f(0,0,0)
        glBegin(GL_LINES)
        glVertex2f(bx, by); glVertex2f(bx+w, by)
        glVertex2f(bx, by+lh); glVertex2f(bx+w, by+lh)
        ox = 0
        for _, w in p.columns + [('', 0)]:
            glVertex2f(bx+ox, by)
            glVertex2f(bx+ox, by+lh)
            ox += w
        glEnd()
        ox = 0
        for (_, w), lbl in zip(p.columns, self.labels):
            lbl.x, lbl.y = bx + ox, by
            lbl.draw()
            ox += w

        if self.selected:
            glColor4f(0, 0, 1, 0.3)
            glRectf(bx, by, bx+p.width, by+lh)

class ListHeader(object):
    def __init__(self, p):
        self.parent = p

    def draw(self, x, y, w):
        p = self.parent
        glColor3f(0, 1, 1)
        glRectf(x, y, x+w, y+p.header_height)

class ListView(Control):
    li_class = ListItem
    lh_class = ListHeader
    header_height = 25
    line_height = 17
    def __init__(self, font_name='Arial', font_size=10, *a, **k):
        Control.__init__(self, *a, **k)
        self.font, self.font_size = font_name, font_size
        f = pyglet.font.load(font_name, font_size)
        self.font_height = f.ascent - f.descent
        self.items = []
        self.columns = []
        self.col_lookup = {}
        self._view_y = 0
        self.cur_select = None

    def set_columns(self, cols):
        # [('name1', 20), ('name2', 30)]
        self.columns = list(cols)
        self.col_lookup = {
            name: index
            for index, (name, width) in enumerate(cols)
        }
        self.header = self.lh_class(self)
        self.header.data = [n for n, w in cols]

    def append(self, val):
        if isinstance(val, ListItem):
            li = val
            li.parent = self
        elif isinstance(val, (list, tuple)):
            li = self.li_class(self)
            li.data = val
        self.items.append(li)
        return li

    def clear(self):
        self.items = []

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

    def draw(self, dt):
        ui_utils.border(0, 0, self.width, self.height)

        hh = self.header_height
        w, h = self.width - 16, self.height - hh - 16
        lh, vy = self.line_height, self.view_y
        self.header.draw(8, h, w)

        with ScissorBox(self, 0, 0, w+2, h+2) as sb:
            # GUIDO Y U REJECT PEP377 !!
            sb.break_if_invalid()
            y = h + vy
            nskip = int(max(1.0 * vy / lh, 0))
            ndisp = int(ceil(1.0 * (y - nskip * lh) / lh))
            for i in xrange(nskip, min(nskip + ndisp, len(self.items))):
                self.items[i].draw(8, y + 8 - (i+1)*lh, w)

    def on_mouse_scroll(self, x, y, dx, dy):
        self.view_y -= dy * 40

    def _mouse_click(self, evt_type, x, y, button, modifier):
        h = self.height - self.header_height
        lh, vy = self.line_height, self.view_y
        i = (h + vy - y) / lh
        if 0 <= i < len(self.items):
            cs = self.cur_select
            if cs is not None: self.items[cs].selected = False
            self.dispatch_event(evt_type, self.items[i])
            self.cur_select = i
            self.items[i].selected = True

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
            l.blit(x, y)
            r.blit(x + w - wr, y)
            m.get_region(0, 0, w - wl - wr, m.height).blit(x + wl, y)
        else:
            w /= 2
            l.get_region(0, 0, w, l.height).blit(x, y)
            _x = r.width - w
            r.get_region(_x, 0, w, r.height).blit(x + w, y)

    def draw(self, dt):
        value = self.value
        width, height = self.width, self.height

        glColor3f(1,1,1)
        self._drawit(0, 0, width, *self.pic_frame)
        w = (width - self.core_w_correct) * value
        if w: self._drawit(self.offs_x, self.offs_y, w, *self.pic_core)

class BigProgressBar(ProgressBar):
    r = common_res.pbar
    pic_frame = (r.bfl, r.bfm, r.bfr)
    pic_core = (r.bl, r.bm, r.br)
    offs_x, offs_y = 9, 9
    core_w_correct = 18
    del r

class SmallProgressBar(ProgressBar):
    r = common_res.pbar
    pic_frame = (r.sfl, r.sfm, r.sfr)
    pic_core = (r.sl, r.sm, r.sr)
    offs_x, offs_y = 8, 8
    core_w_correct = 16
    del r

class ConfirmButtons(Control):
    def __init__(self, buttons=((u'确定', True), (u'取消', False)), *a, **k):
        Control.__init__(self, *a, **k)
        for i, (p, v) in enumerate(buttons):
            btn = Button(
                parent=self, x=i*(80+5), y=0,
                width=80, height=24,
                caption=p
            )
            btn.retval = v
            @btn.event
            def on_click():
                self.confirm(btn.retval)

        self.width, self.height = len(buttons)*85-5, 24

    def confirm(self, val):
        self.value = val
        self.dispatch_event('on_confirm', val)

    def draw(self, dt):
        self.draw_subcontrols(dt)

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

ConfirmButtons.register_event_type('on_confirm')
