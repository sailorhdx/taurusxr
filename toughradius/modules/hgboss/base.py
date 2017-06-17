#!/usr/bin/env python
# coding=utf-8
import re
import traceback
from hashlib import md5
from toughradius.toughlib import utils, logger, dispatch
from toughradius.modules.base import BaseHandler
from toughradius.toughlib.permit import permit
from toughradius.common import tools
from toughradius.modules import models
from toughradius.toughlib.storage import Storage
from toughradius.modules.settings import *
from toughradius.modules.hgboss import bgwsdl
from toughradius.modules.hgboss import optwsdl

class Codes:
    SUCCESS = 0
    ERROR_IP_AUTH = 1
    ERROR_ROUTE_FAIL = 2
    ERROR_MESSAGE_FORMAT = 3
    ERROR_UN_LOGIN = 4
    ERROR_LOGIN_FAIL = 5
    ERROR_VERSION_UNSUPPORT = 6
    ERROR_REQUEST_MAX = 7
    ERROR_SERVER_BUSY = 8
    ERROR_REJECT_ACCEPT = 9
    ERROR_NOT_EXIST = 101
    ERROR_ALREADY_EXIST = 102
    ERROR_DATA_FORMAT = 103
    ERROR_NOT_RECORD = 104
    ERROR_UNKNOWN = 9999


class NULLError(BaseException):
    pass


class WsBaseHandler(BaseHandler):
    respfmt = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n       <soapenv:Body>\n          <ns1:{method}Response soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://www.ly-bns.net/wsdd/">\n             <{method}Return href="#id0"/>\n          </ns1:{method}Response>\n          <multiRef id="id0" soapenc:root="0" soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xsi:type="xsd:int" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">{code}</multiRef>\n       </soapenv:Body>\n    </soapenv:Envelope>\n    '.format
    respfmt2 = '<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n       <soapenv:Body>\n          <ns1:{method}Response soapenv:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:ns1="http://www.ly-bns.net/wsdd/">\n             <{method}Return xsi:type="soapenc:string" xmlns:soapenc="http://schemas.xmlsoap.org/soap/encoding/">{resultxml}</{method}Return>\n          </ns1:{method}Response>\n       </soapenv:Body>\n    </soapenv:Envelope>\n    '.format

    def _wsresp(self, method, code = 0, **kwargs):
        if not kwargs:
            return self.respfmt(method=method, code=code)
        xmlroot = '<Response>{0}</Response>'
        results = ['<ErrorCode>{0}</ErrorCode>'.format(code)]
        for k, v in kwargs.iteritems():
            results.append('<{k}>{v}</{k}>'.format(k=k, v=v))

        return self.respfmt2(method=method, resultxml=xmlroot.format(''.join(results)))

    def get_ws_attr(self, wsbody, attrname, defval = None, notnull = False):
        part = '.*<{attr}\\s+.*>(.*)</{attr}>.*'.format(attr=attrname)
        attrgrp = re.search(part, wsbody)
        attrval = attrgrp.group(1) if attrgrp else defval
        if attrval is None and notnull:
            raise NULLError('[SOAPError] {} is null'.format(attrname))
        return attrval.strip()

    def send_wsresp(self, method, code = 0, error = None, **kwargs):
        if error:
            logger.error(u'[SOAPError] {0}'.format(error), trace='api')
        resp = self._wsresp(method, code=code, **kwargs)
        logger.info(resp, trace='api')
        self.write(resp)

    def get(self):
        self.post()

    def post(self):
        self.set_header('Content-Type', 'text/xml;charset=utf-8')
        self.set_header('Cache-Control', 'no-cache')
        if '/interface/operategw?wsdl' == self.request.uri:
            owsurl = '{0}://{1}'.format(self.request.protocol, self.request.host)
            self.finish(optwsdl.wsdlxml(wsurl=owsurl))
            return
        if '/interface/businessgw?wsdl' == self.request.uri:
            bwsurl = '{0}://{1}'.format(self.request.protocol, self.request.host)
            self.finish(bgwsdl.wsdlxml(wsurl=bwsurl))
            return
        wsbody = self.request.body
        logger.info('recv soap message %s' % utils.safeunicode(wsbody), trace='api')
        for _method in self.methods:
            try:
                if wsbody.find('<wsdd:%s' % _method) >= 0:
                    getattr(self, _method)(wsbody)
            except NULLError:
                self.send_wsresp(_method, code=103)
            except:
                self.send_wsresp(_method, code=9999, error=traceback.format_exc())