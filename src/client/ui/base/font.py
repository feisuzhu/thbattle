# -*- coding: utf-8 -*-

import pyglet
from pyglet.gl import GL_ALPHA, GL_TEXTURE_2D
from pyglet.font.base import GlyphRenderer, Font, FontException
from math import ceil
import Image


class AncientPixGlyphRenderer(GlyphRenderer):
    gbk_cols = 191
    gbk_rows = 126
    def __init__(self, font):
        GlyphRenderer.__init__(self, font)
        self.font = font

    def render(self, text):
        char = u'⑨' if self.font.password else text[0]
        asc = ord(char)
        font = self.font
        if font.italic:
            if font.bold:
                suffix = 'SHADOWTHICK'
            else:
                suffix = 'SHADOWTHIN'
        else:
            suffix = 'BLOAT'

        if font.size == 9:
            suffix = '12' + suffix
        else:
            suffix = '16' + suffix

        if char in u'♠♡♣♢':
            # special case for suits
            i = suit.index(char)
            if font.size == 9:
                grid = font.suit12
            else:
                grid = font.suit16

            glyph = font.create_glyph(grid[i])
            glyph.set_bearings(1, -2, h + 1)
            return glyph

        elif asc < 128:  # ASCII
            h = int(font.size*4/3)
            w = h // 2
            w += 4
            h += 4
            datasz = int(ceil(w/8.))*h

            fontdata = self.font.fontdata['ASC%s' % suffix]
            loc = asc * datasz
            data = fontdata[loc:loc+datasz]
            i = Image.fromstring('1', (w, h), data).convert('L')
            bbox = i.getbbox()
            if bbox:
                bbox = (bbox[0] - 2, 0, bbox[2] + 2, h)
                print bbox
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
            fontdata = self.font.fontdata['GBK%s' % suffix]
            data = fontdata[loc:loc+datasz]
            i = Image.fromstring('1', (w, h), data).convert('L')

        ii = i
        if self.font.bold:
            ii = Image.new('L', (w, h))
            ii.paste(i, (1, 0))
            ii.paste(i, (0, 0), i)

        img = pyglet.image.ImageData(w, h, 'A', ii.tostring())
        glyph = self.font.create_glyph(img)
        glyph.set_bearings(2, -2, w - 4 + 1)
        t = list(glyph.tex_coords)
        glyph.tex_coords = t[9:12] + t[6:9] + t[3:6] + t[:3]
        return glyph


class AncientPixFont(Font):
    glyph_renderer_class = AncientPixGlyphRenderer
    texture_width = 1024
    texture_height = 1024
    _font_texture = [pyglet.image.Texture.create_for_size(
        GL_TEXTURE_2D, texture_width, texture_height, GL_ALPHA,
    )]

    @property
    def texture(self):
        return self._font_texture

    @texture.setter
    def texture(self, val):
        pass

    @property
    def fontdata(self):
        # Lazy loading
        from ..resource import font as fontdata
        return fontdata

    @property
    def suit12(self):
        # Lazy loading
        from ..resource import suit12
        return suit12

    @property
    def suit16(self):
        # Lazy loading
        from ..resource import suit16
        return suit16

    def __init__(self, name, size, bold=False, italic=False, dpi=None):
        Font.__init__(self)
        if size != 9:
            size = 12

        self._size = size
        self.bold = bold
        self.italic = italic

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
