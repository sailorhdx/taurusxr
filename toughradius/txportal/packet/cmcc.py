#!/usr/bin/env python
# coding=utf-8
import struct
import random
import hashlib
from toughradius.txportal.packet import pktutils
import binascii
import six
import copy
import itertools
md5_constructor = hashlib.md5
random_generator = random.SystemRandom()
__CurrentSN = random_generator.randrange(1, 32767)
REQ_CHALLENGE = 1
ACK_CHALLENGE = 2
REQ_AUTH = 3
ACK_AUTH = 4
REQ_LOGOUT = 5
ACK_LOGOUT = 6
AFF_ACK_AUTH = 7
NTF_LOGOUT = 8
REQ_INFO = 9
ACK_INFO = 10
NTF_USERDISCOVER = 11
NTF_USERIPCHANGE = 12
AFF_NTF_USERIPCHAN = 13
ACK_NTF_LOGOUT = 14
NTF_HEARTBEAT = 15
NTF_USER_HEARTBEAT = 16
ACK_NTF_USER_HEARTBEAT = 17
NTF_CHALLENGE = 18
NTF_USER_NOTIFY = 19
AFF_NTF_USER_NOTIFY = 20
AUTH_CHAP = 0
AUTH_PAP = 1

def CurrentSN():
    global __CurrentSN
    __CurrentSN = (__CurrentSN + 1) % 32767
    return __CurrentSN


def hexlify(attr_type, value):
    if attr_type in (3, 4, 10):
        return binascii.hexlify(value)
    else:
        return value


AckChallengeErrs = {1: 'Request Challenge was rejected',
 2: 'A link has been established',
 3: 'A user is certification process, please try again later',
 4: 'request Challenge failed'}
AckAuthErrs = {1: 'User authentication request was refused',
 2: 'A link has been established',
 3: 'A user is certification process, please try again later',
 4: 'User authentication failed'}
AckLogoutErrs = {1: 'User logoff rejection',
 2: 'User logoff failure (error)',
 3: 'User is offline'}
AckInfoErrs = {1: 'Does not support or deal with failure information query function',
 2: 'Message processing failure, for some unknown reason'}
PKT_TYPES = {REQ_CHALLENGE: 'REQ_CHALLENGE',
 ACK_CHALLENGE: 'ACK_CHALLENGE',
 REQ_AUTH: 'REQ_AUTH',
 ACK_AUTH: 'ACK_AUTH',
 REQ_LOGOUT: 'REQ_LOGOUT',
 ACK_LOGOUT: 'ACK_LOGOUT',
 AFF_ACK_AUTH: 'AFF_ACK_AUTH',
 NTF_LOGOUT: 'NTF_LOGOUT',
 REQ_INFO: 'REQ_INFO',
 ACK_INFO: 'ACK_INFO',
 NTF_USERDISCOVER: 'NTF_USERDISCOVER',
 NTF_USERIPCHANGE: 'NTF_USERIPCHANGE',
 AFF_NTF_USERIPCHAN: 'AFF_NTF_USERIPCHAN',
 ACK_NTF_LOGOUT: 'ACK_NTF_LOGOUT',
 NTF_HEARTBEAT: 'NTF_HEARTBEAT',
 NTF_USER_HEARTBEAT: 'NTF_USER_HEARTBEAT',
 ACK_NTF_USER_HEARTBEAT: 'ACK_NTF_USER_HEARTBEAT',
 NTF_CHALLENGE: 'NTF_CHALLENGE',
 NTF_USER_NOTIFY: 'NTF_USER_NOTIFY',
 AFF_NTF_USER_NOTIFY: 'AFF_NTF_USER_NOTIFY'}

class Error(Exception):
    pass


class UnpackError(Error):
    pass


class NeedData(UnpackError):
    pass


class PackError(Error):
    pass


