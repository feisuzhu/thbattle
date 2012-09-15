# -*- coding: utf-8 -*-

import pyglet
from utils import extendclass

class TextureExtension(pyglet.image.Texture):
    __metaclass__ = extendclass

    def get_t4f_v4f_vertices(self, x, y, z=0, width=None, height=None, tilt=0):
        t = self.tex_coords
        x1 = x - self.anchor_x
        y1 = y - self.anchor_y
        x2 = x1 + (width is None and self.width or width)
        y2 = y1 + (height is None and self.height or height)
        return [
             t[0],  t[1],  t[2],  1.,
             x1,    y1,    z+tilt,1.,
             t[3],  t[4],  t[5],  1.,
             x2,    y1,    z,     1.,
             t[6],  t[7],  t[8],  1.,
             x2,    y2,    z,     1.,
             t[9],  t[10], t[11], 1.,
             x1,    y2,    z+tilt,1.
        ]

    def get_t2c4n3v3_vertices(self, rgba, x, y, z=0, width=None, height=None, tilt=0):
        t = self.tex_coords
        r, g, b, a = rgba
        x1 = x - self.anchor_x
        y1 = y - self.anchor_y
        x2 = x1 + (width is None and self.width or width)
        y2 = y1 + (height is None and self.height or height)
        return [
            t[0],  t[1],  r,  g,  b,  a,  0,  0,  1,  x1,  y1,  z+tilt,
            t[3],  t[4],  r,  g,  b,  a,  0,  0,  1,  x2,  y1,  z,
            t[6],  t[7],  r,  g,  b,  a,  0,  0,  1,  x2,  y2,  z,
            t[9],  t[10], r,  g,  b,  a,  0,  0,  1,  x1,  y2,  z+tilt,
        ]

    def get_quad_vertices(self, x, y, z=0, width=None, height=None, tilt=0):
        x1 = x - self.anchor_x
        y1 = y - self.anchor_y
        x2 = x1 + (width is None and self.width or width)
        y2 = y1 + (height is None and self.height or height)
        return [
             x1,    y1,    z+tilt,
             x2,    y1,    z,
             x2,    y2,    z,
             x1,    y2,    z+tilt,
        ]

    def blit_nobind(self, x, y, z=0, width=None, height=None, tilt=0):
        from pyglet.gl import glInterleavedArrays, glDrawArrays, \
            GL_T4F_V4F, GL_QUADS, GLfloat
        array = (GLfloat * 32)()
        array[:] = self.get_t4f_v4f_vertices(x, y, z, width, height, tilt)
        glInterleavedArrays(GL_T4F_V4F, 0, array)
        glDrawArrays(GL_QUADS, 0, 4)

    def bind(self):
        from pyglet.gl import glBindTexture, glEnable, glPushAttrib, GL_ENABLE_BIT
        glPushAttrib(GL_ENABLE_BIT)
        glEnable(self.target)
        glBindTexture(self.target, self.id)

    def unbind(self):
        from pyglet.gl import glPopAttrib
        glPopAttrib()

    def __enter__(self):
        self.bind()
        return self

    def __exit__(self, *exc_values):
        self.unbind()

__all__ = ['']
