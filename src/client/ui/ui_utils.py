# -*- coding: utf-8 -*-
import pyglet
from pyglet.gl import *
from resource import border as border_res

def border(x, y, w, h):
    cnw, cne, csw, cse, en, ew, es, ee, fill = border_res
    sz = cnw.height
    if w < sz * 2 or w < sz * 2:
        return # not impl

    glColor3f(1, 1, 1)
    x0, y0 = x + w - sz, y + h - sz
    csw.blit(x, y)
    cnw.blit(x, y0)
    cse.blit(x0, y)
    cne.blit(x0, y0)

    w1 = w - 2 * sz
    h1 = h - 2 * sz

    x1, x2 = x + sz, x + w1
    y1, y2 = y, y + sz + h1

    en.get_region(0, 0, w1, sz).blit(x1, y2)
    es.get_region(0, 0, w1, sz).blit(x1, y1)

    x1, x2 = x, x + sz + w1
    y1, y2 = y + sz, y + w1

    ew.get_region(0, 0, sz, h1).blit(x1, y1)
    ee.get_region(0, 0, sz, h1).blit(x2, y1)

    fill.get_region(0, 0, w1, h1).blit(x + sz, y + sz)
