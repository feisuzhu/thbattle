# -*- coding: utf-8 -*-
# Convert QQYXS's mif animation to png & desc file

import sys

try:
    fn = sys.argv[1]
except IndexError:
    print 'Usage: mif2png.py <filename>'
    sys.exit(1)

print 'Converting %s' % fn

import Image, ImageDraw, os
from struct import unpack

f = open(fn, 'rb')

FRAME_ANIM = 7
FRAME_SINGLE = 3

_, frame_width, frame_height, frame_type, frame_count = \
    unpack('IIIII', f.read(4*5))

img_size = frame_width * frame_height

img = Image.new('RGBA', (frame_width*frame_count, frame_height))

def parse565a(i, a):
    r = ((0xF800 & i) >> 11) << 3
    g = ((0x07E0 & i) >> 5) << 2
    b = ((0x001F & i) >> 0) << 3
    return (r,g,b,min(a<<3, 255))

def convert(imgdata, alpha, sz):
    #sz = len(alpha)
    imgdata = unpack('H'*sz, imgdata)
    alpha = unpack('B'*sz, alpha)
    pixels = [parse565a(i, a) for i, a in zip(imgdata, alpha)]
    return pixels

atlist = []
for i in xrange(frame_count):
    if frame_type == FRAME_ANIM:
        animtime, = unpack('I', f.read(4))
        atlist.append(animtime)
    elif frame_type == FRAME_SINGLE:
        assert frame_count == 1
    imgdata = f.read(img_size*2)
    alpha = f.read(img_size)
    pixels = convert(imgdata, alpha, img_size)
    p = 0
    for y in xrange(frame_height):
        for x in xrange(i*frame_width, (i+1)*frame_width):
            img.putpixel((x, y), pixels[p])
            p += 1

img.save('%s.png' % fn)
open('%s.desc.py' % fn, 'w').write(
    '%s_animtime = %s' % (os.path.basename(fn), repr(atlist))
)
