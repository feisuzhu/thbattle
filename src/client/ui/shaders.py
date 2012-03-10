# -*- coding: utf-8 -*-

from base.shader import *

DummyShader = DummyShaderProgram()

try:
    thick = FragmentShader('''
        #extension GL_EXT_gpu_shader4 : enable
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
                ivec2 size = textureSize2D(tex, 0);
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
    )
    FontShadowThick = ShaderProgram(thick)

    thin = FragmentShader('''
        #extension GL_EXT_gpu_shader4 : enable
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
                ivec2 size = textureSize2D(tex, 0);
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
    )
    FontShadow = ShaderProgram(thin)

except ShaderError as e:
    FontShadowThick = FontShadow = DummyShader

try:
    fshader = FragmentShader(
        '''
        void main()
        {
            float l = dot(gl_Color, vec4(0.3, 0.59, 0.11, 0.0));
            gl_FragColor = vec4(l, l, l, gl_Color.a);
        }
        '''
    )
    Grayscale = ShaderProgram(fshader)
except ShaderError as e:
    Grayscale = DummyShader


def _get_gaussian_coef(radius):
    from math import erfc
    inv_sigma = 3.0/radius
    def f(x):
        return 0.5*erfc(-x*inv_sigma*0.707106781)
    l = [f(0.5 + i) - f(-0.5 + i) for i in xrange(radius+1)]
    l1 = l[1:]
    l1.reverse()
    return l1 + l

try:
    r = 12
    coef = _get_gaussian_coef(r)
    src = '''
        uniform sampler2DRect tex;
        void main()
        {
            vec2 xy = gl_TexCoord[0].xy;
            vec4 s = vec4(0.0, 0.0, 0.0, 0.0);
            // s += texture2DRect(tex, vec2(xy.x-1.0, xy.y));
            %s
            gl_FragColor = s;
        }
    '''

    fshader = FragmentShader(
        src % '\n'.join(
            's += texture2DRect(tex, vec2(xy.x+(%d.0), xy.y)) * %f;' % (i, v)
            for i, v in zip(xrange(-r, r+1), coef)
        )
    )
    GaussianBlurHorizontal = ShaderProgram(fshader)

    fshader = FragmentShader(
        src % '\n'.join(
            's += texture2DRect(tex, vec2(xy.x, xy.y+(%d.0))) * %f;' % (i, v)
            for i, v in zip(xrange(-r, r+1), coef)
        )
    )
    GaussianBlurVertical = ShaderProgram(fshader)

except ShaderError as e:
    GaussianBlurHorizontal = GaussianBlurVertical = DummyShader
