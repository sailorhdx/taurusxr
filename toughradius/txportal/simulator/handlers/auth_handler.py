#!/usr/bin/env python
# coding=utf-8
import struct
from twisted.internet import defer
from toughradius.txportal.packet import cmcc, huawei
from toughradius.txportal.simulator.handlers import base_handler
import functools

class AuthHandler(base_handler.BasicHandler):

    def proc_cmccv1(self, req, rundata):
        resp = cmcc.Portal.newMessage(cmcc.ACK_AUTH, req.userIp, req.serialNo, req.reqId, secret=self.secret)
        resp.attrNum = 1
        resp.attrs = [(5, 'success')]
        return resp

    def proc_cmccv2(self, req, rundata):
        resp = cmcc.Portal.newMessage(cmcc.ACK_AUTH, req.userIp, req.serialNo, req.reqId, secret=self.secret)
        resp.attrNum = 1
        resp.attrs = [(5, 'success')]
        return resp

    def proc_huaweiv1(self, req, rundata):
        resp = huawei.Portal.newMessage(huawei.ACK_AUTH, req.userIp, req.serialNo, req.reqId, secret=self.secret)
        resp.attrNum = 1
        resp.attrs = [(5, 'success')]
        return resp

    def proc_huaweiv2(self, req, rundata):
        resp = huawei.PortalV2.newMessage(huawei.ACK_AUTH, req.userIp, req.serialNo, req.reqId, self.secret, auth=req.auth, chap=req.isChap == 0)
        resp.attrNum = 1
        resp.attrs = [(5, 'success')]
        resp.auth_packet()
        return resp