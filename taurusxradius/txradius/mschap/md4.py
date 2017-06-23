#!/usr/bin/env python
# coding=utf-8
md4_test = [('', 66247539591895304393806215489418987968L),
 ('a', 252414033801067011759054190481608473380L),
 ('abc', 218367266684986933958873955756159693469L),
 ('message digest', 288541341801218712890536998221291913547L),
 ('abcdefghijklmnopqrstuvwxyz', 286604973750735409367980532615713205673L),
 ('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789', 5646734620340757891802959268092047588L),
 ('12345678901234567890123456789012345678901234567890123456789012345678901234567890', 302042679781913196959168694191041283382L)]
from U32 import U32

class MD4:
    A = None
    B = None
    C = None
    D = None
    count, len1, len2 = (None, None, None)
    buf = []

    def __init__(self):
        self.A = U32(1732584193L)
        self.B = U32(4023233417L)
        self.C = U32(2562383102L)
        self.D = U32(271733878L)
        self.count, self.len1, self.len2 = U32(0L), U32(0L), U32(0L)
        self.buf = [0] * 64

    def __repr__(self):
        r = 'A = %s, \nB = %s, \nC = %s, \nD = %s.\n' % (self.A.__repr__(),
         self.B.__repr__(),
         self.C.__repr__(),
         self.D.__repr__())
        r = r + 'count = %s, \nlen1 = %s, \nlen2 = %s.\n' % (self.count.__repr__(), self.len1.__repr__(), self.len2.__repr__())
        for i in range(4):
            for j in range(16):
                r = r + '%4s ' % hex(self.buf[i + j])

            r = r + '\n'

        return r

    def make_copy(self):
        dest = new()
        dest.len1 = self.len1
        dest.len2 = self.len2
        dest.A = self.A
        dest.B = self.B
        dest.C = self.C
        dest.D = self.D
        dest.count = self.count
        for i in range(self.count):
            dest.buf[i] = self.buf[i]

        return dest

    def update(self, str):
        buf = []
        for i in str:
            buf.append(ord(i))

        ilen = U32(len(buf))
        if long(self.len1 + (ilen << 3)) < long(self.len1):
            self.len2 = self.len2 + U32(1)
        self.len1 = self.len1 + (ilen << 3)
        self.len2 = self.len2 + (ilen >> 29)
        L = U32(0)
        bufpos = 0
        while long(ilen) > 0:
            if 64 - long(self.count) < long(ilen):
                L = U32(64 - long(self.count))
            else:
                L = ilen
            for i in range(int(L)):
                self.buf[i + int(self.count)] = buf[i + bufpos]

            self.count = self.count + L
            ilen = ilen - L
            bufpos = bufpos + int(L)
            if long(self.count) == 64L:
                self.count = U32(0L)
                X = []
                i = 0
                for j in range(16):
                    X.append(U32(self.buf[i]) + (U32(self.buf[i + 1]) << 8) + (U32(self.buf[i + 2]) << 16) + (U32(self.buf[i + 3]) << 24))
                    i = i + 4

                A = self.A
                B = self.B
                C = self.C
                D = self.D
                A = f1(A, B, C, D, 0, 3, X)
                D = f1(D, A, B, C, 1, 7, X)
                C = f1(C, D, A, B, 2, 11, X)
                B = f1(B, C, D, A, 3, 19, X)
                A = f1(A, B, C, D, 4, 3, X)
                D = f1(D, A, B, C, 5, 7, X)
                C = f1(C, D, A, B, 6, 11, X)
                B = f1(B, C, D, A, 7, 19, X)
                A = f1(A, B, C, D, 8, 3, X)
                D = f1(D, A, B, C, 9, 7, X)
                C = f1(C, D, A, B, 10, 11, X)
                B = f1(B, C, D, A, 11, 19, X)
                A = f1(A, B, C, D, 12, 3, X)
                D = f1(D, A, B, C, 13, 7, X)
                C = f1(C, D, A, B, 14, 11, X)
                B = f1(B, C, D, A, 15, 19, X)
                A = f2(A, B, C, D, 0, 3, X)
                D = f2(D, A, B, C, 4, 5, X)
                C = f2(C, D, A, B, 8, 9, X)
                B = f2(B, C, D, A, 12, 13, X)
                A = f2(A, B, C, D, 1, 3, X)
                D = f2(D, A, B, C, 5, 5, X)
                C = f2(C, D, A, B, 9, 9, X)
                B = f2(B, C, D, A, 13, 13, X)
                A = f2(A, B, C, D, 2, 3, X)
                D = f2(D, A, B, C, 6, 5, X)
                C = f2(C, D, A, B, 10, 9, X)
                B = f2(B, C, D, A, 14, 13, X)
                A = f2(A, B, C, D, 3, 3, X)
                D = f2(D, A, B, C, 7, 5, X)
                C = f2(C, D, A, B, 11, 9, X)
                B = f2(B, C, D, A, 15, 13, X)
                A = f3(A, B, C, D, 0, 3, X)
                D = f3(D, A, B, C, 8, 9, X)
                C = f3(C, D, A, B, 4, 11, X)
                B = f3(B, C, D, A, 12, 15, X)
                A = f3(A, B, C, D, 2, 3, X)
                D = f3(D, A, B, C, 10, 9, X)
                C = f3(C, D, A, B, 6, 11, X)
                B = f3(B, C, D, A, 14, 15, X)
                A = f3(A, B, C, D, 1, 3, X)
                D = f3(D, A, B, C, 9, 9, X)
                C = f3(C, D, A, B, 5, 11, X)
                B = f3(B, C, D, A, 13, 15, X)
                A = f3(A, B, C, D, 3, 3, X)
                D = f3(D, A, B, C, 11, 9, X)
                C = f3(C, D, A, B, 7, 11, X)
                B = f3(B, C, D, A, 15, 15, X)
                self.A = self.A + A
                self.B = self.B + B
                self.C = self.C + C
                self.D = self.D + D

    def digest(self):
        res = [0] * 16
        s = [0] * 8
        padding = [0] * 64
        padding[0] = 128
        padlen, oldlen1, oldlen2 = U32(0), U32(0), U32(0)
        temp = self.make_copy()
        oldlen1 = temp.len1
        oldlen2 = temp.len2
        if 56 <= long(self.count):
            padlen = U32(56 - long(self.count) + 64)
        else:
            padlen = U32(56 - long(self.count))
        temp.update(int_array2str(padding[:int(padlen)]))
        s[0] = oldlen1 & U32(255)
        s[1] = oldlen1 >> 8 & U32(255)
        s[2] = oldlen1 >> 16 & U32(255)
        s[3] = oldlen1 >> 24 & U32(255)
        s[4] = oldlen2 & U32(255)
        s[5] = oldlen2 >> 8 & U32(255)
        s[6] = oldlen2 >> 16 & U32(255)
        s[7] = oldlen2 >> 24 & U32(255)
        temp.update(int_array2str(s))
        res[0] = temp.A & U32(255)
        res[1] = temp.A >> 8 & U32(255)
        res[2] = temp.A >> 16 & U32(255)
        res[3] = temp.A >> 24 & U32(255)
        res[4] = temp.B & U32(255)
        res[5] = temp.B >> 8 & U32(255)
        res[6] = temp.B >> 16 & U32(255)
        res[7] = temp.B >> 24 & U32(255)
        res[8] = temp.C & U32(255)
        res[9] = temp.C >> 8 & U32(255)
        res[10] = temp.C >> 16 & U32(255)
        res[11] = temp.C >> 24 & U32(255)
        res[12] = temp.D & U32(255)
        res[13] = temp.D >> 8 & U32(255)
        res[14] = temp.D >> 16 & U32(255)
        res[15] = temp.D >> 24 & U32(255)
        return int_array2str(res)


def F(x, y, z):
    return x & y | ~x & z


def G(x, y, z):
    return x & y | x & z | y & z


def H(x, y, z):
    return x ^ y ^ z


def ROL(x, n):
    return x << n | x >> 32 - n


def f1(a, b, c, d, k, s, X):
    return ROL(a + F(b, c, d) + X[k], s)


def f2(a, b, c, d, k, s, X):
    return ROL(a + G(b, c, d) + X[k] + U32(1518500249L), s)


def f3(a, b, c, d, k, s, X):
    return ROL(a + H(b, c, d) + X[k] + U32(1859775393L), s)


def int_array2str(array):
    str = ''
    for i in array:
        str = str + chr(i)

    return str


new = MD4