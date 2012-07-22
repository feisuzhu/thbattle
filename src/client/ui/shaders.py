# -*- coding: utf-8 -*-

from base.shader import *
from pyglet.gl import gl_info

have = gl_info.have_version

DummyShader = DummyShaderProgram()

import logging

log = logging.getLogger('shaders')

try:
    thick = '''
        %s
        uniform sampler2D tex;
        uniform vec4 shadow_color;
        void main()
        {
            vec4 sample = texture2D(tex, gl_TexCoord[0].xy);
            if(sample.a > 0.49) {
                gl_FragColor = gl_Color;
                return;
            } else {
                float x = gl_TexCoord[0].x;
                float y = gl_TexCoord[0].y;
                ivec2 size = textureSize%s(tex, 0);
                float w = float(size[0]);
                float h = float(size[1]);
                for(float ox=-2.0; ox<=2.0; ox+=1.0)
                    for(float oy=-1.0; oy<=1.0; oy+=1.0) {
                        if(texture2D(tex, vec2(x+ox/w, y+oy/h)).a >= 0.49) {
                            gl_FragColor = shadow_color;
                            return;
                        }
                    }
                for(float ox=-1.0; ox<=1.0; ox+=1.0)
                    for(float oy=-2.0; oy<=2.0; oy+=4.0) {
                        if(texture2D(tex, vec2(x+ox/w, y+oy/h)).a >= 0.49) {
                            gl_FragColor = shadow_color;
                            return;
                        }
                    }
                gl_FragColor = vec4(0.0, 0.0, 0.0, 0.0);
            }
        }
        '''

    if have(3, 1, 0):
        thick = thick % ('', '')
    else:
        thick = thick % ('#extension GL_EXT_gpu_shader4 : enable', '2D')

    FontShadowThick = ShaderProgram(FragmentShader(thick))

    thin = '''
        %s
        uniform sampler2D tex;
        uniform vec4 shadow_color;
        void main()
        {
            vec4 sample = texture2D(tex, gl_TexCoord[0].xy);
            if(sample.a > 0.49) {
                gl_FragColor = gl_Color;
                return;
            } else {
                float x = gl_TexCoord[0].x;
                float y = gl_TexCoord[0].y;
                ivec2 size = textureSize%s(tex, 0);
                float w = float(size[0]);
                float h = float(size[1]);
                float a = 0.0;
                a += texture2D(tex, vec2(x+1.0/w, y)).a;
                a += texture2D(tex, vec2(x-1.0/w, y)).a;
                a += texture2D(tex, vec2(x, y+1.0/h)).a;
                a += texture2D(tex, vec2(x, y-1.0/h)).a;
                gl_FragColor = a > 0.49 ? shadow_color : vec4(0.0, 0.0, 0.0, 0.0);
            }
        }
    '''

    if have(3, 1, 0):
        thin = thin % ('', '')
    else:
        thin = thin % ('#extension GL_EXT_gpu_shader4 : enable', '2D')

    FontShadow = ShaderProgram(FragmentShader(thin))

except Exception as e:
    if isinstance(e, ShaderError):
        log.error(e.infolog)
    else:
        log.exception(e)
    FontShadowThick = FontShadow = DummyShader

try:
    fshader = FragmentShader(
        '''
        uniform sampler2D tex;
        void main()
        {
            float l = dot(texture2D(tex, gl_TexCoord[0].xy), vec4(0.3, 0.59, 0.11, 0.0));
            gl_FragColor = vec4(l, l, l, 1.0);
        }
        '''
    )
    Grayscale = ShaderProgram(fshader)
except Exception as e:
    if isinstance(e, ShaderError):
        log.error(e.infolog)
    else:
        log.exception(e)
    Grayscale = DummyShader


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
            's += texture2D(tex, vec2(xy.x+(%d.0/size[0]), xy.y)) * %f;' % (i, v)
            for i, v in zip(xrange(-l, l+1), coef)
        )
    )
    GaussianBlurHorizontal = ShaderProgram(fshader)

    fshader = FragmentShader(
        src % '\n'.join(
            's += texture2D(tex, vec2(xy.x, xy.y+(%d.0/size[1]))) * %f;' % (i, v)
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
