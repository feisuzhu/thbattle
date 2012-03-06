# -*- coding: utf-8 -*-

from base.shader import *

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
                    for(float oy=-2.0; oy<=2.0; oy+=1.0) {
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
    FontShadowThick = FontShadow = DummyShaderProgram()

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
    Grayscale = DummyShaderProgram()

DummyShader = DummyShaderProgram()
