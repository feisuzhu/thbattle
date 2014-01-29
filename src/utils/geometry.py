# -*- coding: utf-8 -*-


def rect_to_dict(rect):
    x, y, w, h = rect
    return dict(
        x=x, y=y,
        width=w, height=h,
    )


def rectv2f(x, y, w, h, ax=0, ay=0):
    x1, y1 = x + w, y + h
    return [ax+x, ay+y, ax+x1, ay+y, ax+x1, ay+y1, ax+x, ay+y1]


def rrectv2f(x, y, w, h, ax=0, ay=0):
    x1, y1 = x + w, y + h
    return [ax+x, ay+y, ax+x, ay+y1, ax+x1, ay+y1, ax+x1, ay+y]


def inpoly(x, y, vlist):
    rst = False
    n = len(vlist)
    i = 0
    j = n - 1
    while i < n:
        if ((vlist[i][1] > y) != (vlist[j][1] > y)) and \
                (x <
                    (vlist[j][0] - vlist[i][0]) *
                    (y - vlist[i][1]) /
                    (vlist[j][1] - vlist[i][1]) +
                    (vlist[i][0])):
            rst = not rst

        j = i
        i += 1

    return rst
