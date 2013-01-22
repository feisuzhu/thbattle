#!/usr/bin/python
import math

from SimpleCV import *
import Image as PIL


def generate(filename, w, h):
    print filename
    data = open(filename).read()

    thin_file = open(filename + 'SHADOWTHIN', 'w')
    thick_file = open(filename + 'SHADOWTHICK', 'w')
    bloat_file = open(filename + 'BLOAT', 'w')

    linesize = int(math.ceil(w/8.0))
    charsize = linesize * h

    chars = [
        data[i*charsize:(i+1)*charsize]
        for i in xrange(len(data)/charsize)
    ]

    for char in chars:
        charimg = PIL.fromstring('1', (w, h), char)
        paste = PIL.new('1', (w+4, h+4))
        paste.paste(charimg, (2, 2))
        bloat_file.write(paste.tostring())

        img = Image(paste)
        img = img.convolve([
            [0, 1, 0],
            [1, 1, 1],
            [0, 1, 0],
        ])
        thin = PIL.fromstring('RGB', (w+4, h+4), img.toString()).convert('1').tostring()
        thin_file.write(thin)
        img = img.dilate()
        thick = PIL.fromstring('RGB', (w+4, h+4), img.toString()).convert('1').tostring()
        thick_file.write(thick)


generate('ASC12', 6, 12)
generate('ASC16', 8, 16)
generate('GBK12', 12, 12)
generate('GBK16', 16, 16)
