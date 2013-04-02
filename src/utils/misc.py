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

    def exclude(self, *elems):
        nl = list.__getattribute__(self, '__class__')(self)
        for e in elems:
            nl.remove(e)
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
        # from gevent_extension import the_hub
        self.queue.put(self.complete_tag)
        # the_hub.interrupt(self.queue.put, self.complete_tag)

    def wait(self):
        self.queue.get()


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
    current_fbo = None
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
        try:
            gl.glFramebufferTexture2DEXT(
                gl.GL_FRAMEBUFFER_EXT,
                gl.GL_COLOR_ATTACHMENT0_EXT,
                t.target, t.id, 0,
            )
        except gl.GLException as e:
            # HACK: Some Intel card return errno == 1286L
            # which means GL_INVALID_FRAMEBUFFER_OPERATION_EXT
            # but IT ACTUALLY WORKS FINE!!
            pass

        gl.glViewport(0, 0, t.width, t.height)

        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glLoadIdentity()
        gl.gluOrtho2D(0, t.width, 0, t.height)

        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glLoadIdentity()

        # ATI cards hack
        gl.glBegin(gl.GL_LINES)
        gl.glEnd()
        # --------------

    texture = property(_get_texture, _set_texture)

    def __enter__(self):
        self.bind()

    def __exit__(self, exc_type, exc_value, tb):
        self.unbind()

    def bind(self):
        assert Framebuffer.current_fbo is None
        from pyglet import gl
        t = self.texture
        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, self.fbo_id)
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

        Framebuffer.current_fbo = self

    def unbind(self):
        from pyglet import gl
        gl.glMatrixMode(gl.GL_MODELVIEW)
        gl.glPopMatrix()
        gl.glMatrixMode(gl.GL_PROJECTION)
        gl.glPopMatrix()
        gl.glPopAttrib()
        gl.glBindFramebufferEXT(gl.GL_FRAMEBUFFER_EXT, 0)
        Framebuffer.current_fbo = None

    def __del__(self):
        from pyglet import gl
        try:
            gl.glDeleteFramebuffersEXT(1, self.fbo_id)
        except:
            pass

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

TRANS = {
    124: 101, #LOAD_FAST: LOAD_NAME,
    125: 90, #STORE_FAST: STORE_NAME,
    126: 91, #DELETE_FAST: DELETE_NAME,
}

def pinnable(*scopevars):
    def _pinnable(f):
        c = f.__code__

        assert c.co_argcount == 0
        assert len(c.co_freevars) == 0
        assert len(c.co_cellvars) == 0

        names = c.co_names
        vnames = c.co_varnames

        len_names = len(names)

        bcode = [ord(i) for i in c.co_code]
        nbcode = []
        i = 0
        n = len(bcode)
        while i < n:
            op = bcode[i]
            nop = TRANS.get(op, op)
            i += 1
            if op >= 90: # HAVE_ARGUMENT
                if op in (124, 125, 126): # (LOAD|STORE|DELETE)_FAST opcodes
                    nbcode.append(nop)
                    arg = bcode[i] + (bcode[i+1] << 8)
                    arg += len_names
                    nbcode.extend([arg & 255, (arg >> 8) & 255])
                elif op == 116: # LOAD_GLOBAL
                    arg = bcode[i] + (bcode[i+1] << 8)
                    gname = names[arg]
                    if gname in scopevars:
                        nbcode.append(101) # LOAD_NAME
                    else:
                        nbcode.append(nop)
                    nbcode.extend(bcode[i:i+2])
                else:
                    nbcode.append(nop)
                    nbcode.extend(bcode[i:i+2])
                i += 2
            else:
                nbcode.append(nop)

        nbcode = ''.join(chr(i) for i in nbcode)
        newco = type(c)(
            0, 0, c.co_stacksize, c.co_flags & (~2), # CO_NEWLOCALS
            nbcode, c.co_consts, names + vnames,
            tuple(), c.co_filename, '<pinnable %s>' % f.__name__,
            c.co_firstlineno, c.co_lnotab
        )
        return newco
    return _pinnable

def remove_dups(s):
    seen = set()
    for i in s:
        if i not in seen:
            yield i
            seen.add(i)

@property
def __mixins(self):
    return self.__class__.__bases__

def __prev_mixin(self, this):
    mixins = self.mixins

    try:
        i = mixins.index(this) + 1
    except ValueError:
        return None

    if i >= len(mixins):
        return None

    return mixins[i]

