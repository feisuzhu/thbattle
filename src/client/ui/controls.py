# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import *
from client.ui.base import message as ui_message, schedule as ui_schedule
from client.ui.base.shader import ShaderGroup, ShaderUniformGroup
from client.ui.base.interp import *
from client.ui import resource as common_res, shaders
from client.core import Executive
from utils import Rect, Framebuffer, DisplayList, textsnap

HAVE_FBO = gl_info.have_extension('GL_EXT_framebuffer_object')

from math import ceil

import logging
log = logging.getLogger('UI_Controls')

class Colors:
    class green:
        # Frame
        frame = 49, 69, 99
        heavy = 66, 138, 115
        medium = 140, 186, 140
        light = 206, 239, 156
        caption = 255, 255, 255
        caption_shadow = heavy
        close_btn = common_res.buttons.close_green
        # Button
        btn_frame = heavy
        fill_up = 173, 207, 140
        fill_medline = 173, 223, 156
        fill_down = 189, 223, 156
        fill_botline = 222, 239, 206
        text = frame

    class red:
        # Frame
        frame = 171, 68, 81
        medium = 0xff, 0x9f, 0x8c
        heavy = frame
        light = 254, 221, 206
        caption = 255, 255, 255
        caption_shadow = frame
        close_btn = common_res.buttons.close_red
        # Button
        btn_frame = frame
        fill_up = 0xee, 0x89, 0x78
        fill_medline = fill_up
        fill_down = 0xf7, 0x9c, 0x8c
        fill_botline = fill_down
        text = frame

    class blue:
        # Frame
        frame = 0x31, 0x55, 0x97
        medium = 0x90, 0xbc, 0xed
        heavy = 0x64, 0x8a, 0xd0
        light = 0xa3, 0xd1, 0xfa
        caption = frame
        caption_shadow = 0xe5, 0xef, 0xfb
        close_btn = common_res.buttons.close_blue
        # Button
        btn_frame = 0x54, 0x67, 0xa6
        fill_up = 0x90, 0xbf, 0xef
        fill_down = 0xa3, 0xd1, 0xfa
        fill_medline = 0x9a, 0xc8, 0xf5
        fill_botline = 0xc5, 0xf2, 0xff
        text = frame

    class orange:
        # Frame
        frame = 0x88, 0x66, 0x66
        medium = 0xff, 0xcc, 0x77
        heavy = frame
        light = 0xff, 0xee, 0xaa
        caption = 255, 255, 255
        caption_shadow = frame
        close_btn = common_res.buttons.close_orange
        # Button
        btn_frame = frame
        fill_up = medium
        fill_medline = fill_up
        fill_down = 0xff, 0xdd, 0x88
        fill_botline = light
        text = frame

    class gray:
        # Frame
        close_btn = common_res.buttons.close_blue
        btn_frame  =  104, 104, 104
        caption  =  81, 81, 81
        caption_shadow  =  237, 237, 237
        fill_botline  =  229, 229, 229
        fill_down  =  199, 199, 199
        fill_medline  =  191, 191, 191
        fill_up  =  182, 182, 182
        frame  =  81, 81, 81
        heavy  =  134, 134, 134
        light  =  199, 199, 199
        medium  =  180, 180, 180
        text  =  81, 81, 81

    @staticmethod
    def get4f(c):
        return c[0]/255.0, c[1]/255.0, c[2]/255.0, 1.0

    @staticmethod
    def get4i(c):
        return c + (255, )