class Portal(object):
    __hdr__ = (('ver', 'B', 1),
     ('type', 'B', 0),
     ('isChap', 'B', 0),
     ('rsv', 'B', 0),
     ('serialNo', 'H', 0),
     ('reqId', 'H', 0),
     ('userIp', '4s', 0),
     ('userPort', 'H', 0),
     ('errCode', 'B', 0),
     ('attrNum', 'B', 0))
    attrs = []

    def __init__(self, **attributes):
        self.__hdr_fmt__ = '>' + ''.join([ x[1] for x in self.__hdr__ ])
        self.__hdr_fields__ = [ x[0] for x in self.__hdr__ ]
        self.__hdr_len__ = struct.calcsize(self.__hdr_fmt__)
        self.__hdr_defaults__ = dict(zip(self.__hdr_fields__, [ x[2] for x in self.__hdr__ ]))
        if 'secret' in attributes:
            self.secret = attributes.pop('secret')
        if 'source' in attributes:
            self.source = attributes.pop('source')
        if 'packet' in attributes:
            try:
                print 'data is', attributes
                self.unpack(attributes.pop('packet'))
            except struct.error:
                if len(attributes[0]) < self.__hdr_len__:
                    raise NeedData
                raise UnpackError('invalid %s: %r' % (self.__class__.__name__, attributes[0]))

        else:
            for k in self.__hdr_fields__:
                setattr(self, k, copy.copy(self.__hdr_defaults__[k]))

            for k, v in attributes.iteritems():
                setattr(self, k, v)

        for key, value in attributes.items():
            if key in self.__hdr_fields__:
                setattr(self, key, value)

    @property
    def sid(self):
        return '{0}_{1}'.format(self.reqId, self.userIp)

    def __len__(self):
        return self.__hdr_len__ + sum([ 2 + len(o[1]) for o in self.attrs ])

    def __str__(self):
        return self.pack_hdr() + self.pack_attrs()

    def __repr__(self):
        l = [ '%s=%r' % (k, getattr(self, k)) for k in self.__hdr_defaults__ ]
        l.append('attrs=%s' % self.attrs)
        return '%s <%s> (%s)' % (self.__class__.__name__, PKT_TYPES.get(self.type), ', '.join(l))

    def pack_hdr(self):
        """Return packed header string."""
        try:
            params = [ getattr(self, k) for k in self.__hdr_fields__ ]
            return struct.pack(self.__hdr_fmt__, *params)
        except Exception as e:
            raise PackError(e)

    def pack_attrs(self):
        if not self.attrs:
            return ''
        l = []
        for t, data in self.attrs:
            l.append('%s%s%s' % (chr(t), chr(len(data) + 2), data))

        return ''.join(l)

    def pack(self):
        """Return packed header + self.data string."""
        return str(self)

    def unpack(self, buf):
        for k, v in itertools.izip(self.__hdr_fields__, struct.unpack(self.__hdr_fmt__, buf[:self.__hdr_len__])):
            setattr(self, k, v)

        buf = buf[self.__hdr_len__:]
        self.attrs = []
        _count = 0
        while buf:
            if _count == self.attrNum:
                return
            t = ord(buf[0])
            l = ord(buf[1])
            d, buf = buf[2:l], buf[l:]
            self.attrs.append((t, d))
            _count += 1

    def get_user_name(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: <=16(\xe5\x8f\xaf\xe5\x8f\x98)
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe8\xaf\xa5\xe5\xb1\x9e\xe6\x80\xa7\xe8\xa1\xa8\xe7\xa4\xba\xe8\xa6\x81\xe8\xae\xa4\xe8\xaf\x81\xe7\x9a\x84\xe7\x94\xa8\xe6\x88\xb7\xe7\x9a\x84\xe5\x90\x8d\xe5\xad\x97\xef\xbc\x8c\xe5\xbf\x85\xe9\xa1\xbb\xe5\x87\xba\xe7\x8e\xb0\xe5\x9c\xa8REQ_AUTH\xef\xbc\x8803\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe3\x80\x82
        \xe8\xaf\xa5\xe5\xb1\x9e\xe6\x80\xa7\xe8\xa1\xa8\xe6\x98\x8e\xe4\xba\x86\xe5\xbe\x85\xe9\xaa\x8c\xe8\xaf\x81\xe7\x9a\x84\xe7\x94\xa8\xe6\x88\xb7\xe7\x9a\x84\xe5\xaf\x86\xe7\xa0\x81\xef\xbc\x8c\xe5\x9c\xa8\xe4\xbc\xa0\xe8\xbe\x93\xe8\xbf\x87\xe7\xa8\x8b\xe4\xb8\xad\xe6\x98\xaf\xe5\x8a\xa0\xe5\xaf\x86\xe7\x9a\x84\xe3\x80\x82\xe5\xbd\x93\xe7\x94\xa8\xe6\x88\xb7\xe9\x87\x87\xe7\x94\xa8PAP\xe6\x96\xb9\xe5\xbc\x8f\xe8\xae\xa4\xe8\xaf\x81\xe6\x97\xb6\xef\xbc\x8c\xe5\xbf\x85\xe9\xa1\xbb\xe5\x87\xba\xe7\x8e\xb0\xe5\x9c\xa8REQ_AUTH\xef\xbc\x8803\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe3\x80\x82
        """
        for attr in self.attrs:
            if attr[0] == 1:
                return pktutils.DecodeString(attr[1])

    def get_password(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: 16(\xe5\x9b\xba\xe5\xae\x9a)
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe8\xaf\xa5\xe5\xb1\x9e\xe6\x80\xa7\xe8\xa1\xa8\xe6\x98\x8e\xe4\xba\x86\xe5\xbe\x85\xe9\xaa\x8c\xe8\xaf\x81\xe7\x9a\x84\xe7\x94\xa8\xe6\x88\xb7\xe7\x9a\x84\xe5\xaf\x86\xe7\xa0\x81\xef\xbc\x8c\xe5\x9c\xa8\xe4\xbc\xa0\xe8\xbe\x93\xe8\xbf\x87\xe7\xa8\x8b\xe4\xb8\xad\xe6\x98\xaf\xe5\x8a\xa0\xe5\xaf\x86\xe7\x9a\x84\xe3\x80\x82\xe5\xbd\x93\xe7\x94\xa8\xe6\x88\xb7\xe9\x87\x87\xe7\x94\xa8PAP\xe6\x96\xb9\xe5\xbc\x8f\xe8\xae\xa4\xe8\xaf\x81\xe6\x97\xb6\xef\xbc\x8c\xe5\xbf\x85\xe9\xa1\xbb\xe5\x87\xba\xe7\x8e\xb0\xe5\x9c\xa8REQ_AUTH\xef\xbc\x8803\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe3\x80\x82
        \xe6\xad\xa4\xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe7\x9a\x84\xe9\x95\xbf\xe5\xba\xa6\xe8\xa6\x81\xe6\xb1\x82\xe5\xb0\x91\xe4\xba\x8e32\xe5\xad\x97\xe8\x8a\x82\xe3\x80\x82
        """
        for attr in self.attrs:
            if attr[0] == 2:
                return pktutils.DecodeString(attr[1])

    def get_challenge(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: 16(\xe5\x9b\xba\xe5\xae\x9a)
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe8\xa1\xa8\xe7\xa4\xba\xe8\xae\xbe\xe5\xa4\x87\xe4\xbc\xa0\xe9\x80\x81\xe7\xbb\x99CHAP\xe8\xae\xa4\xe8\xaf\x81\xe7\x9a\x84\xe7\x94\xa8\xe6\x88\xb7\xe7\x9a\x84chap challenge\xe3\x80\x82
        \xe5\xae\x83\xe5\x8f\xaa\xe8\x83\xbd\xe7\x94\xa8\xe5\x9c\xa8chap\xe6\x96\xb9\xe5\xbc\x8f\xe8\xae\xa4\xe8\xaf\x81\xe7\x9a\x84REQ_AUTH(03)\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xef\xbc\x8c\xe5\xbd\x93\xe6\x98\xafCHAP\xe8\xae\xa4\xe8\xaf\x81\xe6\x96\xb9\xe5\xbc\x8f\xe6\x97\xb6\xef\xbc\x8c\xe5\xbf\x85\xe9\xa1\xbb\xe5\x87\xba\xe7\x8e\xb0\xe5\x9c\xa8REQ_AUTH\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe3\x80\x82
        """
        for t, v in self.attrs:
            if t == 3:
                return pktutils.DecodeOctets(v)

    def get_chap_pwd(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: 16(\xe5\x9b\xba\xe5\xae\x9a)
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe8\xaf\xa5\xe5\xb1\x9e\xe6\x80\xa7\xe8\xa1\xa8\xe7\xa4\xba\xe7\x94\xb1ppp chap\xe7\x94\xa8\xe6\x88\xb7\xe9\x80\x9a\xe8\xbf\x87MD5\xe7\xae\x97\xe6\xb3\x95\xe5\x8a\xa0\xe5\xaf\x86\xe5\x90\x8e\xe7\x9a\x84\xe5\xaf\x86\xe7\xa0\x81\xe3\x80\x82
        \xe5\xbd\x93\xe5\x87\xba\xe7\x8e\xb0\xe6\xad\xa4\xe5\xb1\x9e\xe6\x80\xa7\xe6\x97\xb6\xef\xbc\x8c\xe5\x85\xb6chap challenge\xe5\x9c\xa8Challenge\xef\xbc\x8803\xef\xbc\x89\xe5\xb1\x9e\xe6\x80\xa7\xe4\xb8\xad\xe3\x80\x82\xe5\xbd\x93\xe9\x87\x87\xe7\x94\xa8chap\xe6\x96\xb9\xe5\xbc\x8f\xe8\xae\xa4\xe8\xaf\x81\xe6\x97\xb6\xef\xbc\x8c\xe5\xbf\x85\xe9\xa1\xbb\xe5\x87\xba\xe7\x8e\xb0\xe5\x9c\xa8REQ_AUTH\xef\xbc\x8803\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe3\x80\x82
        """
        for attr in self.attrs:
            if attr[0] == 4:
                return pktutils.DecodeOctets(attr[1])

    def get_text_info(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: \xe5\xa4\xa7\xe4\xba\x8e\xe7\xad\x89\xe4\xba\x8e3,\xe5\xb0\x8f\xe4\xba\x8e\xe7\xad\x89\xe4\xba\x8e255
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe8\xaf\xa5\xe5\xb1\x9e\xe6\x80\xa7\xe7\x94\xa8\xe4\xba\x8eBAS\xe5\xb0\x86RADIUS\xe7\xad\x89\xe7\xac\xac\xe4\xb8\x89\xe6\x96\xb9\xe8\xae\xa4\xe8\xaf\x81\xe8\xae\xbe\xe5\xa4\x87\xe7\x9a\x84\xe6\x8f\x90\xe7\xa4\xba\xe4\xbf\xa1\xe6\x81\xaf\xe9\x80\x8f\xe4\xbc\xa0\xe5\x88\xb0Portal Server\xe3\x80\x82
        \xe5\xbd\x93\xe8\xae\xa4\xe8\xaf\x81\xe5\xa4\xb1\xe8\xb4\xa5\xe6\x97\xb6\xef\xbc\x8c\xe8\xa1\xa8\xe7\xa4\xba\xe8\xae\xa4\xe8\xaf\x81\xe5\xa4\xb1\xe8\xb4\xa5\xe5\x8e\x9f\xe5\x9b\xa0\xe3\x80\x82
        \xe5\xbf\x85\xe9\xa1\xbb\xe5\x87\xba\xe7\x8e\xb0\xe5\x9c\xa8NTF_LOGOUT\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xef\xbc\x8c\xe8\xa1\xa8\xe7\xa4\xbaBAS\xe5\xbc\xba\xe5\x88\xb6\xe7\x94\xa8\xe6\x88\xb7\xe4\xb8\x8b\xe7\xba\xbf\xe7\x9a\x84\xe5\x8e\x9f\xe5\x9b\xa0\xef\xbc\x8c\xe5\xbd\x93\xe8\xae\xa4\xe8\xaf\x81\xe6\x8b\x92\xe7\xbb\x9d\xe6\x88\x96\xe8\x80\x85\xe8\xae\xa4\xe8\xaf\x81\xe8\xb6\x85\xe6\x97\xb6\xe7\x9a\x84\xe6\x97\xb6\xe5\x80\x99\xef\xbc\x8c\xe5\xbf\x85\xe9\xa1\xbb\xe5\x87\xba\xe7\x8e\xb0\xe5\x9c\xa8ACK_AUTH\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe3\x80\x82
        \xe9\x95\xbf\xe5\xba\xa6\xe8\x87\xb3\xe5\xb0\x91\xe4\xb8\xba3\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe4\xbd\x86\xe4\xb8\x8d\xe8\xb6\x85\xe8\xbf\x87253\xe5\xad\x97\xe8\x8a\x82\xe3\x80\x82\xe5\x86\x85\xe5\xae\xb9\xe5\x8f\xaf\xe4\xbb\xa5\xe4\xb8\xba\xe4\xbb\xbb\xe6\x84\x8f\xe5\xad\x97\xe7\xac\xa6\xe4\xb8\xb2\xef\xbc\x8c\xe4\xbd\x86\xe6\x98\xaf\xe4\xb8\x8d\xe5\x8c\x85\xe6\x8b\xac\xe5\xad\x97\xe7\xac\xa6\xe4\xb8\xb2\xe7\xbb\x93\xe6\x9d\x9f\xe7\xac\xa6\xe2\x80\x98\x00\xe2\x80\x99\xe3\x80\x82
        \xe8\xaf\xa5\xe5\xb1\x9e\xe6\x80\xa7\xe5\x8f\xaf\xe4\xbb\xa5\xe5\xad\x98\xe5\x9c\xa8\xe4\xba\x8e\xe4\xbb\x8eBAS\xe5\x88\xb0Portal Server\xe7\x9a\x84\xe4\xbb\xbb\xe4\xbd\x95\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xef\xbc\x8c\xe5\x90\x8c\xe4\xb8\x80\xe4\xb8\xaa\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe5\x85\x81\xe8\xae\xb8\xe6\x9c\x89\xe5\xa4\x9a\xe4\xb8\xaa\xe8\xaf\xa5\xe5\xb1\x9e\xe6\x80\xa7\xef\xbc\x8c\xe5\xbb\xba\xe8\xae\xae\xe5\x8f\xaa\xe6\x90\xba\xe5\xb8\xa61\xe4\xb8\xaa\xe3\x80\x82
        """
        texts = []
        for attr in self.attrs:
            if attr[0] == 5:
                texts.append(pktutils.DecodeString(attr[1]))

        return texts

    def get_up_link_flux(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: 2/10
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe6\x9c\xac\xe5\xb1\x9e\xe6\x80\xa7\xe5\x8f\xaa\xe8\x83\xbd\xe7\x94\xa8\xe5\x9c\xa8REQ_INFO\xef\xbc\x88Type\xef\xbc\x9d9\xef\xbc\x89\xe5\x92\x8cACK_INFO\xef\xbc\x88Type\xef\xbc\x9d0x0a\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xef\xbc\x8c\xe6\x95\xb0\xe9\x87\x8f\xe4\xb8\x8d\xe8\x83\xbd\xe8\xb6\x85\xe8\xbf\x871\xe3\x80\x82
        \xe5\xbd\x93\xe6\x98\xafREQ_INFO\xe6\x8a\xa5\xe6\x96\x87\xe6\x97\xb6\xef\xbc\x8c\xe9\x95\xbf\xe5\xba\xa6\xe4\xb8\xba2\xe5\xad\x97\xe8\x8a\x82\xe3\x80\x82
        \xe5\xbd\x93\xe6\x98\xafACK_INFO\xe6\x8a\xa5\xe6\x96\x87\xe6\x97\xb6\xef\xbc\x8c\xe9\x95\xbf\xe5\xba\xa6\xe4\xb8\xba10\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe8\xa1\xa8\xe7\xa4\xba\xe8\xaf\xa5\xe7\x94\xa8\xe6\x88\xb7\xe7\x9a\x84\xe4\xb8\x8a\xe8\xa1\x8c\xef\xbc\x88\xe8\xbe\x93\xe5\x87\xba\xef\xbc\x89\xe7\x9a\x84\xe6\xb5\x81\xe9\x87\x8f\xef\xbc\x8c
        \xe7\x94\xa8\xe4\xb8\x80\xe4\xb8\xaa8\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8864Bits\xef\xbc\x89\xe6\x97\xa0\xe7\xac\xa6\xe5\x8f\xb7\xe6\x95\xb4\xe6\x95\xb0\xef\xbc\x88\xe7\xbd\x91\xe7\xbb\x9c\xe9\xa1\xba\xe5\xba\x8f\xef\xbc\x89\xe8\xa1\xa8\xe7\xa4\xba\xef\xbc\x8c\xe5\x8d\x95\xe4\xbd\x8d\xe4\xb8\xbakbytes\xe3\x80\x82
        """
        pass

    def get_down_link_flux(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: 2/10
        \xe6\x9c\xac\xe5\xb1\x9e\xe6\x80\xa7\xe5\x8f\xaa\xe8\x83\xbd\xe7\x94\xa8\xe5\x9c\xa8REQ_INFO\xef\xbc\x88Type\xef\xbc\x9d9\xef\xbc\x89\xe5\x92\x8cACK_INFO\xef\xbc\x88Type\xef\xbc\x9d0x0a\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xef\xbc\x8c\xe6\x95\xb0\xe9\x87\x8f\xe4\xb8\x8d\xe8\x83\xbd\xe8\xb6\x85\xe8\xbf\x871\xe3\x80\x82
        \xe5\xbd\x93\xe6\x98\xafREQ_INFO\xe6\x8a\xa5\xe6\x96\x87\xe6\x97\xb6\xef\xbc\x8c\xe9\x95\xbf\xe5\xba\xa6\xe4\xb8\xba2\xe5\xad\x97\xe8\x8a\x82\xe3\x80\x82
        \xe5\xbd\x93\xe6\x98\xafACK_INFO\xe6\x8a\xa5\xe6\x96\x87\xe6\x97\xb6\xef\xbc\x8c\xe9\x95\xbf\xe5\xba\xa6\xe4\xb8\xba10\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe8\xa1\xa8\xe7\xa4\xba\xe8\xaf\xa5\xe7\x94\xa8\xe6\x88\xb7\xe7\x9a\x84\xe4\xb8\x8b\xe8\xa1\x8c\xef\xbc\x88\xe8\xbe\x93\xe5\x85\xa5\xef\xbc\x89\xe7\x9a\x84\xe6\xb5\x81\xe9\x87\x8f\xef\xbc\x8c
        \xe7\x94\xa8\xe4\xb8\x80\xe4\xb8\xaa8\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8864Bits\xef\xbc\x89\xe6\x97\xa0\xe7\xac\xa6\xe5\x8f\xb7\xe6\x95\xb4\xe6\x95\xb0\xef\xbc\x88\xe7\xbd\x91\xe7\xbb\x9c\xe9\xa1\xba\xe5\xba\x8f\xef\xbc\x89\xe8\xa1\xa8\xe7\xa4\xba\xef\xbc\x8c\xe5\x8d\x95\xe4\xbd\x8d\xe4\xb8\xbakbytes\xe3\x80\x82
        """
        pass

    def get_port(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: >=2\xef\xbc\x8c<=255
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe6\x9c\xac\xe5\xb1\x9e\xe6\x80\xa7\xe5\x8f\xaa\xe8\x83\xbd\xe7\x94\xa8\xe5\x9c\xa8REQ_INFO\xef\xbc\x88Type\xef\xbc\x9d9\xef\xbc\x89\xe5\x92\x8cACK_INFO\xef\xbc\x88Type\xef\xbc\x9d0x0a\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xef\xbc\x8c\xe6\x95\xb0\xe9\x87\x8f\xe4\xb8\x8d\xe8\x83\xbd\xe8\xb6\x85\xe8\xbf\x871\xe3\x80\x82
        \xe5\xbd\x93\xe6\x98\xafREQ_INFO\xe6\x8a\xa5\xe6\x96\x87\xe6\x97\xb6\xef\xbc\x8c\xe9\x95\xbf\xe5\xba\xa6\xe4\xb8\xba2\xe5\xad\x97\xe8\x8a\x82\xe3\x80\x82
        \xe5\xbd\x93\xe6\x98\xafACK_INFO\xe6\x8a\xa5\xe6\x96\x87\xe6\x97\xb6\xef\xbc\x8c\xe5\x8f\x98\xe9\x95\xbf\xef\xbc\x8c\xe4\xbd\x86\xe4\xb8\x8d\xe8\x83\xbd\xe8\xb6\x85\xe8\xbf\x87253\xe5\xad\x97\xe8\x8a\x82\xe3\x80\x82\xe5\x86\x85\xe5\xae\xb9\xe4\xb8\xba\xe4\xb8\x80\xe4\xb8\xaa\xe5\xad\x97\xe7\xac\xa6\xe4\xb8\xb2\xef\xbc\x88\xe6\x97\xa0'\x00'\xe7\xbb\x93\xe6\x9d\x9f\xe7\xac\xa6\xef\xbc\x89\xe3\x80\x82
        \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe8\x87\xb3\xe5\xb0\x912\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe4\xbd\x86\xe4\xb8\x8d\xe8\xb6\x85\xe8\xbf\x8734\xe5\xad\x97\xe8\x8a\x82\xe3\x80\x82\xe5\xbf\x85\xe9\xa1\xbb\xe5\x87\xba\xe7\x8e\xb0\xe5\x9c\xa8REQ_INFO\xe5\x92\x8cACK_INFO\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe3\x80\x82
        \xe5\x85\xb6\xe6\xa0\xbc\xe5\xbc\x8f\xe4\xb8\xba\xe4\xb8\xbb\xe6\x9c\xba\xe5\x90\x8d-vlan-\xe6\xa7\xbd\xe4\xbd\x8d\xef\xbc\x882 Bytes-vlan \xe6\xa0\x87\xe8\xaf\x86\xef\xbc\x884 Bytes\xef\xbc\x89@vlan-SSID-SSID\xe6\xa0\x87\xe8\xaf\x86(\xe6\x9c\x80\xe9\x95\xbf32\xe5\xad\x97\xe8\x8a\x82)@SSID\xe3\x80\x82
        """
        for attr in self.attrs:
            if attr[0] == 8:
                return pktutils.DecodeString(attr[1])

    def get_ip_config(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6\xef\xbc\x9a4(\xe5\x9b\xba\xe5\xae\x9a)
        \xe6\x8f\x8f\xe8\xbf\xb0\xef\xbc\x9a\xe7\x94\xa8\xe4\xba\x8e\xe4\xba\x8c\xe6\xac\xa1\xe5\x9c\xb0\xe5\x9d\x80\xe6\x96\xb9\xe5\xbc\x8f\xe4\xb8\xad\xef\xbc\x8c\xe8\xa1\xa8\xe7\xa4\xba\xe7\x94\xa8\xe6\x88\xb7IP\xe7\x9a\x84\xe5\x88\x87\xe6\x8d\xa2\xe3\x80\x82
             \xe5\xbd\x93\xe6\x98\xaf\xe4\xba\x8c\xe6\xac\xa1\xe5\x9c\xb0\xe5\x9d\x80\xe6\x96\xb9\xe5\xbc\x8f\xe6\x97\xb6\xef\xbc\x8c\xe5\xbf\x85\xe9\xa1\xbb\xe5\x87\xba\xe7\x8e\xb0\xe5\x9c\xa8ACK_AUTH\xef\xbc\x880x03\xef\xbc\x89\xe3\x80\x81
             ACK_LOGOUT\xef\xbc\x880x06\xef\xbc\x89\xe3\x80\x81NTF_LOGOUT\xef\xbc\x880x08\xef\xbc\x89\xe5\x92\x8cNTF_USERIPCHAN\xef\xbc\x880x0c\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe3\x80\x82
             \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc4\xe5\xad\x97\xe8\x8a\x82\xe9\x95\xbf\xef\xbc\x8c\xe5\x9c\xa8\xe4\xb8\x8d\xe5\x90\x8c\xe6\x8a\xa5\xe6\x96\x87\xe7\xb1\xbb\xe5\x9e\x8b\xe4\xb8\xad\xe5\x90\xab\xe4\xb9\x89\xe4\xb8\x8d\xe5\x90\x8c
             
        1,\xe5\x9c\xa8ACK _AUTH\xef\xbc\x88Type\xef\xbc\x9d4\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xef\xbc\x8c\xe8\xa1\xa8\xe7\xa4\xbaBAS\xe8\xae\xbe\xe5\xa4\x87\xe7\xab\xaf\xe9\x80\x9a\xe7\x9f\xa5Portal Server\xe6\xad\xa4\xe7\x94\xa8\xe6\x88\xb7\xe9\x9c\x80\xe8\xa6\x81\xe4\xba\x8c\xe6\xac\xa1\xe5\x9c\xb0\xe5\x9d\x80\xe5\x88\x86\xe9\x85\x8d\xe3\x80\x82
          \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe7\xbd\xae\xe4\xb8\xba\xe5\x85\xa81\xef\xbc\x880xFFFFFFFF\xef\xbc\x89\xef\xbc\x8c\xe8\xa1\xa8\xe7\xa4\xba\xe7\x94\xa8\xe6\x88\xb7\xe5\xae\xa2\xe6\x88\xb7\xe7\xab\xaf\xe5\xbf\x85\xe9\xa1\xbb\xe5\x90\x8e\xe7\xbb\xa7\xe8\xa7\xa6\xe5\x8f\x91DHCP\xe7\x9b\xb8\xe5\xba\x94\xe7\x9a\x84\xe6\xb5\x81\xe7\xa8\x8b\xef\xbc\x8c
          Portal Server\xe9\xa1\xbb\xe5\xb0\x86\xe6\xad\xa4\xe6\xb6\x88\xe6\x81\xaf\xe9\x80\x9a\xe7\x9f\xa5\xe7\x94\xa8\xe6\x88\xb7\xe5\xae\xa2\xe6\x88\xb7\xe7\xab\xaf\xef\xbc\x8c\xe8\xa7\xa6\xe5\x8f\x91DHCP\xe8\xbf\x87\xe7\xa8\x8b\xe9\x87\x8a\xe6\x94\xbe\xe7\xa7\x81\xe7\xbd\x91IP\xef\xbc\x8c\xe7\x94\xb3\xe8\xaf\xb7\xe5\x85\xac\xe7\xbd\x91IP\xe3\x80\x82
        2,\xe5\x9c\xa8ACK_LOGOUT\xef\xbc\x88Type\xef\xbc\x9d6\xef\xbc\x89\xe5\x92\x8cNTF_LOGOUT\xef\xbc\x88Type\xef\xbc\x9d8\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xef\xbc\x8c
          \xe8\xa1\xa8\xe7\xa4\xba\xe7\x94\xa8\xe6\x88\xb7\xe6\xad\xa4\xe6\x97\xb6\xe4\xbd\xbf\xe7\x94\xa8\xe7\x9a\x84IP\xe5\x9c\xb0\xe5\x9d\x80\xe5\xbf\x85\xe9\xa1\xbb\xe5\x9b\x9e\xe6\x94\xb6\xef\xbc\x8cPortal Server\xe5\xbf\x85\xe9\xa1\xbb\xe9\x80\x9a\xe7\x9f\xa5\xe7\x94\xa8\xe6\x88\xb7\xe8\xa7\xa6\xe5\x8f\x91DHCP\xe8\xbf\x87\xe7\xa8\x8b\xe9\x87\x8a\xe6\x94\xbe\xe5\x85\xac\xe7\xbd\x91IP\xef\xbc\x8c
          \xe8\xae\xbe\xe5\xa4\x87\xe5\xb0\x86\xe9\x87\x8d\xe6\x96\xb0\xe4\xb8\xba\xe7\x94\xa8\xe6\x88\xb7\xe5\x88\x86\xe9\x85\x8d\xe4\xb8\x80\xe4\xb8\xaa\xe7\xa7\x81\xe7\xbd\x91\xe7\x9a\x84IP\xe5\x9c\xb0\xe5\x9d\x80\xef\xbc\x8c\xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe6\xb2\xa1\xe6\x9c\x89\xe6\x84\x8f\xe4\xb9\x89\xef\xbc\x8c\xe7\xbd\xae\xe4\xb8\xba\xe5\x85\xa81\xe3\x80\x82
        3,\xe5\x9c\xa8NTF_USERIPCHANGE\xef\xbc\x88Type\xef\xbc\x9d0x0c\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xef\xbc\x8c
          \xe8\xa1\xa8\xe7\xa4\xbaBAS\xe9\x80\x9a\xe7\x9f\xa5Portal Server\xe7\x94\xa8\xe6\x88\xb7\xe7\x9a\x84IP\xe5\x9c\xb0\xe5\x9d\x80\xe6\x9b\xb4\xe6\x94\xb9\xe3\x80\x82\xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe4\xb8\xba\xe7\x94\xa8\xe6\x88\xb7\xe8\xae\xa4\xe8\xaf\x81\xe5\x89\x8d\xe7\x9a\x84\xe7\xa7\x81\xe7\xbd\x91IP\xe5\x9c\xb0\xe5\x9d\x80\xe3\x80\x82
        
        """
        for attr in self.attrs:
            if attr[0] == 9:
                return pktutils.DecodeInteger(attr[1])

    def get_bas_ip(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: 4(\xe5\x9b\xba\xe5\xae\x9a)
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc4\xe5\xad\x97\xe8\x8a\x82\xe3\x80\x82\xe5\x8f\xaa\xe6\x9c\x89\xe5\x9c\xa8REQ_INFO\xe3\x80\x81REQ_CHALLENGE\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe4\xb8\x8d\xe5\x90\xab\xe6\xad\xa4\xe5\xb1\x9e\xe6\x80\xa7\xef\xbc\x8c\xe5\x85\xb6\xe4\xbb\x96\xe6\x8a\xa5\xe6\x96\x87\xe5\xbf\x85\xe9\xa1\xbb\xe5\x8c\x85\xe5\x90\xab\xe6\xad\xa4\xe5\xb1\x9e\xe6\x80\xa7\xe3\x80\x82
        \xe5\xbd\x93\xe5\xa4\x84\xe4\xba\x8eIPv6\xe7\x8e\xaf\xe5\xa2\x83\xe6\x97\xb6\xef\xbc\x8c\xe5\x85\xb6\xe5\x80\xbc\xe4\xb8\xba0\xef\xbc\x8c\xe6\x8e\xa5\xe5\x85\xa5\xe7\x94\xa8\xe6\x88\xb7\xe7\x9a\x84IPv6\xe5\x9c\xb0\xe5\x9d\x80\xe5\xb0\x86\xe9\x80\x9a\xe8\xbf\x87\xe5\xb1\x9e\xe6\x80\xa7\xe2\x80\x9cBAS-IPv6\xe2\x80\x9d\xe4\xba\x88\xe4\xbb\xa5\xe6\x8f\x90\xe4\xbe\x9b\xe3\x80\x82
        """
        for attr in self.attrs:
            if attr[0] == 10:
                return pktutils.DecodeAddress(attr[1])

    def get_session_id(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: 6(\xe5\x9b\xba\xe5\xae\x9a)
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe6\xad\xa4\xe5\xb1\x9e\xe6\x80\xa7\xe7\x94\xa8\xe6\x9d\xa5\xe6\xa0\x87\xe8\xaf\x86\xe7\x94\xa8\xe6\x88\xb7\xef\xbc\x8c\xe5\xbb\xba\xe8\xae\xae\xe5\x8f\x96\xe7\x94\xa8\xe6\x88\xb7\xe7\x9a\x84mac\xe5\x9c\xb0\xe5\x9d\x80\xe3\x80\x82
        \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc6\xe5\xad\x97\xe8\x8a\x82\xe3\x80\x82\xe5\xbd\x93BAS\xe5\x85\xb3\xe5\xbf\x83\xe7\x94\xa8\xe6\x88\xb7\xe7\x9a\x84mac\xe5\x9c\xb0\xe5\x9d\x80\xe6\x97\xb6\xef\xbc\x8c
        \xe5\xbf\x85\xe9\xa1\xbb\xe5\x87\xba\xe7\x8e\xb0\xe5\x9c\xa8ACK_AUTH\xef\xbc\x8cACK_LOGOUT\xef\xbc\x8cNTF_LOGOUT\xe5\x92\x8cNTF_USERIPCHAN\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xef\xbc\x8c\xe5\x90\xa6\xe5\x88\x99\xe5\x8f\xaf\xe4\xbb\xa5\xe4\xb8\x8d\xe5\x87\xba\xe7\x8e\xb0\xe3\x80\x82
        """
        for attr in self.attrs:
            if attr[0] == 11:
                return pktutils.DecodeOctets(attr[1])

    def get_delay_time(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: 6(\xe5\x9b\xba\xe5\xae\x9a)
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe7\x94\xa8\xe6\x88\xb7\xe8\xae\xb0\xe5\xbd\x95\xe6\x8a\xa5\xe6\x96\x87\xe7\x9a\x84\xe5\x8f\x91\xe9\x80\x81\xe5\xbb\xb6\xe6\x97\xb6
        \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc6\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe7\x94\xa8\xe4\xba\x8eREQ_LOGOUT\xef\xbc\x88Type\xef\xbc\x9d5\xef\xbc\x89\xe5\x92\x8cNTF_LOGOUT\xef\xbc\x88Type\xef\xbc\x9d8\xef\xbc\x89\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xef\xbc\x8c\xe8\xa1\xa8\xe7\xa4\xba\xe6\x8a\xa5\xe6\x96\x87\xe5\x8f\x91\xe9\x80\x81\xe6\x97\xb6\xe9\x97\xb4\xe4\xb8\x8e\xe5\xae\x9e\xe9\x99\x85\xe5\x8f\x91\xe7\x94\x9f\xe6\x97\xb6\xe9\x97\xb4\xe7\x9a\x84\xe9\x97\xb4\xe9\x9a\x94\xe3\x80\x82\xe7\x9b\xae\xe5\x89\x8d\xe6\xb2\xa1\xe6\x9c\x89\xe5\xae\x9e\xe7\x8e\xb0\xe3\x80\x82
        """
        for attr in self.attrs:
            if attr[0] == 12:
                return pktutils.DecodeOctets(attr[1])

    def get_user_list(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: >=6,<=254
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe6\x9c\x80\xe7\x9f\xad4\xe4\xb8\xaa\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe6\x9c\x80\xe9\x95\xbf252\xe4\xb8\xaa\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c
        \xe7\x94\xa8\xe4\xba\x8e\xe7\x94\xa8\xe6\x88\xb7\xe5\xbf\x83\xe8\xb7\xb3\xe6\x8a\xa5\xe6\x96\x87\xef\xbc\x88NTF_USER_HEARTBEAT\xef\xbc\x88Type=0x010\xef\xbc\x89\xef\xbc\x89\xe5\x92\x8c\xe7\x94\xa8\xe6\x88\xb7\xe5\xbf\x83\xe8\xb7\xb3\xe5\x9b\x9e\xe5\xba\x94\xe6\x8a\xa5\xe6\x96\x87\xef\xbc\x88ACK_NTF_USER_HEARTBEAT\xef\xbc\x88Type=0x11\xef\xbc\x89\xef\xbc\x89\xe3\x80\x82
        \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe4\xb8\xad\xe5\x8c\x85\xe5\x90\xab\xe4\xba\x86\xe7\x94\xa8\xe6\x88\xb7IP\xe5\x9c\xb0\xe5\x9d\x80\xe5\x88\x97\xe8\xa1\xa8\xef\xbc\x8c\xe6\xaf\x8f\xe4\xb8\xaa\xe7\x94\xa8\xe6\x88\xb7IP\xe5\x9c\xb0\xe5\x9d\x80\xe5\x8d\xa0\xe7\x94\xa84\xe4\xb8\xaa\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe4\xb8\xad\xe9\x97\xb4\xe6\xb2\xa1\xe6\x9c\x89\xe5\x88\x86\xe9\x9a\x94\xe7\xac\xa6\xe3\x80\x82
        """
        for attr in self.attrs:
            if attr[0] == 13:
                return pktutils.DecodeOctets(attr[1])

    def get_eap_message(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: <=254
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe6\xad\xa4\xe5\xb1\x9e\xe6\x80\xa7\xe4\xb8\xbb\xe8\xa6\x81\xe9\x80\x82\xe7\x94\xa8\xe4\xba\x8eEAP_TLS\xe8\xae\xa4\xe8\xaf\x81\xe3\x80\x82\xe5\x85\x81\xe8\xae\xb8\xe5\x87\xba\xe7\x8e\xb0\xe5\xa4\x9a\xe4\xb8\xaa\xef\xbc\x8cEAP\xe8\xae\xa4\xe8\xaf\x81\xe6\x96\xb9\xe5\xbc\x8f\xe6\x97\xb6\xef\xbc\x8c\xe5\xbf\x85\xe9\xa1\xbb\xe5\x87\xba\xe7\x8e\xb0\xe5\x9c\xa8REQ_AUTH\xe5\x8f\x8aNTF_CHALLENGE\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe3\x80\x82
        \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe6\x9c\x80\xe9\x95\xbf255\xe4\xb8\xaa\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe7\x94\xa8\xe4\xba\x8e\xe8\xaf\x81\xe4\xb9\xa6\xe8\xaf\xb7\xe6\xb1\x82\xe6\x8a\xa5\xe6\x96\x87\xef\xbc\x88NTF_CHALLENGE\xef\xbc\x88Type=0x012\xef\xbc\x89\xef\xbc\x89\xe5\x92\x8c\xe8\xae\xa4\xe8\xaf\x81\xe8\xaf\xb7\xe6\xb1\x82\xe6\x8a\xa5\xe6\x96\x87\xef\xbc\x88REQ_AUTH\xef\xbc\x88Type=0x03\xef\xbc\x89\xef\xbc\x89\xe3\x80\x82
        REQ_AUTH\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe8\xaf\xa5\xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe4\xb8\xad\xe9\x9c\x80\xe8\xa6\x81\xe5\x8c\x85\xe5\x90\xab\xe7\x99\xbb\xe5\xbd\x95\xe5\x90\x8d\xef\xbc\x8cNTF_CHALLENGE\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe8\xaf\xa5\xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe4\xb8\xbb\xe8\xa6\x81\xe7\x94\xa8\xe4\xba\x8e\xe4\xbc\xa0\xe8\xbe\x93\xe8\xaf\x81\xe4\xb9\xa6\xe3\x80\x82
        """
        texts = []
        for attr in self.attrs:
            if attr[0] == 14:
                texts.append(pktutils.DecodeString(attr[1]))

        return texts

    def get_user_notify(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: <=254
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe6\xad\xa4\xe5\xb1\x9e\xe6\x80\xa7\xe4\xb8\xbb\xe8\xa6\x81\xe7\x94\xa8\xe4\xba\x8e\xe9\x80\x8f\xe4\xbc\xa0\xe7\x9a\x84Radius\xe8\xae\xa1\xe8\xb4\xb9\xe5\x9b\x9e\xe5\xba\x94\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe7\x9a\x84hw_User_Notify\xe5\x86\x85\xe5\xae\xb9\xe3\x80\x82
        \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe6\x9c\x80\xe9\x95\xbf255\xe4\xb8\xaa\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe7\x94\xa8\xe4\xba\x8e\xe7\x94\xa8\xe6\x88\xb7\xe6\xb6\x88\xe6\x81\xaf\xe9\x80\x9a\xe7\x9f\xa5\xe6\x8a\xa5\xe6\x96\x87\xef\xbc\x88NTF_USER_NOTIFY\xef\xbc\x88Type=0x013\xef\xbc\x89\xef\xbc\x89,
        \xe5\xb0\x86Radius\xe6\x9c\x8d\xe5\x8a\xa1\xe5\x99\xa8\xe7\x9a\x84\xe8\xae\xa1\xe8\xb4\xb9\xe5\xbc\x80\xe5\xa7\x8b\xe5\x9b\x9e\xe5\xba\x94\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe7\x9a\x84hw_User_Notify\xe5\x86\x85\xe5\xae\xb9\xe9\x80\x8f\xe4\xbc\xa0\xe7\xbb\x99\xe5\xae\xa2\xe6\x88\xb7\xe7\xab\xaf\xe3\x80\x82
        \xe5\x8f\xaf\xe4\xbb\xa5\xe5\xae\x9e\xe7\x8e\xb0Portal\xe8\xae\xa4\xe8\xaf\x81\xe9\x80\x9a\xe8\xbf\x87\xe5\x90\x8e\xe6\x8f\x90\xe7\xa4\xba\xe5\xb8\x90\xe5\x8f\xb7\xe4\xbd\x99\xe9\xa2\x9d\xe7\xad\x89\xe9\x87\x8d\xe8\xa6\x81\xe4\xbf\xa1\xe6\x81\xaf\xe3\x80\x82
        """
        for attr in self.attrs:
            if attr[0] == 15:
                return pktutils.DecodeOctets(attr[1])

    def get_bas_ipv6(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: 16
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe7\x94\xa8\xe4\xba\x8e\xe6\xa0\x87\xe8\xaf\x86BAS\xe8\xae\xbe\xe5\xa4\x87\xe7\x9a\x84IPv6\xe5\x9c\xb0\xe5\x9d\x80\xef\xbc\x8c\xe6\x89\x80\xe6\x9c\x89BAS\xe8\xae\xbe\xe5\xa4\x87\xe5\x8f\x91\xe9\x80\x81\xe7\x9a\x84\xe6\x8a\xa5\xe6\x96\x87\xe9\x83\xbd\xe5\xba\x94\xe8\xaf\xa5\xe6\x90\xba\xe5\xb8\xa6\xe8\xaf\xa5\xe5\xb1\x9e\xe6\x80\xa7\xe3\x80\x82
        \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc16\xe5\xad\x97\xe8\x8a\x82\xe3\x80\x82\xe5\x8f\xaa\xe6\x9c\x89\xe5\x9c\xa8REQ_INFO\xe3\x80\x81REQ_CHALLENGE\xe6\x8a\xa5\xe6\x96\x87\xe4\xb8\xad\xe4\xb8\x8d\xe5\x90\xab\xe6\xad\xa4\xe5\xb1\x9e\xe6\x80\xa7\xef\xbc\x8c\xe5\x85\xb6\xe4\xbb\x96\xe6\x8a\xa5\xe6\x96\x87\xe5\xbf\x85\xe9\xa1\xbb\xe5\x8c\x85\xe5\x90\xab\xe6\xad\xa4\xe5\xb1\x9e\xe6\x80\xa7\xe3\x80\x82IPv4\xe7\x8e\xaf\xe5\xa2\x83\xe6\x97\xb6\xef\xbc\x8c\xe5\x85\xb6\xe5\x80\xbc\xe4\xb8\xba0\xe3\x80\x82
        """
        for attr in self.attrs:
            if attr[0] == 100:
                return pktutils.DecodeOctets(attr[1])

    def get_useripv6_list(self):
        """
        \xe9\x95\xbf\xe5\xba\xa6: >=18,<=252
        \xe6\x8f\x8f\xe8\xbf\xb0: \xe7\x94\xa8\xe4\xba\x8e\xe6\xa0\x87\xe8\xaf\x86\xe6\x8e\xa5\xe5\x85\xa5\xe7\x94\xa8\xe6\x88\xb7\xe7\x9a\x84IPv6\xe5\x9c\xb0\xe5\x9d\x80\xef\xbc\x8c\xe5\x85\xb6\xe5\x80\xbc\xe7\x94\xb1Portal Server\xe6\xa0\xb9\xe6\x8d\xae\xe7\x94\xa8\xe6\x88\xb7\xe8\x8e\xb7\xe5\xbe\x97\xe7\x9a\x84IPv6\xe5\x9c\xb0\xe5\x9d\x80\xe5\xa1\xab\xe5\x86\x99\xe3\x80\x82
        \xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe6\x9c\x80\xe7\x9f\xad16\xe4\xb8\xaa\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe6\x9c\x80\xe9\x95\xbf252\xe4\xb8\xaa\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe7\x94\xa8\xe4\xba\x8e\xe7\x94\xa8\xe6\x88\xb7\xe5\xbf\x83\xe8\xb7\xb3\xe6\x8a\xa5\xe6\x96\x87\xef\xbc\x88NTF_USER_HEARTBEAT\xef\xbc\x88Type=0x010\xef\xbc\x89\xef\xbc\x89
        \xe5\x92\x8c\xe7\x94\xa8\xe6\x88\xb7\xe5\xbf\x83\xe8\xb7\xb3\xe5\x9b\x9e\xe5\xba\x94\xe6\x8a\xa5\xe6\x96\x87\xef\xbc\x88ACK_NTF_USER_HEARTBEAT\xef\xbc\x88Type=0x11\xef\xbc\x89\xef\xbc\x89\xe3\x80\x82\xe5\xb1\x9e\xe6\x80\xa7\xe5\x80\xbc\xe4\xb8\xad\xe5\x8c\x85\xe5\x90\xab\xe4\xba\x86\xe7\x94\xa8\xe6\x88\xb7IPv6\xe5\x9c\xb0\xe5\x9d\x80\xe5\x88\x97\xe8\xa1\xa8\xef\xbc\x8c
        \xe6\xaf\x8f\xe4\xb8\xaa\xe7\x94\xa8\xe6\x88\xb7IPv6\xe5\x9c\xb0\xe5\x9d\x80\xe5\x8d\xa0\xe7\x94\xa816\xe4\xb8\xaa\xe5\xad\x97\xe8\x8a\x82\xef\xbc\x8c\xe4\xb8\xad\xe9\x97\xb4\xe6\xb2\xa1\xe6\x9c\x89\xe5\x88\x86\xe9\x9a\x94\xe7\xac\xa6\xe3\x80\x82
        """
        for attr in self.attrs:
            if attr[0] == 101:
                return pktutils.DecodeOctets(attr[1])

    @property
    def err_string(self):
        return ''

    @staticmethod
    def newMessage(typ, userIp, serialNo, reqId, secret, basip = None, chap = False):
        return Portal(type=typ, isChap=0 if chap else 1, userIp=pktutils.EncodeAddress(userIp), serialNo=serialNo, reqId=reqId, secret=six.b(secret))

    @staticmethod
    def newReqChallenge(userIp, secret, basip = None, serialNo = None, chap = True, mac = None):
        """0x01"""
        pkt = Portal.newMessage(REQ_CHALLENGE, userIp, serialNo or CurrentSN(), 0, secret, chap=chap)
        if mac:
            pkt.attrNum = 1
            pkt.attrs = [(255, mac)]
        return pkt

    @staticmethod
    def newReqAuth(userIp, username, password, reqId, challenge, secret, basip = None, serialNo = None, chap = True, mac = None):
        """0x03"""
        pkt = Portal.newMessage(REQ_AUTH, userIp, serialNo or CurrentSN(), reqId, secret, chap=chap)
        username = pktutils.EncodeString(username)
        password = pktutils.EncodeString(password)
        if chap:
            _reqid = struct.pack('>H', reqId)
            chap_pwd = md5_constructor('%s%s%s' % (_reqid[1], password, challenge)).digest()
            pkt.attrNum = 3
            pkt.attrs = [(1, username), (3, challenge), (4, chap_pwd)]
            if mac:
                pkt.attrNum += 1
                pkt.attrs.append((255, mac))
        else:
            pkt.attrNum = 2
            pkt.attrs = [(1, username), (2, password)]
            if mac:
                pkt.attrNum += 1
                pkt.attrs.append((255, mac))
        return pkt

    @staticmethod
    def newReqLogout(userIp, secret, basip = None, serialNo = None, chap = True, mac = None):
        """0x05"""
        pkt = Portal.newMessage(REQ_LOGOUT, userIp, serialNo or CurrentSN(), 0, secret, chap=chap)
        if mac:
            pkt.attrNum = 1
            pkt.attrs = [(255, mac)]
        return pkt

    @staticmethod
    def newAffAckAuth(userIp, secret, basip = None, serialNo = None, reqId = None, chap = True, mac = None):
        """0x07"""
        pkt = Portal.newMessage(AFF_ACK_AUTH, userIp, serialNo or CurrentSN(), reqId or 0, secret, chap=chap)
        return pkt

    @staticmethod
    def newReqInfo(userIp, secret, basip = None, serialNo = None, chap = True, mac = None):
        """0x09"""
        pkt = Portal.newMessage(REQ_INFO, userIp, serialNo or CurrentSN(), 0, secret, chap=chap)
        pkt.attrNum = 1
        pkt.attrs = [(8, '\x00\x00')]
        if mac:
            pkt.attrNum += 1
            pkt.attrs.append((255, mac))
        return pkt

    @staticmethod
    def newNtfHeart(secret, basip = None, chap = True, mac = None):
        """0x0f NTF_HEARTBEAT"""
        pkt = Portal.newMessage(NTF_HEARTBEAT, '0.0.0.0', CurrentSN(), 0, secret, chap=chap)
        if mac:
            pkt.attrNum = 1
            pkt.attrs = [(255, mac)]
        return pkt


if __name__ == '__main__':
    pkt = Portal(packet='\x02\x02\x00\x00\x1b@\x00\x00\xac\x10\x01*\x00\x00\x01\x01\x06\xf2\xc3\xa0\xfe\xf1\x0c8\xea\xfb\x9aM\x86\xb4E\x06&\x06S\xf7O\xf6')
    print repr(pkt)