# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from pyglet import graphics
from pyglet.window import mouse
from client.ui.base import Control
from client.ui.base.interp import *
from client.ui import resource as common_res, ui_utils
from utils import Rect, ScissorBox, Framebuffer, dilate

from math import ceil

import logging
log = logging.getLogger('UI_Controls')

class Colors(object):
    class green(object):
        # Dialog
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

    class red(object):
        # Dialog
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

    class blue(object):
        # Dialog
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

    class orange(object):
        # Dialog
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

class Button(Control):
    NORMAL=0
    HOVER=1
    PRESSED=2
    DISABLED=3

    hover_alpha = InterpDesc('_hv')
    class color:
        frame = 66, 138, 123
        fill_up = 173, 207, 140
        fill_medline = 173, 223, 156
        fill_down = 189, 223, 156
        fill_botline = 222, 239, 206
        text = 49, 69, 99

    def __init__(self, caption='Button', color=Colors.green, *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.caption = caption
        self._state = Button.NORMAL
        self.state = Button.NORMAL
        self.hover_alpha = 0.0
        self.color = color

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

        def draw_it(func):
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

        fbo_tex = Framebuffer(pyglet.image.Texture.create_for_size(
            GL_TEXTURE_RECTANGLE_ARB, w, h, GL_RGBA
        ))
        with fbo_tex:
            draw_it(color)

        fbo_tex_gray = Framebuffer(pyglet.image.Texture.create_for_size(
            GL_TEXTURE_RECTANGLE_ARB, w, h, GL_RGBA
        ))
        r, g, b = self.color.text
        l = int(r*.3 + g*.59 + b*.11)
        lbl.color = (l, l, l, 255)
        with fbo_tex_gray:
            draw_it(gray)

        self.fbo_tex, self.fbo_tex_gray = fbo_tex, fbo_tex_gray


    def draw(self):
        glColor3f(1.0, 1.0, 1.0)
        if self.state == Button.DISABLED:
            self.fbo_tex_gray.texture.blit(0, 0)
        else:
            self.fbo_tex.texture.blit(0, 0)
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

    def draw(self):
        glColor3f(1.0, 1.0, 1.0)
        if self.state == Button.DISABLED:
            self.images[3].blit(0, 0)
        else:
            if self.state == Button.PRESSED:
                self.images[2].blit(0, 0)
            else:
                self.images[0].blit(0, 0)
                a = self.hover_alpha
                if a: # HOVER, or HOVER -> NORMAL
                    glColor4f(1.0, 1.0, 1.0, a)
                    self.images[1].blit(0, 0)

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

class Dialog(Control):
    '''
    Dialog, can move
    '''
    next_zindex = 1

    def __init__(self, caption='Dialog', color=Colors.green,
                 bot_reserve=10, bg=None, shadow_thick=2,
                 *args, **kwargs):
        Control.__init__(self, *args, **kwargs)
        self.zindex = Dialog.next_zindex
        self.color = color
        self.caption = caption
        self.bg = bg
        self.no_move = False
        self.bot_reserve = bot_reserve
        self.shadow_thick = shadow_thick
        Dialog.next_zindex += 1
        self.btn_close = ImageButton(
            images=color.close_btn,
            parent=self, font_size=12,
            x=self.width-18, y=self.height-19,
            manual_draw=True
        )
        self.dragging = False
        @self.btn_close.event
        def on_click():
            self.close()

        self.update()

    def update(self):
        w, h  = self.width, self.height
        tex = pyglet.image.Texture.create_for_size(
            GL_TEXTURE_RECTANGLE_ARB, w, h, GL_RGBA
        )
        fbo = Framebuffer(tex)

        def color(rgb):
            r, g, b = rgb
            return r/255., g/255., b/255.

        lbl = pyglet.text.Label(
            self.caption, u'AncientPix', 9,
            color=self.color.caption + (255,),
            x=2, y=4,
            anchor_x='left', anchor_y='bottom'
        )
        from client.ui import shaders
        from client.ui.base import shader
        if isinstance(shaders.FontShadowThick, shader.DummyShaderProgram):
            # no shader? fall back
            ttex = pyglet.image.Texture.create_for_size(
                GL_TEXTURE_RECTANGLE_ARB, lbl.content_width+4, 24, GL_RGBA
            )
            tfbo = Framebuffer(ttex)
            with tfbo:
                lbl.draw()

            shadow = ttex.get_image_data()
            for i in range(self.shadow_thick):
                shadow = dilate(shadow, self.color.shadow_thick)
            shadow = shadow.get_texture()
            with tfbo:
                glClearColor(0,0,0,0)
                glClear(GL_COLOR_BUFFER_BIT)
                glColor3f(1,1,1)
                shadow.blit(0, 0)
                lbl.draw()
        else:
            ttex = False

        with fbo:
            bg = self.bg
            r = self.bot_reserve
            if bg:
                glColor3f(1, 1, 1)
                bg.blit(2, r)
            else:
                glClearColor(1,1,1,1)
                glClear(GL_COLOR_BUFFER_BIT)

            glColor3f(*color(self.color.medium))
            glRectf(0, h-24, w, h) # title bar
            glRectf(0, 0, w, r) # bot reserve
            glBegin(GL_LINES)
            glColor3f(*color(self.color.heavy))
            glVertex2f(0, h-24); glVertex2f(w, h-24)
            glVertex2f(0, r); glVertex2f(w, r)
            glEnd()

            if ttex:
                glColor3f(1,1,1)
                ttex.blit(20, h-24)
            else:
                shader = [
                    shaders.DummyShader,
                    shaders.FontShadow,
                    shaders.FontShadowThick,
                ][self.shadow_thick]
                with shader as fs:
                    fs.uniform.shadow_color = color(self.color.caption_shadow) + (1.0, )
                    glColor3f(*color(self.color.caption))
                    lbl.x, lbl.y = 20, h-20
                    lbl.draw()

            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glColor3f(*color(self.color.frame))
            glLineWidth(4.0)
            glRectf(0, 0, w, h)
            glLineWidth(1.0)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        self.fbo = fbo

    def on_resize(self, width, height):
        self.label.x = width // 2
        self.label.y = height - 8
        self.btn_close.x = width - 20
        self.btn_close.y = height - 19

    def draw(self):
        glColor3f(1,1,1)
        self.fbo.texture.blit(0,0)

        w, h = self.width, self.height
        ax, ay = self.abs_coords()
        ax, ay = int(ax), int(ay)

        ob = (GLint*4)()
        glGetIntegerv(GL_SCISSOR_BOX, ob)
        ob = list(ob)
        nb = Rect(*ob).intersect(Rect(ax, ay, w, h))
        if nb:
            if nb.height > 25:
                glScissor(nb.x, nb.y, nb.width, nb.height-25)
                self.draw_subcontrols()
            glScissor(*ob)

        self.btn_close.do_draw()

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
    def __init__(self, text='Yoooooo~', color=Colors.green, *args, **kwargs):
        Control.__init__(self, can_focus=True, *args, **kwargs)
        self.document = pyglet.text.document.UnformattedDocument(text)
        self.document.set_style(0, len(self.document.text), dict(
                color=(0, 0, 0, 255),
                font_name='AncientPix',
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

    # TODO: def on_key_press(...): #handle Ctrl+C Ctrl+V Ctrl+A
    def on_text(self, text):
        from pyglet.window import key
        if text == '\r': # Why this??
            self.dispatch_event('on_enter')
            return pyglet.event.EVENT_HANDLED

TextBox.register_event_type('on_enter')

class PlayerPortrait(Dialog):
    def __init__(self, player_name, color=Colors.blue, *args, **kwargs):
        self.player_name = player_name
        Dialog.__init__(
            self, caption=player_name, color=color,
            bot_reserve=50, width=128, height=245,
            shadow_thick=1,
            *args, **kwargs
        )

        self.no_move = True
        self.btn_close.state = Button.DISABLED

    def update(self):
        self.caption = self.player_name
        Dialog.update(self)

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

    def draw(self):
        '''
        glPushAttrib(GL_POLYGON_BIT)
        glColor3f(1.0, 1.0, 1.0)
        glRecti(0, 0, self.width, self.height)
        glColor3f(0.0, 0.0, 0.0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        glRecti(0, 0, self.width, self.height)
        glPopAttrib()'''
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

    def draw(self):
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

    def draw(self):
        glColor4f(1,1,1,1)
        self.draw_subcontrols()

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

    def draw(self):
        glColor4f(1,1,1,1)
        self.draw_subcontrols()

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

    def draw(self):
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
        c = p.color.text + (255,)
        self.labels[index] = Label(
            text=val, font_name='AncientPix', font_size=9,
            anchor_x='left', anchor_y = 'bottom', color=c,
        )

    def draw(self):
        p = self.parent
        lh = p.line_height
        color = p.color

        glDisable(GL_BLEND)
        glColor4f(0,0,0,0)
        glRectf(0, 0, p.width, 15)
        glEnable(GL_BLEND)

        if self.selected:
            c = [i/255.0 for i in color.light] + [1.0]
            glColor4f(*c)
            glRectf(0, 0, p.width, 15)

        glColor3f(1,1,1)

        ox = 2
        for (_, w), lbl in zip(p.columns, self.labels):
            lbl.x, lbl.y = ox, 2
            lbl.draw()
            ox += w

        return

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
        self.cur_select = None
        th = self.tex_height = 10 * self.line_height
        tex = pyglet.image.Texture.create_for_size(
            GL_TEXTURE_RECTANGLE_ARB, self.width, self.tex_height,
            GL_RGBA
        )
        fbo = self.fbo = Framebuffer(tex)
        with fbo:
            glClearColor(0,0,0,0)
            glClear(GL_COLOR_BUFFER_BIT)

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
        self.update_single(li)
        return li

    def clear(self):
        self.items = []
        with self.fbo:
            glClearColor(0,0,0,0)
            glClear(GL_COLOR_BUFFER_BIT)

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

    def update(self):
        n = len(self.items)
        if n * self.line_height >= self.tex_height:
            self._double_tex_height()

        fbo = self.fbo
        tex =  fbo.texture
        y = tex.height
        lh = self.line_height
        with fbo:
            for i in self.items:
                y -= lh
                glLoadIdentity()
                glTranslatef(0, y, 0)
                i.draw()

    def update_single(self, item):
        items = self.items
        n = len(items)
        if n * self.line_height >= self.tex_height:
            self._double_tex_height()

        i = items.index(item)
        fbo = self.fbo
        tex = fbo.texture
        y = tex.height
        lh = self.line_height
        with fbo:
            y -= (i+1)*lh
            glTranslatef(0, y, 0)
            item.draw()

    def _double_tex_height(self):
        old_tex = self.fbo.texture
        h = old_tex.height
        del self.fbo
        tex = pyglet.image.Texture.create_for_size(
            GL_TEXTURE_RECTANGLE_ARB, old_tex.width, h*2,
            GL_RGBA
        )
        fbo = Framebuffer(tex)
        with fbo:
            glClearColor(0,0,0,0)
            glClear(GL_COLOR_BUFFER_BIT)
            glColor3f(1, 1, 1)
            old_tex.blit(0, h)
        self.tex_height = h*2
        self.fbo = fbo

    def draw(self):
        #glColor3f(.5,.5,.5) # XXXXXXXXXXX
        #glRectf(0, 0, self.width, self.height)
        glColor3f(1,1,1)

        tex = self.fbo.texture
        hh = self.header_height
        content_height = len(self.items) * self.line_height
        client_height = self.height - hh
        vy = self.view_y
        y = content_height - vy
        by = y - client_height
        if by < 0: by = 0

        #print 'y := ', y, 'vy := ', vy, content_height, client_height
        if y:
            glColor3f(1,1,1)
            tex = tex.get_region(0, tex.height - content_height, tex.width, tex.height)
            tex.get_region(0, by, tex.width, y-by).blit(0, client_height - (y-by))

        glPushMatrix()
        glTranslatef(0, client_height, 0)
        self.header.draw()
        glPopMatrix()

    def on_mouse_scroll(self, x, y, dx, dy):
        self.view_y -= dy * 40

    def _mouse_click(self, evt_type, x, y, button, modifier):
        h = self.height - self.header_height
        lh, vy = self.line_height, self.view_y
        i = (h + vy - y) / lh
        if 0 <= i < len(self.items):
            cs = self.cur_select
            if cs is not None:
                item = self.items[cs]
                item.selected = False
                self.update_single(item)
            self.dispatch_event(evt_type, self.items[i])
            self.cur_select = i
            item = self.items[i]
            item.selected = True
            self.update_single(item)

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

    def draw(self):
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
        self.buttons = bl = []
        for i, (p, v) in enumerate(buttons):
            btn = Button(
                parent=self, x=i*(80+6), y=0,
                width=80, height=24,
                caption=p
            )
            btn.retval = v
            @btn.event
            def on_click(btn=btn):
                self.confirm(btn.retval)

            bl.append(btn)

        self.width, self.height = len(buttons)*85-6, 24

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
        self.lbl = lbl

        btn = ConfirmButtons(buttons, parent=self)
        @btn.event
        def on_confirm(val):
            self.value = val
            self.delete()
            self.dispatch_event('on_confirm', val)
        btn.x, btn.y = (dw - btn.width)/2, 5

        p = self.parent
        pw, ph = p.width, p.height
        self.x, self.y = (pw - dw)/2, (ph - dh)/2

    def draw(self):
        glColor3f(1,1,1)
        Dialog.draw(self)
        self.lbl.draw()

ConfirmBox.register_event_type('on_confirm')

