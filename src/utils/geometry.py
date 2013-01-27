class Rect(object):
    '''
    This class is copied from pyglet/contrib/wydget
    '''
    def __init__(self, x, y, width, height):
        self.x = x; self.y = y
        self.width = width; self.height = height

    def __nonzero__(self):
        return bool(self.width and self.height)

    def __repr__(self):
        return 'Rect(xy=%.4g,%.4g; wh=%.4g,%.4g)'%(self.x, self.y,
            self.width, self.height)

    def __eq__(self, other):
        return (self.x == other.x and self.y == other.y and
            self.width == other.width and  self.height == other.height)

    def __ne__(self, other):
        return not (self == other)

    def copy(self):
        return self.__class__(self.x, self.y, self.width, self.height)

    def clippedBy(self, other):
        i = self.intersect(other)
        if i is None: return True
        if i.x > self.x: return True
        if i.y > self.y: return True
        if i.width < self.width: return True
        if i.height < self.height: return True
        return False

    def intersect(self, other):
        s_tr_x, s_tr_y = self.topright
        o_tr_x, o_tr_y = other.topright
        bl_x = max(self.x, other.x)
        bl_y = max(self.y, other.y)
        tr_x = min(s_tr_x, o_tr_x)
        tr_y = min(s_tr_y, o_tr_y)
        w, h = max(0, tr_x-bl_x), max(0, tr_y-bl_y)
        if not w or not h:
            return None
        return self.__class__(bl_x, bl_y, w, h)

    def get_top(self): return self.y + self.height
    def set_top(self, y): self.y = y - self.height
    top = property(get_top, set_top)

    def get_bottom(self): return self.y
    def set_bottom(self, y): self.y = y
    bottom = property(get_bottom, set_bottom)

    def get_left(self): return self.x
    def set_left(self, x): self.x = x
    left = property(get_left, set_left)

    def get_right(self): return self.x + self.width
    def set_right(self, x): self.x = x - self.width
    right = property(get_right, set_right)

    def get_center(self):
        return (self.x + self.width//2, self.y + self.height//2)
    def set_center(self, center):
        x, y = center
        self.x = x - self.width//2
        self.y = y - self.height//2
    center = property(get_center, set_center)

    def get_midtop(self):
        return (self.x + self.width//2, self.y + self.height)
    def set_midtop(self, midtop):
        x, y = midtop
        self.x = x - self.width//2
        self.y = y - self.height
    midtop = property(get_midtop, set_midtop)

    def get_midbottom(self):
        return (self.x + self.width//2, self.y)
    def set_midbottom(self, midbottom):
        x, y = midbottom
        self.x = x - self.width//2
        self.y = y
    midbottom = property(get_midbottom, set_midbottom)

    def get_midleft(self):
        return (self.x, self.y + self.height//2)
    def set_midleft(self, midleft):
        x, y = midleft
        self.x = x
        self.y = y - self.height//2
    midleft = property(get_midleft, set_midleft)

    def get_midright(self):
        return (self.x + self.width, self.y + self.height//2)
    def set_midright(self, midright):
        x, y = midright
        self.x = x - self.width
        self.y = y - self.height//2
    midright = property(get_midright, set_midright)

    def get_topleft(self):
        return (self.x, self.y + self.height)
    def set_topleft(self, pos):
        x, y = pos
        self.x = x
        self.y = y - self.height
    topleft = property(get_topleft, set_topleft)

    def get_topright(self):
        return (self.x + self.width, self.y + self.height)
    def set_topright(self, pos):
        x, y = pos
        self.x = x - self.width
        self.y = y - self.height
    topright = property(get_topright, set_topright)

    def get_bottomright(self):
        return (self.x + self.width, self.y)
    def set_bottomright(self, pos):
        x, y = pos
        self.x = x - self.width
        self.y = y
    bottomright = property(get_bottomright, set_bottomright)

    def get_bottomleft(self):
        return (self.x, self.y)
    def set_bottomleft(self, pos):
        self.x, self.y = pos
    bottomleft = property(get_bottomleft, set_bottomleft)

    def glLineStripVertices(self):
        x, y, w, h = self.x, self.y, self.width, self.height
        x1, y1 = x + w, y + h
        return [ x, y, x1, y, x1, y1, x, y1, x, y ]

    def glQuadsVertices(self):
        x, y, w, h = self.x, self.y, self.width, self.height
        x1, y1 = x + w, y + h
        return [ x, y, x1, y, x1, y1, x, y1 ]

def rect_to_dict(rect):
    x, y, w, h = rect
    return dict(
        x=x, y=y,
        width=w, height=h,
    )

def rectv2f(x, y, w, h, ax=0, ay=0):
    x1, y1 = x + w, y + h
    return [ ax+x, ay+y, ax+x1, ay+y, ax+x1, ay+y1, ax+x, ay+y1 ]

def rrectv2f(x, y, w, h, ax=0, ay=0):
    x1, y1 = x + w, y + h
    return [ ax+x, ay+y, ax+x, ay+y1, ax+x1, ay+y1, ax+x1, ay+y ]