cls_cache = {}
def classmix(*_classes):
    classes = []
    for c in _classes:
        if hasattr(c, '_is_mixedclass'):
            classes.extend(c.__bases__)
        else:
            classes.append(c)

    classes = tuple(remove_dups(classes))
    cached = cls_cache.get(classes, None)
    if cached: return cached

    clsname = ', '.join(cls.__name__ for cls in classes)
    new_cls = type(
        'Mixed(%s)' % clsname,
        classes,
        {
            'mixins': __mixins,
            'prev_mixin': __prev_mixin,
            '_is_mixedclass': True,
        }
    )
    cls_cache[classes] = new_cls
    return new_cls

from functools import wraps

def hook(module):
    def inner(hooker):
        funcname = hooker.__name__
        hookee = getattr(module, funcname)
        @wraps(hookee)
        def real_hooker(*args, **kwargs):
            return hooker(hookee, *args, **kwargs)
        setattr(module, funcname, real_hooker)
        return real_hooker
    return inner

def gif_to_animation(giffile):
    import pyglet
    import Image

    im = Image.open(giffile)

    dur = []
    framedata = []

    while True:
        dur.append(im.info['duration'])
        framedata.append(im.convert('RGBA').tostring())
        try:
            im.seek(im.tell()+1)
        except:
            break

    dur[0] = 100

    w, h = im.size

    frames = []
    for d, data in zip(dur, framedata):
        img = pyglet.image.ImageData(w, h, 'RGBA', data, pitch=-w*4)
        img.anchor_x, img.anchor_y = img.width // 2, img.height // 2
        frames.append(
            pyglet.image.AnimationFrame(img, d/1000.0)
        )

    anim = pyglet.image.Animation(frames)
    anim.width, anim.height = w, h

    return anim

class DisplayList(object):
    compiled = False
    def __init__(self):
        from pyglet import gl
        self._list_id = gl.glGenLists(1)

    def __enter__(self):
        self.compiled = True
        from pyglet import gl
        gl.glNewList(self._list_id, gl.GL_COMPILE)
        return self

    def __exit__(self, *exc_args):
        from pyglet import gl
        gl.glEndList()

    def __call__(self):
        if not self.compiled:
            return Exception('Not compiled!')
        from pyglet import gl
        gl.glCallList(self._list_id)

    def __del__(self):
        from pyglet import gl
        try:
            gl.glDeleteLists(self._list_id, 1)
        except:
            pass

def extendclass(clsname, bases, _dict):
    for cls in bases:
        for key, value in _dict.items():
            if key == '__module__':
                continue
            setattr(cls, key, value)


def textsnap(text, font, l):
    tl = 0
    for i, g in enumerate(font.get_glyphs(text)):
        if tl + g.advance > l:
            break
        tl += g.advance
    else:
        return text

    return text[:i]


def textwidth(text, font):
    return sum([g.advance for g in font.get_glyphs(text)])


def partition(pred, l):
    t = filter(pred, l)
    f = filter(lambda v: not pred(v), l)
    return t, f


import functools

def track(f):
    @functools.wraps(f)
    def _wrapper(*a, **k):
        print '%s: %s %s' % (f.__name__, a, k)
        return f(*a, **k)
    return _wrapper


class _Enum(object):
    def __init__(self, forward, reverse):
        self.forward = forward
        self.reverse = reverse

    def __getattr__(self, name):
        return self.forward[name]

    def rlookup(self, v):
        return self.reverse[v]


class EnumMeta(type):
    def __new__(cls, clsname, bases, _dict):
        if bases == (object,):
            return type.__new__(cls, clsname, bases, _dict)

        forward = {}
        reverse = {}
        _dict.pop('__module__')
        for k, v in _dict.iteritems():
            forward[k] = v
            reverse[v] = k

        return _Enum(forward, reverse)


class Enum(object):
    __metaclass__ = EnumMeta


def flatten(l):
    rst = []
    def _flatten(sl):
        for i in sl:
            if isinstance(i, (list, tuple)):
                _flatten(i)
            else:
                rst.append(i)

    _flatten(l)
    return rst


def group_by(l, keyfunc):
    if not l: return []

    grouped = []
    group = []

    lastkey = keyfunc(l[0])
    for i in l:
        k = keyfunc(i)
        if k == lastkey:
            group.append(i)
        else:
            grouped.append(group)
            group = [i]
            lastkey = k

    if group:
        grouped.append(group)

    return grouped


def instantiate(cls):
    return cls()


def surpress_and_restart(f):
    def wrapper(*a, **k):
        while True:
            try:
                return f(*a, **k)
            except Exception as e:
                import logging
                log = logging.getLogger('misc')
                log.exception(e)

    return wrapper


def swallow(f):
    def wrapper(*a, **k):
        try:
            return f(*a, **k)
        except:
            pass

    return wrapper
