#!/usr/bin/env python
# coding=utf-8
import re
from toughradius.toughlib import logger
cisco_fmt = re.compile('\\w+\\s\\d+/\\d+/\\d+:(\\d+).(\\d+)\\s')

def parse_cisco(req):
    """phy_slot/phy_subslot/phy_port:XPI.XCI"""
    nasportid = req.get_nas_portid()
    if not nasportid:
        return
    matchs = cisco_fmt.search(nasportid.lower())
    if matchs:
        req.vlanid1 = matchs.group(1)
        req.vlanid2 = matchs.group(2)
    return req


def parse_std(req):
    """"""
    nasportid = req.get_nas_portid()
    if not nasportid:
        return
    nasportid = nasportid.lower()

    def parse_vlanid():
        ind = nasportid.find('vlanid=')
        if ind == -1:
            return
        ind2 = nasportid.find(';', ind)
        if ind2 == -1:
            req.vlanid = int(nasportid[ind + 7])
        else:
            req.vlanid = int(nasportid[ind + 7:ind2])

    def parse_vlanid2():
        ind = nasportid.find('vlanid2=')
        if ind == -1:
            return
        ind2 = nasportid.find(';', ind)
        if ind2 == -1:
            req.vlanid2 = int(nasportid[ind + 8])
        else:
            req.vlanid2 = int(nasportid[ind + 8:ind2])

    parse_vlanid()
    parse_vlanid2()
    return req


parse_radback = parse_cisco
parse_zte = parse_cisco
parse_ros = parse_cisco
_parses = {'0': parse_std,
 '9': parse_cisco,
 '3041': parse_cisco,
 '2352': parse_radback,
 '2011': parse_std,
 '25506': parse_std,
 '39999': parse_std,
 '3902': parse_zte,
 '14988': parse_ros}

def radius_parse(req):
    try:
        vendorid = str(req.vendor_id)
        if vendorid in _parses:
            _parses[vendorid](req)
        else:
            parse_normal(req)
    except Exception as err:
        logger.exception(err, trace='radius', tag='radius_vlan_parse_error')

    return req

def parse_normal(req):
    return req

plugin_name = 'radius vlan parse'
plugin_types = ['radius_auth_req', 'radius_acct_req']
plugin_priority = 110
plugin_func = radius_parse