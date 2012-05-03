# -*- coding: utf-8 -*-
class DataHolder(object):
    def __data__(self):
        return self.__dict__

    @staticmethod
    def parse(dd):
        new = DataHolder()
        for k, v in dd.items():
            if isinstance(v, dict):
                setattr(new, k, DataHolder.parse(v))
            elif isinstance(v, (list, tuple, set, frozenset)):
                setattr(new, k, type(v)(
                    DataHolder.parse(lv) if isinstance(lv, dict) else lv
                    for lv in v
                ))
            else:
                setattr(new, k, v)
        return new

class BatchList(list):
    def __getattribute__(self, name):
        try:
            list_attr = list.__getattribute__(self, name)
            return list_attr
        except AttributeError:
            pass

        return list.__getattribute__(self, '__class__')(
            getattr(i, name) for i in self
        )

    def __call__(self, *a, **k):
        return list.__getattribute__(self, '__class__')(
            f(*a, **k) for f in self
        )

    def exclude(self, elem):
        nl = list.__getattribute__(self, '__class__')(self)
        nl.remove(elem)
        return nl

    def rotate_to(self, elem):
        i = self.index(elem)
        n = len(self)
        return self.__class__((self*2)[i:i+n])

class IRP(object):
    '''I/O Request Packet'''
    complete_tag = object()
    def __init__(self):
        from gevent.queue import Queue
        self.queue = Queue()

    def complete(self):
        from gevent_extension import the_hub
        the_hub.interrupt(self.queue.put, self.complete_tag)

    def wait(self):
        for f in self.queue:
            if f is self.complete_tag:
                break
            else:
                f()

    def do_callback(self, func):
        from gevent_extension import the_hub
        the_hub.interrupt(self.queue.put, func)

class ScissorBox(object):
    exc = Exception('ScissorBox Invalid')
    def __init__(self, con, x, y, w, h):
        ax, ay = con.abs_coords()
        self.box = (x+ax, y+ay, w, h)

    def __enter__(self):
        from utils import Rect
        from pyglet.gl import GLint, glGetIntegerv, GL_SCISSOR_BOX, glScissor
        ob = (GLint*4)()
        glGetIntegerv(GL_SCISSOR_BOX, ob)
        ob = list(ob)
        box = [int(i) for i in self.box]
        nb = Rect(*ob).intersect(Rect(*box))
        if nb:
            glScissor(nb.x, nb.y, nb.width, nb.height)
        self.ob, self.nb = ob, nb
        return self

    def __exit__(self, exc_type, exc_value, tb):
        if exc_value is self.exc:
            return True
        else:
            from pyglet.gl import glScissor
            glScissor(*self.ob)

    def break_if_invalid(self):
        if not self.nb:
            raise self.exc

class CheckFailed(Exception): pass

def check(b):
    if not b:
        raise CheckFailed

def check_type(pattern, obj):
    if isinstance(pattern, (list, tuple)):
        check(isinstance(obj, (list, tuple)))
        if len(pattern) == 2 and pattern[-1] is Ellipsis:
            cls = pattern[0]
            for v in obj:
                check(isinstance(v, cls))
        else:
            check(len(pattern) == len(obj))
            for cls, v in zip(pattern, obj):
                check_type(cls, v)
    else:
        check(isinstance(obj, pattern))

class Framebuffer(object):
    def __init__(self, texture=None):
        from pyglet import gl
        fbo_id = gl.GLuint(0)
        gl.glGenFramebuffersEXT(1, gl.byref(fbo_id))
        self.fbo_id = fbo_id
        self._texture = None
        if texture:
            self.bind()
            self.texture = texture
            self.unbind()


    def _get_texture(self):
        return self._texture

    def _set_texture(self, t):
        self._texture = t
        from pyglet import gl
        gl.glFramebufferTexture2DEXT(
            gl.GL_FRAMEBUFFER_EXT,
            gl.GL_COLOR_ATTACHMENT0_EXT,
            t.target, t.id, 0,
        )
        gl.glViewport(0, 0, t.width, t.height)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluOrtho2D(0, t.width, 0, t.height)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

    texture = property(_get_texture, _set_texture)

    def __enter__(self):
        self.bind()

    def __exit__(self, exc_type, exc_value, tb):
        self.unbind()

    def bind(self):
        from pyglet import gl
        t = self.texture
        gl.glBindFramebufferEXT(gl.GL_DRAW_FRAMEBUFFER_EXT, self.fbo_id)
        gl.glPushAttrib(gl.GL_VIEWPORT_BIT | gl.GL_TRANSFORM_BIT)
        if t:
            gl.glViewport(0, 0, t.width, t.height)
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPushMatrix()
        if t:
            gl.glLoadIdentity()
            gl.gluOrtho2D(0, t.width, 0, t.height)
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPushMatrix()
        if t:
            gl.glLoadIdentity()

    def unbind(self):
        from pyglet import gl
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glPopAttrib()
        gl.glBindFramebufferEXT(gl.GL_DRAW_FRAMEBUFFER_EXT, 0)

    def __del__(self):
        from pyglet import gl
        gl.glDeleteFramebuffersEXT(1, self.fbo_id)

    def bind_as_readbuffer(self):
        from pyglet import gl
        gl.glBindFramebufferEXT(gl.GL_READ_FRAMEBUFFER_EXT, self.fbo_id)

    def unbind_as_readbuffer(self):
        from pyglet import gl
        gl.glBindFramebufferEXT(gl.GL_READ_FRAMEBUFFER_EXT, 0)

    def blit_from_current_readbuffer(self, src_box, dst_box=None, mask=None, _filter=None):
        from pyglet import gl
        mask = mask if mask else gl.GL_COLOR_BUFFER_BIT
        _filter = _filter if _filter else gl.GL_LINEAR

        if not dst_box:
            dst_box = (0, 0, src_box[2] - src_box[0], src_box[3] - src_box[1])

        args = tuple(src_box) + tuple(dst_box) + (mask, _filter)
        gl.glBlitFramebufferEXT(*args)

def dilate(im, color):
    import pyglet
    w, h = im.width, im.height
    _ori = bytearray(im.get_data('A', w))
    _new = bytearray(_ori)

    class accesser(object):
        def __init__(self, arr):
            self.arr = arr
        def __getitem__(self, val):
            x, y = val
            if not (0 <= x < w and 0 <= y < h):
                return 0
            else:
                return self.arr[y*w + x]

        def __setitem__(self, loc, val):
            x, y = loc
            self.arr[y*w + x] = val

    ori = accesser(_ori)
    new = accesser(_new)

    for x in xrange(w):
        for y in xrange(h):
            if any([
                ori[x, y],
                ori[x-1, y], ori[x+1, y], ori[x, y-1], ori[x, y+1],
                ori[x-1, y-1], ori[x-1, y+1], ori[x+1, y-1], ori[x+1, y+1],
            ]):
                new[x, y] = True
            else:
                new[x, y] = False

    color = ''.join([chr(i) for i in color]) + '\xff'
    tr = ['\x00'*4, color]
    new = ''.join([tr[i] for i in _new])
    new = pyglet.image.ImageData(w, h, 'RGBA', new)
    return new
