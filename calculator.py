from math import ceil, floor


def rounder(num, up=True):
    digits = 2
    mul = 10**digits
    if up:
        return ceil(num * mul)/mul
    else:
        return floor(num*mul)/mul