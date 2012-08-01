# -*- coding: utf-8 -*-

from pyglet.gl import *

class ShaderError(Exception): pass

def _get_infolog(oid):
    buffer = create_string_buffer(3000)
    i = GLsizei(0)
    glGetInfoLogARB(
        oid, 3000, byref(i), cast(
            byref(buffer),
            POINTER(c_char)
        )
    )
    return buffer.value

class _Shader(object):
    def __init__(self, src):
        sid = False
        try:
            sid = glCreateShaderObjectARB(self.shader_type)
        except GLException:
            pass

        if not sid:
            raise ShaderError("Can't create shader object!")

        l = GLsizei(len(src))
        buf = create_string_buffer(src, len(src) + 10)
        pbuf = pointer(buf)
        glShaderSourceARB(
            sid, 1, cast(byref(pbuf), POINTER(POINTER(c_char))),
            byref(l)
        )
        glCompileShader(sid)
        v = GLint()
        glGetShaderiv(sid, GL_COMPILE_STATUS, byref(v))
        if not v:
            log = _get_infolog(sid)
            e = ShaderError("Error compiling shader!")
            e.infolog = log
            raise e

        self.sid = sid

class VertexShader(_Shader):
    shader_type = GL_VERTEX_SHADER_ARB

class FragmentShader(_Shader):
    shader_type = GL_FRAGMENT_SHADER_ARB

class _UniformAccesser(object):
    def __init__(self, prg):
        object.__setattr__(self, 'prg', prg)
        object.__setattr__(self, 'lookup', {})

    def __getattr__(self, name):
        prg = object.__getattribute__(self, 'prg')
        assert prg is ShaderProgram.shader_stack[-1]

        prg = prg.pid
        loc = self.lookup.get(name)
        if loc: return loc

        loc = glGetUniformLocationARB(prg, name)
        if loc == -1:
            raise ShaderError('No such uniform!')

        self.lookup[name] = loc
        return loc

    def __setattr__(self, name, value):
        loc = getattr(self, name)

        if not isinstance(value, (list, tuple)):
            value = (value, )

        t = type(value[0])
        t = {int:'i', float:'f'}.get(t)
        if not t:
            raise ShaderError('Unknown variable type!')

        n = len(value)
        fn = 'glUniform%d%s' % (n, t)
        from pyglet import gl
        func = getattr(gl, fn)

        func(loc, *value)

class _AttributeAccesser(object):
    def __init__(self, prg):
        object.__setattr__(self, 'prg', prg)

    def __getattr__(self, name):
        prg = object.__getattribute__(self, 'prg')
        assert prg is ShaderProgram.shader_stack[-1]
        prg = prg.pid

        loc = glGetAttribLocationARB(prg, name)
        if loc == -1:
            raise ShaderError('No such attribute!')

        return loc

class ShaderProgram(object):
    shader_stack = []
    def __init__(self, *shaders):
        pid = False
        try:
            pid = glCreateProgramObjectARB()
        except GLException:
            pass

        if not pid:
            raise ShaderError("Can't create program object!")

        for s in shaders:
            glAttachObjectARB(pid, s.sid)

        glLinkProgram(pid)

        v = GLint(0)
        glGetProgramiv(pid, GL_LINK_STATUS, byref(v))
        if not v:
            log = _get_infolog(sid)
            e = ShaderError("Error linking program!")
            e.infolog = log
            raise e

        self.pid = pid

        self.uniform = _UniformAccesser(self)
        self.attrib = _AttributeAccesser(self)

    def use(self):
        ShaderProgram.shader_stack.append(self)
        glUseProgramObjectARB(self.pid)

    def unuse(self):
        l = ShaderProgram.shader_stack
        p = l.pop()
        assert p is self
        if l:
            glUseProgramObjectARB(l[-1].pid)
        else:
            glUseProgramObjectARB(0)

    @classmethod
    def restore(cls):
        cls.shader_stack[:] = []
        glUseProgramObjectARB(0)

    def __enter__(self):
        self.use()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.unuse()

class DummyShaderProgram(object):
    def __init__(self, *a):
        from utils import DataHolder
        self.uniform = DataHolder()
        self.attrib = DataHolder()

    def use(self):
        pass

    def restore(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass
