#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import utils, logger, dispatch
from cyclone import httpclient
from hashlib import md5
from urllib import urlencode
from toughradius.modules import models
from toughradius.toughlib.mail import send_mail as sendmail
from toughradius.modules.events.event_basic import BasicEvent

class SendEmailEvent(BasicEvent):

    def on_email_done(self, resp):
        _body = utils.safeunicode(resp.body)
        logger.info(u'邮件发送响应; %s %s' % _body, trace='event')
        return resp

    def on_email_error(self, err):
        logger.info(u'邮件发送失败; %s %s' % str(err), trace='event')
        return err

    def event_sendmail(self, mailto, topic, content = None):
        smtp_server = self.get_param_value('smtp_server', '127.0.0.1')
        from_addr = self.get_param_value('smtp_from')
        smtp_port = int(self.get_param_value('smtp_port', 25))
        smtp_user = self.get_param_value('smtp_user', None)
        smtp_pwd = self.get_param_value('smtp_pwd', None)
        smtp_tls = int(self.get_param_value('smtp_tls', '0')) == 1
        d = sendmail(server=smtp_server, port=smtp_port, user=smtp_user, password=smtp_pwd, from_addr=from_addr, mailto=mailto, topic=topic, content=content, tls=smtp_tls)
        d.addCallbacks(self.on_email_done, self.on_email_error)
        return d


def __call__(dbengine = None, mcache = None, **kwargs):
    return SendEmailEvent(dbengine=dbengine, mcache=mcache, **kwargs)