# -*- coding: utf-8 -*-

# -- stdlib --
from math import ceil

# -- third party --
from PIL import Image
from pyglet.font.base import Font, GlyphRenderer
import pyglet

# -- own --
from client.ui.resloader import L


# -- code --
class AncientPixGlyphRenderer(GlyphRenderer):
    gbk_cols = 191
    gbk_rows = 126

    def __init__(self, font):
        GlyphRenderer.__init__(self, font)
        self.font = font

    def render(self, text):
        glyph = self.render_char(text, 0)
        thin = self.render_char(text, 1)
        thick = self.render_char(text, 2)
        glyph.shadows = [None, thin, thick]
        return glyph

    def render_char(self, text, type):
        char = u'⑨' if self.font.password else text[0]
        asc = ord(char)
        font = self.font
        suffix = ('BLOAT', 'SHADOWTHIN', 'SHADOWTHICK')[type]

        if font.size == 9:
            suffix = '12' + suffix
        else:
            suffix = '16' + suffix

        if char in u'♠♥♣♦':
            # special case for suits
            i = u'♠♥♣♦'.index(char)
            if font.size == 9:
                h = 12
                grid = L('c-suit12')
            else:
                h = 16
                grid = L('c-suit16')

            glyph = font.create_glyph(grid[i])
            glyph.set_bearings(1, -2, h + 1)
            return glyph

        elif char == u'\u200b':
            glyph = font.create_glyph(
                pyglet.image.ImageData(1, 1, 'RGBA', '\xFF'*4)
            )
            glyph.set_bearings(0, 0, 0)
            glyph.vertices = (0, 0, 0, 0)
            return glyph

        elif asc < 128:  # ASCII
            h = int(font.size*4/3)
            w = h // 2
            w += 4
            h += 4
            datasz = int(ceil(w/8.))*h

            fontdata = L('c-font')['ASC%s' % suffix]
            loc = asc * datasz
            data = fontdata[loc:loc+datasz]
            i = Image.fromstring('1', (w, h), data).convert('L')
            bbox = i.getbbox()
            if bbox:
                adj = 2 - type  # normal = 0, thinshadow = 1, thickshadow = 2
                bbox = (bbox[0] - adj, 0, bbox[2] + adj, h)
                i = i.crop(bbox)
                w = bbox[2] - bbox[0]
            # else: space/return/etc..

        else:  # GBK
            w = h = int(font.size*4/3) + 4
            datasz = int(ceil(w/8.))*h
            try:
                gbk = char.encode('gbk')
            except UnicodeEncodeError:
                gbk = u'⑨'.encode('gbk')
            rol = (256 + ord(gbk[0]) - 0x81) & 0xff
            col = (256 + ord(gbk[1]) - 0x40) & 0xff
            loc = rol * self.gbk_cols + col
            loc *= datasz
            fontdata = L('c-font')['GBK%s' % suffix]
            data = fontdata[loc:loc+datasz]
            i = Image.fromstring('1', (w, h), data).convert('L')

        ii = i
        if self.font.bold:
            ii = Image.new('L', (w, h))
            ii.paste(i, (1, 0))
            ii.paste(i, (0, 0), i)

        white = Image.new('L', ii.size, 255)
        final = Image.merge('RGBA', (white, white, white, ii))

        img = pyglet.image.ImageData(w, h, 'RGBA', final.tostring())
        glyph = self.font.create_glyph(img)
        glyph.set_bearings(2, -2, w - 4 + 1)
        t = list(glyph.tex_coords)
        glyph.tex_coords = t[9:12] + t[6:9] + t[3:6] + t[:3]
        glyph.character = char
        return glyph


class AncientPixFont(Font):
    glyph_renderer_class = AncientPixGlyphRenderer
    texture_width = 1024
    texture_height = 2048
    _font_texture = []

    @property
    def textures(self):
        if not AncientPixFont._font_texture:
            AncientPixFont._font_texture = [self.texture_class.create(self.texture_width, self.texture_height)]

        return self._font_texture

    @textures.setter
    def textures(self, val):
        pass

    def __init__(self, name, size, bold=False, italic=False, dpi=None):
        Font.__init__(self)
        if size != 9:
            size = 12

        self._size = size
        self.bold = bold
        self.italic = False

        self.password = (name == 'AncientPixPassword')

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, val):
        pass

    @property
    def ascent(self):
        return int(self.size*4/3) + 1

    @property
    def descent(self):
        return 0

    @staticmethod
    def have_font(name):
        return name in ('AncientPix', 'AncientPixPassword')

    @staticmethod
    def add_font_data(data):
        pass
