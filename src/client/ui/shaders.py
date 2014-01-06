# -*- coding: utf-8 -*-

from base.shader import *
from pyglet.gl import gl_info

have = gl_info.have_version

import logging

log = logging.getLogger('shaders')


def _get_gaussian_coef(radius):
    from math import erfc
    a = 3.0 / radius * 0.707106781

    f = lambda x: 0.5*erfc(-x*a)

    l = [f(0.5 + i) - f(-0.5 + i) for i in xrange(radius+1)]
    l = [i for i in l if i>0.01]
    l1 = l[1:]
    l1.reverse()
    l = l1 + l
    s = sum(l)
    l = [i/s for i in l]
    return l

try:
    r = 9
    coef = _get_gaussian_coef(r)
    src = '''
        uniform sampler2D tex;
        uniform ivec2 size;
        void main()
        {
            vec2 xy = gl_TexCoord[0].xy;
            vec4 s = vec4(0.0, 0.0, 0.0, 0.0);
            %s
            gl_FragColor = vec4(s.rgb, 1.0);
        }
    '''
    l = len(coef)//2
    fshader = FragmentShader(
        src % '\n'.join(
            's += texture2D(tex, vec2(xy.x+(%d.0/float(size[0])), xy.y)) * %f;' % (i, v)
            for i, v in zip(xrange(-l, l+1), coef)
        )
    )
    GaussianBlurHorizontal = ShaderProgram(fshader)

    fshader = FragmentShader(
        src % '\n'.join(
            's += texture2D(tex, vec2(xy.x, xy.y+(%d.0/float(size[1])))) * %f;' % (i, v)
            for i, v in zip(xrange(-l, l+1), coef)
        )
    )
    GaussianBlurVertical = ShaderProgram(fshader)

except Exception as e:
    if isinstance(e, ShaderError):
        log.error(e.infolog)
    else:
        log.exception(e)
    GaussianBlurHorizontal = GaussianBlurVertical = DummyShader