class Button(Control):
    NORMAL=0
    HOVER=1
    PRESSED=2
    DISABLED=3

    hover_alpha = InterpDesc('_hv')

    def __init__(self, caption='Button', color=Colors.green, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.caption = caption
        self._state = Button.NORMAL
        self.state = Button.NORMAL
        self.hover_alpha = 0.0
        self.color = color

        self._dl = DisplayList()
        self._dl_gray = DisplayList()

        self.update()

    def update(self):
        lbl = pyglet.text.Label(
            self.caption, u'AncientPix', 9,
            color=self.color.text + (255,),
            x=self.width//2, y=self.height//2,
            anchor_x='center', anchor_y='center'
        )
        w, h = self.width, self.height

        def color(rgb):
            r, g, b = rgb
            return r/255., g/255., b/255., 1.0

        def gray(rgb):
            r, g, b = rgb
            l = r*.3/255 + g*.59/255 + b*.11/255
            return l, l, l, 1.0

        def build(func, dl):
            with dl:
                glColor4f(*func(self.color.fill_down))
                glRectf(0.0, 0.0, w, h*.5)
                glColor4f(*func(self.color.fill_up))
                glRectf(0.0, h*.5, w, h)

                glBegin(GL_LINES)
                glColor4f(*func(self.color.fill_medline))
                glVertex2f(0, h*.5); glVertex2f(w, h*.5)
                glColor4f(*func(self.color.fill_botline))
                glVertex2f(0, 2); glVertex2f(w, 2)
                glEnd()

                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
                glColor4f(*func(self.color.heavy))
                glRectf(1., 1., w, h)
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

                lbl.draw()

        build(color, self._dl)

        r, g, b = self.color.text
        l = int(r*.3 + g*.59 + b*.11)
        lbl.color = (l, l, l, 255)
        build(gray, self._dl_gray)

    def draw(self):
        glColor3f(1.0, 1.0, 1.0)
        if self.state == Button.DISABLED:
            self._dl_gray()
        else:
            self._dl()
            if self.state == Button.PRESSED:
                glColor4f(0, 0, 0, .25)
                glRectf(0, 0, self.width, self.height)
            else:
                a = self.hover_alpha
                if a: # HOVER, or HOVER -> NORMAL
                    glColor4f(1.0, 1.0, .843, a)
                    glRectf(0, 0, self.width, self.height)

    def on_mouse_enter(self, x, y):
        if self.state != Button.DISABLED:
            self.state = Button.HOVER

    def on_mouse_leave(self, x, y):
        if self.state != Button.DISABLED:
            self.state = Button.NORMAL

    def on_mouse_press(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            if button == mouse.LEFT:
                self.state = Button.PRESSED

    def on_mouse_release(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            if button == mouse.LEFT:
                self.state = Button.HOVER

    def on_mouse_click(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            self.dispatch_event('on_click')

    def _get_state(self):
        return self._state

    def _set_state(self, val):
        last = self._state
        self._state = val
        if val == Button.HOVER:
            self.hover_alpha = .25
        elif last == Button.HOVER and val == Button.NORMAL:
            self.hover_alpha = LinearInterp(
                .25, 0, .17
            )
    state = property(_get_state, _set_state)

class ImageButton(Control):
    NORMAL=0
    HOVER=1
    PRESSED=2
    DISABLED=3

    hover_alpha = InterpDesc('_hv')

    def __init__(self, images, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.images = images
        self._state = Button.NORMAL
        self.state = Button.NORMAL
        self.hover_alpha = 0.0
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
                    if a: # HOVER, or HOVER -> NORMAL
                        glColor4f(1.0, 1.0, 1.0, a)
                        blit(btn, 1)
                        glColor3f(1, 1, 1)

        glPopAttrib()
        glPopMatrix()


    def on_mouse_enter(self, x, y):
        if self.state != Button.DISABLED:
            self.state = Button.HOVER

    def on_mouse_leave(self, x, y):
        if self.state != Button.DISABLED:
            self.state = Button.NORMAL

    def on_mouse_press(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            if button == mouse.LEFT:
                self.state = Button.PRESSED

    def on_mouse_release(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            if button == mouse.LEFT:
                self.state = Button.HOVER

    def on_mouse_click(self, x, y, button, modifier):
        if self.state != Button.DISABLED:
            self.dispatch_event('on_click')

    def _get_state(self):
        return self._state

    def _set_state(self, val):
        last = self._state
        self._state = val
        if val == Button.HOVER:
            self.hover_alpha = 1.
        elif last == Button.HOVER and val == Button.NORMAL:
            self.hover_alpha = LinearInterp(
                1., 0, .3
            )
    state = property(_get_state, _set_state)

Button.register_event_type('on_click')
ImageButton.register_event_type('on_click')

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
    def __init__(self, caption='Frame', color=Colors.green,
                 bot_reserve=10, bg=None, shadow_thick=2,
                 *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.color = color
        self.caption = caption
        self.bg = bg
        self.labels = []
        self.bot_reserve = bot_reserve
        self.shadow_thick = shadow_thick

        self.update()

    def update(self):
        cap = self.caption
        f = pyglet.font.load('AncientPix', 9)
        cap = textsnap(cap, f, self.width - 20 - 4)

        sg = ShaderGroup([
            shaders.DummyShader,
            shaders.FontShadow,
            shaders.FontShadowThick,
        ][self.shadow_thick])

        args = ((
            'shadow_color',
            tuple([i/255.0 for i in self.color.caption_shadow+(255,)])
        ), )
        g = ShaderUniformGroup(args, sg)

        l = self.caption_lbl = pyglet.text.Label(
            cap, u'AncientPix', 9,
            color=self.color.caption + (255,),
            x=20, y=self.height - 20,
            anchor_x='left', anchor_y='bottom',
            group=g
        )
        l._parent = self

        #with self._dl:
        #    self._batch_content_draw([self])

    @staticmethod
    def _batch_content_draw(dlgs):

        def color(rgb):
            r, g, b = rgb
            return r/255., g/255., b/255.

        from client.ui import shaders

        # bg pics
        bglist = []
        nobglist = []
        for d in dlgs:
            bg = getattr(d, 'bg', None)
            if bg: bglist.append(d)
            else: nobglist.append(d)

        bglist.sort(key=lambda d: d.bg.id)

        glColor3f(1, 1, 1)

        glEnable(GL_TEXTURE_2D)
        curtex = None
        for d in bglist:
            bg = d.bg; r = d.bot_reserve; w = d.width; h = d.height
            ax, ay = d.abs_coords()
            if curtex != bg.id:
                glBindTexture(GL_TEXTURE_2D, bg.id)
                curtex = bg.id

            if bg.height > h - 24 - r or bg.width > w - 4:
                _w = min(bg.width, w - 4)
                _h = min(bg.height, h - 24 - r)
                bg = bg.get_region(0, 0, _w, _h)
            bg.blit_nobind(ax + 2, ay + r)
        glDisable(GL_TEXTURE_2D)

        for d in nobglist:
            x, y = d.abs_coords()
            glRectf(x + 1, d.y + 1, x + d.width-1, d.y + d.height-1)

        for d in dlgs:
            w, h, r = d.width, d.height, d.bot_reserve
            ax, ay = d.abs_coords()
            glColor3f(*color(d.color.medium))
            glRectf(ax, ay+h-24, ax+w, ay+h) # title bar
            glRectf(ax, ay, ax+w, ay+r) # bot reserve
            glBegin(GL_LINES)
            glColor3f(*color(d.color.heavy))
            glVertex2f(ax, ay+h-24); glVertex2f(ax+w, ay+h-24)
            glVertex2f(ax, ay+r); glVertex2f(ax+w, ay+r)
            glEnd()

        lbls = []
        map(lbls.extend, [d.labels for d in dlgs])
        lbls.extend([d.caption_lbl for d in dlgs])

        batch_drawlabel(lbls)

        glLineWidth(2.0)
        for d in dlgs:
            ax, ay = d.abs_coords()
            w, h = d.width, d.height
            glColor3f(*color(d.color.frame))

            vl = (GLfloat*10)(
                ax+1, ay+1,
                ax+1, ay+h-1,
                ax+w-1, ay+h-1,
                ax+w-1, ay+1,
                ax+1, ay+1,
            )

            glInterleavedArrays(GL_V2F, 0, vl)
            glDrawArrays(GL_LINE_STRIP, 0, 5)

        glLineWidth(1.0)

    @staticmethod
    def batch_draw(dlgs):
        glColor3f(1,1,1)
        glPushMatrix()
        glLoadIdentity()
        Frame._batch_content_draw(dlgs)
        glPopMatrix()

        cl = []
        map(cl.extend, [d.control_list for d in dlgs])
        Control.do_draw(cl)

    def close(self):
        self._cancel_close = False
        self.dispatch_event('on_close')
        if not self._cancel_close:
            self.delete()
            self.dispatch_event('on_destroy')

    def cancel_close(self):
        self._cancel_close = True

    def add_label(self, *a, **k):
        l = pyglet.text.Label(*a, **k)
        l._parent = self
        self.labels.append(l)
        return l

    def delete(self):
        Control.delete(self)
        for l in self.labels:
            l.delete()
        self.caption_lbl.delete()

class Dialog(Frame):
    no_move = False
    next_zindex = 1

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
            self.x += dx
            self.y += dy

            for lbl in self.labels + [self.caption_lbl]:
                lbl.begin_update()
                lbl.x += dx
                lbl.y += dy
                lbl.end_update()

            self.dispatch_event('on_move', self.x, self.y)

Frame.register_event_type('on_move')
Frame.register_event_type('on_close')
Frame.register_event_type('on_destroy')

class BalloonPrompt(object):
    balloon_inited = False
    balloon_panel = None
    balloon_cursorloc = (0, 0)
    def init_balloon(self, text, region=None):
        self.balloon_text = text
        self.balloon_region = region

        if not self.balloon_inited:
            self.balloon_inited = True
            self.push_handlers(
                on_mouse_motion=self.balloon_on_mouse_motion,
                on_mouse_drag=self.balloon_on_mouse_motion,
                on_mouse_enter=self.balloon_on_mouse_enter,
                on_mouse_leave=self.balloon_on_mouse_leave,
            )
            self.balloon_state = 'hidden'
        else:
            if self.balloon_state == 'shown':
                self.balloon_panel.delete()
                del self.balloon_panel
                self.balloon_state = 'hidden'

    def balloon_on_mouse_motion(self, x, y, dx, dy, *a):
        ax, ay = self.abs_coords()
        ax += x
        ay += y

        self.balloon_cursorloc = (ax, ay)

        r = self.balloon_region
        if r:
            x1, y1, w, h = r
            x2 = x1 + w
            y2 = y1 + h
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.balloon_on_mouse_enter(x, y)
            else:
                self.balloon_on_mouse_leave(x, y)

        b = self.balloon_panel
        if b:
            b.x, b.y = self._balloon_getloc(ax, ay)

    def _balloon_getloc(self, x, y):
        b = self.balloon_panel
        o = Overlay.cur_overlay
        ow, oh = o.width, o.height
        bw, bh = b.width, b.height

        if x*2 <= ow:
            x += 10
        else:
            x -= bw + 10

        if y*2 <= oh:
            y += 10
        else:
            y -= bh + 10

        return (x, y)

    def balloon_on_mouse_enter(self, x, y):
        if self.balloon_state == 'hidden':
            self.balloon_state = 'ticking'
            self.balloon_overlay = Overlay.cur_overlay
            pyglet.clock.schedule_once(self.balloon_show, 0.8)

    def balloon_on_mouse_leave(self, x, y):
        if self.balloon_state == 'ticking':
            pyglet.clock.unschedule(self.balloon_show)
        if self.balloon_state == 'shown':
            self.balloon_panel.delete()
            del self.balloon_panel
        self.balloon_state = 'hidden'

    def balloon_show(self, dt):
        if self.balloon_state == 'shown': return
        if Overlay.cur_overlay != self.balloon_overlay: return

        self.balloon_state = 'shown'

        ta = TextArea(parent=None, x=2, y=2, width=288, height=100)
        ta.append(self.balloon_text)
        h = ta.content_height
        ta.height = h

        panel = Panel(parent=Overlay.cur_overlay, x=0, y=0, width=292, height=h+4)
        panel.add_control(ta)
        panel.fill_color = (1.0, 1.0, 0.9, 0.5)
        self.balloon_panel = panel

        @panel.event
        def on_mouse_enter(x, y, panel=panel):
            panel.delete()

        panel.x, panel.y = self._balloon_getloc(*self.balloon_cursorloc)

class TextBox(Control):
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
        #ui_utils.border(0, 0, self.width, self.height)
        w, h = self.width, self.height
        border = [i/255.0 for i in self.color.heavy]
        fill = [i/255.0 for i in self.color.light]
        glColor3f(*fill)
        glRectf(0, 0, w, h)
        glColor3f(*border)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRectf(0, 0, w, h)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
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

    # TODO: def on_key_press(...): #handle Ctrl+C Ctrl+V Ctrl+A
    def on_text(self, text):
        from pyglet.window import key
        if text == '\r': # Why this??
            self.dispatch_event('on_enter')
            return pyglet.event.EVENT_HANDLED

TextBox.register_event_type('on_enter')

class PasswordTextBox(TextBox):
    def __init__(self, *a, **k):
        TextBox.__init__(self, font_name='AncientPixPassword', *a, **k)

class PlayerPortrait(Frame):
    shader_group = ShaderGroup(shaders.FontShadow)
    def __init__(self, player_name, color=Colors.blue, *args, **kwargs):
        self.account = None
        self.ready = False
        self.accinfo_labels = []

        self.player_name = player_name
        Frame.__init__(
            self, caption=player_name, color=color,
            bot_reserve=50, width=128, height=245,
            shadow_thick=1,
            *args, **kwargs
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

        def change_loc():
            Executive.call(
                'change_location', ui_message,
                self.parent.portraits.index(self)
            )

        def kick():
            if not self.userid: return
            Executive.call(
                'kick_user', ui_message, self.userid
            )

        btn(u'换位', change_loc , 90, 55, 32, 20)
        btn(u'请离', kick, 90, 80, 32, 20)

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

        lbls = self.labels
        for l in self.accinfo_labels:
            lbls.remove(l)
            l.delete()
        self.accinfo_labels = []
        self.avatar = None

        self.caption = name

        if acc:
            avurl = acc.other['avatar']
        else:
            avurl = None

        if avurl:
            img = self.cached_avatar.get(avurl, None)
            if img:
                sprite = pyglet.sprite.Sprite(img, x=64, y=150)
                sprite.scale = min(1.0, 64.0*2/img.width, 170.0*2/img.height)
                sprite._parent = self
                self.avatar = sprite
            else:
                def callback(rst):
                    if rst:
                        resp, data = rst

                        if data.startswith('GIF'):
                            fn = 'foo.gif'
                        elif data.startswith('\xff\xd8') and data.endswith('\xff\xd9'):
                            fn = 'foo.jpg'
                        elif data.startswith('\x89PNG'):
                            fn = 'foo.png'

                        from StringIO import StringIO
                        f = StringIO(data)

                        if fn == 'foo.gif':
                            from utils import gif_to_animation
                            img = gif_to_animation(f)
                        else:
                            img = pyglet.image.load(fn, file=f)
                            img.anchor_x, img.anchor_y = img.width // 2, img.height // 2

                        sprite = pyglet.sprite.Sprite(img, x=64, y=150)
                        sprite.scale = min(1.0, 64.0*2/img.width, 170.0*2/img.height)
                        sprite._parent = self
                    else:
                        img = sprite = False

                    self.cached_avatar[avurl] = img
                    self.avatar = sprite

                    if sprite:
                        ui_schedule(self.update)

                Executive.call('fetch_resource', callback, avurl)

        Frame.update(self)

        if not acc: return

        c = self.color.caption + (255,)
        f = pyglet.font.load('AncientPix', 9)
        def L(text, loc):
            text = textsnap(text, f, self.width - 8 - 4)
            args = ((
                'shadow_color',
                tuple([i/255.0 for i in self.color.caption_shadow+(255,)])
            ), )
            g = ShaderUniformGroup(args, self.shader_group)

            l = pyglet.text.Label(
                text, x=8, y=47-15*loc,
                anchor_x='left', anchor_y='top',
                font_name='AncientPix', font_size=9,
                color=c, group=g
            )
            l._parent = self

            self.accinfo_labels.append(l)
            self.labels.append(l)

        L(acc.other['title'], 0)
        L(u'节操： %d' % acc.other['credits'], 1)
        g, d = acc.other['games'], acc.other['drops']
        dr = int(100*d/g) if d else 0
        L(u'游戏数：%d(%d%%)' % (g, dr), 2)

    def draw(self):
        PlayerPortrait.draw(self)
        if self.avatar:
            self.avatar.draw()

        #for b in self.buttons:
        #    b.do_draw()
        Button.batch_draw(self.buttons)

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
    def __init__(self, font=u'AncientPix', font_size=9, *args, **kwargs):
        Control.__init__(self, can_focus=True, *args, **kwargs)

        width, height = self.width, self.height

        self.document = doc = pyglet.text.document.FormattedDocument(u'')
        self.default_attrib = dict(
            font_size=font_size, font_name=font,
            bold=False, italic=False,
            underline=None, color=(0, 0, 0, 255),
        )

        self.layout = pyglet.text.layout.IncrementalTextLayout(
            self.document, width-8, height-8, multiline=True
        )

        self.layout.x = 4
        self.layout.y = 4

        self._text = u''

    def _gettext(self):
        return self._text

    def _settext(self, text):
        self._text = u''
        l = self.layout
        l.begin_update()
        self.document.text = u''
        self.append(text)
        #l.end_update() # self.append will call it

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

            # shortcuts
            (r'\|R', set_attrib('color', (0xff, 0x35, 0x35, 0xff))),
            (r'\|G', set_attrib('color', (0x20, 0x80, 0x20, 0xff))),
            (r'\|Y', set_attrib('color', (0xff, 0xff, 0x30, 0xff))),
            (r'\|LB', set_attrib('color', (0x90, 0xdc, 0xe8, 0xff))),
            (r'\|DB', set_attrib('color', (0x00, 0x00, 0x60, 0xff))),
            (r'\|W', set_attrib('color', (0xff, 0xff, 0xff, 0xff))),

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

    def draw(self):
        self.layout.draw()

    def on_mouse_scroll(self, x, y, dx, dy):
        f = self.document.get_font(0)
        size = f.ascent - f.descent
        self.layout.view_y += dy * size*2

    @property
    def content_height(self):
        return self.layout.content_height + 8

    def on_resize(self, width, height):
        l = self.layout
        l.begin_update()
        l.width, l.height = width - 8, height - 8
        l.end_update()

class ListItem(object):
    def __init__(self, p, i):
        self.parent = p
        n = len(p.columns)
        self.labels = [None] * n
        self._data = [''] * n
        self.idx = i
        #self.data = ['Yoo~'] * n

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
            anchor_x='left', anchor_y = 'top', color=c,
            batch=p.batch,
        )

class ListHeader(object):
    def __init__(self, p):
        self.parent = p
        from pyglet.text import Label
        cols = p.columns
        labels = []
        batch = pyglet.graphics.Batch()
        _x = 2
        c = p.color.heavy + (255,)
        for name, width in cols:
            lbl = Label(
                name, anchor_x='left', anchor_y='bottom',
                x=_x, y=5, color=c, font_name='AncientPix', font_size=12,
                batch=batch
            )
            _x += width
        self.batch = batch

    def draw(self):
        p = self.parent
        hh = p.header_height
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
        self._dl = DisplayList()
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

    def append(self, val):
        if isinstance(val, ListItem):
            li = val
            li.parent = self
        elif isinstance(val, (list, tuple)):
            li = self.li_class(self, len(self.items))
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
        glColor3f(1,1,1)

        hh = self.header_height
        client_height = self.height - hh
        vy = self.view_y

        #glPushMatrix()
        if self.need_refresh:
            with self._dl:
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

        self._dl()
        #glPopMatrix()

    def on_mouse_scroll(self, x, y, dx, dy):
        self.view_y -= dy * 40
        self.need_refresh = True

    def _mouse_click(self, evt_type, x, y, button, modifier):
        h = self.height - self.header_height
        lh, vy = self.line_height, self.view_y
        i = (h + vy - y) / lh
        n = len(self.items)
        if 0 <= i < n:
            cs = self.cur_select
            if cs is not None and 0 <= cs < n:
                item = self.items[cs]
            self.dispatch_event(evt_type, self.items[i])
            self.cur_select = i
            item = self.items[i]
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
        width, height = self.width, self.height

        glColor3f(1,1,1)
        tex = self.pic_frame[0].owner
        with tex:
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
    def __init__(self, buttons=((u'确定', True), (u'取消', False)), color=Colors.green, *a, **k):
        Control.__init__(self, *a, **k)
        self.buttons = bl = []
        n = len(buttons)
        if n > 2:
            wl = [len(b[0])*20 + 20 for b in buttons]
        else:
            wl = [80] * n

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
                self.confirm(btn.retval)

            bl.append(btn)
            loc += w + 6

        self.width, self.height = loc, 24

    def confirm(self, val):
        self.value = val
        self.dispatch_event('on_confirm', val)

    def draw(self):
        self.draw_subcontrols()

    def hit_test(self, x, y):
        return self.control_frompoint1(x, y)

ConfirmButtons.register_event_type('on_confirm')

class ConfirmBox(Dialog):
    class Presets:
        OK = ((u'确定', True), )
        OKCancel = ((u'确定', True), (u'取消', False))

    def __init__(self, text=u'Yoo~', caption=u'信息', buttons=Presets.OK, *a, **k):
        lbl = pyglet.text.Label(
            text=text, font_name=u'AncientPix', font_size=9,
            anchor_x='center', anchor_y='bottom',
            width=1000, multiline=True,
            color=(0,0,0,255)
        )
        w, h = lbl.content_width, lbl.content_height
        lbl.width = w
        dw, dh = w+50, h+24+33+20*2
        Dialog.__init__(
            self, caption, width=dw, height=dh,
            bot_reserve=33, *a, **k
        )
        lbl.x = dw // 2
        lbl.y = 33+20
        lbl._parent = self
        self.labels.append(lbl)

        btn = ConfirmButtons(buttons, parent=self, color=self.color)
        @btn.event
        def on_confirm(val):
            self.value = val
            self.delete()
            self.dispatch_event('on_confirm', val)
        btn.x, btn.y = (dw - btn.width)/2, 5

        p = self.parent
        pw, ph = p.width, p.height
        self.x, self.y = (pw - dw)/2, (ph - dh)/2

ConfirmBox.register_event_type('on_confirm')

class Panel(Control):
    fill_color = (1.0, 1.0, 0.8, 0.0)

    def __init__(self, color=Colors.green, *a, **k):
        Control.__init__(self, *a, **k)
        self.color = color
        self.tick = 0
        self.update()

    def update(self):
        w, h = int(self.width), int(self.height)

        from shaders import HAVE_SHADER
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
                 x1,    y2,    0,     1.
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
            glDisable(blurtex.target)

        c = self.fill_color
        if c[3] != 0.0:
            glColor4f(*c)
            glRectf(0, 0, w, h)

        glLineWidth(3.0)
        glColor4f(1, 1, 1, .3)
        glRectf(1.5, 1.5, -1.5+w, -1.5+h)
        glColor3f(*[i/255.0 for i in self.color.frame])
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRectf(-1.5+w, -1.5+h, 1.5, 1.5)
        glLineWidth(1.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        self.draw_subcontrols()

class ImageSelector(Control):
    hover_alpha = InterpDesc('_hover_alpha')
    auxfbo = Framebuffer() if HAVE_FBO else None
    def __init__(self, image, group, *a, **k):
        Control.__init__(
            self, width=145, height=98,
            *a, **k
        )

        self.selected = False
        self.disabled = False
        self.hover_alpha = 0.0
        self.image = image
        self.group = group

        fbo = self.auxfbo
        if fbo:
            self.grayed_image = pyglet.image.Texture.create(
                image.width, image.height
            )

            with fbo:
                fbo.texture = self.grayed_image
                glColor3f(1, 1, 1)
                with shaders.Grayscale:
                    image.blit(0, 0)

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
            if HAVE_FBO:
                self.grayed_image.blit(0, 0)
            else:
                glColor3f(0, 0, 0)
                glRectf(0, 0, self.width, self.height)
        else:
            self.image.blit(0, 0)

        glColor3f(0.757, 1.0, 0.384)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRectf(0, 0, self.width, self.height)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        if self.selected:
            common_res.imagesel_shine.blit(-11, -11)

        a = self.hover_alpha
        if a:
            glColor4f(1, 1, 0.8, a)
            glRectf(0, 0, self.width, self.height)

    def disable(self):
        self.disabled = True
        self.selected = False

    @staticmethod
    def get_selected(group):
        for c in group:
            if c.selected:
                return c
        return None

ImageSelector.register_event_type('on_select')
ImageSelector.register_event_type('on_dblclick')
