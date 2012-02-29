# -*- coding: utf-8 -*-

import pyglet
from pyglet.font.base import GlyphRenderer, Font, FontException
from math import ceil

class AncientPixGlyphRenderer(GlyphRenderer):
    gbk_cols = 191
    gbk_rows = 126
    def __init__(self, font):
        GlyphRenderer.__init__(self, font)
        self.font = font

    def render(self, text):
        h = int(self.font.size*4/3)
        w = h
        char = text[0]
        asc = ord(char)
        datasz = int(ceil(w/8.))*h
        if asc < 128: # ASCII
            w /= 2
            datasz /= 2
            fontdata = self.font.fontdata['ASC%d' % h]
            loc = asc*datasz
            data = fontdata[loc:loc+datasz]
        else: #GBK
            try:
                gbk = char.encode('gbk')
            except UnicodeEncodeError:
                gbk = u'⑨'.encode('gbk')
            rol = (256 + ord(gbk[0]) - 0x81) & 0xff
            col = (256 + ord(gbk[1]) - 0x40) & 0xff
            loc = rol * self.gbk_cols + col
            loc *= datasz
            fontdata = self.font.fontdata['GBK%d' % h]
            data = fontdata[loc:loc+datasz]

        import Image
        data = Image.fromstring('1', (w, h), data).convert('L').tostring()
        img = pyglet.image.ImageData(w, h, 'A', data)
        glyph = self.font.create_glyph(img)
        glyph.set_bearings(0, 0, w)
        t = list(glyph.tex_coords)
        glyph.tex_coords = t[9:12] + t[6:9] + t[3:6] + t[:3]
        return glyph
        # bold # is with FBO(tex): tex.blit(1,0) safe?
        # ----

class AncientPixFont(Font):
    glyph_renderer_class = AncientPixGlyphRenderer
    from ..resource import font as fontdata

    def __init__(self, name, size, bold=False, italic=False, dpi=None):
        Font.__init__(self)
        if size != 9:
            size = 12

        self._size = size
        self.bold = bold

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, val):
        pass

    @property
    def ascent(self):
        return int(self.size*4/3)

    @property
    def descent(self):
        return 0

    @staticmethod
    def have_font(name):
        return name == 'AncientPix'

    @staticmethod
    def add_font_data(data):
        pass
