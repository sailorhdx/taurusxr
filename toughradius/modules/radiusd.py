#!/usr/bin/env python
# coding=utf-8
import datetime
import os
import six
import msgpack
import toughradius
import importlib
from txzmq import ZmqEndpoint, ZmqFactory, ZmqPushConnection, ZmqPullConnection, ZmqREPConnection, ZmqREQConnection
from twisted.internet import protocol
from twisted.internet import reactor
from twisted.internet.threads import deferToThread
from twisted.application import service, internet
from twisted.internet import defer
from toughradius.toughlib import utils
from toughradius.toughlib import mcache
from toughradius.toughlib import logger, dispatch
from toughradius.toughlib.config import redis_conf
from toughradius.toughlib.storage import Storage
from toughradius.toughlib.redis_cache import CacheManager
from toughradius.toughlib.dbengine import get_engine
from toughradius.txradius.radius import dictionary
from toughradius.txradius.radius import packet
from toughradius.txradius.radius.packet import PacketError
from toughradius.txradius import message
from toughradius.toughlib.utils import timecast
from toughradius.modules import models
from toughradius.modules.settings import *
from toughradius.modules.radius.plugins import mac_parse, vlan_parse, rate_process
from toughradius.modules.radius.radius_authorize import RadiusAuth
from toughradius.modules.radius.radius_acct_start import RadiusAcctStart
from toughradius.modules.radius.radius_acct_update import RadiusAcctUpdate
from toughradius.modules.radius.radius_acct_stop import RadiusAcctStop
from toughradius.modules.radius.radius_acct_onoff import RadiusAcctOnoff
from toughradius.common import log_trace
from toughradius.common import eslogapi
from sqlalchemy.sql import text as _sql

class RADIUSMaster(protocol.DatagramProtocol):
    """ 
     radius协议监听主进程，本身不处理任何业务逻辑，只做消息的路由与转发。
     auth_master 和 acct_master 可以以独立的进程来运行，保证认证与记账业务互不影响。
     消息通过msgpack进行二进制封装转发，保证性能和兼容性。
    """

    def __init__(self, config, service = 'auth'):
        self.config = config
        self.service = service
        self.zmqreq = ZmqREQConnection(ZmqFactory(), ZmqEndpoint('bind', config.mqproxy[service + '_bind']))
        logger.info('%s master zmqreq bind @ ' % self.zmqreq)

    def datagramReceived(self, datagram, (host, port)):
        message = msgpack.packb([datagram, host, port])
        d = self.zmqreq.sendMsg(message)
        d.addCallback(self.reply)
        d.addErrback(logger.exception)

    def reply(self, result):
        data, host, port = msgpack.unpackb(result[0])
        self.transport.write(data, (host, int(port)))


class TraceMix:
    auth_req_plugins = []
    acct_req_plugins = []
    auth_accept_plugins = []

    def load_plugins(self, load_types = []):

        def add_plugin(pobj):
            if hasattr(pobj, 'plugin_types') and hasattr(pobj, 'plugin_name') and hasattr(pobj, 'plugin_priority') and hasattr(pobj, 'plugin_func'):
                for ptype in load_types:
                    if ptype == 'radius_auth_req' and ptype in pobj.plugin_types and pobj not in self.auth_req_plugins:
                        self.auth_req_plugins.append(pobj)
                        logger.info('load auth_req_plugin -> {} {}'.format(pobj.plugin_priority, pobj.plugin_name))
                    if ptype == 'radius_accept' and ptype in pobj.plugin_types and pobj not in self.auth_accept_plugins:
                        self.auth_accept_plugins.append(pobj)
                        logger.info('load auth_accept_plugin -> {} {}'.format(pobj.plugin_priority, pobj.plugin_name))
                    if ptype == 'radius_acct_req' and ptype in pobj.plugin_types and pobj not in self.acct_req_plugins:
                        self.acct_req_plugins.append(pobj)
                        logger.info('load acct_req_plugin -> {} {}'.format(pobj.plugin_priority, pobj.plugin_name))

        default_plugins_dir = os.path.join(os.path.dirname(__file__), 'radius/plugins')
        logger.info('start load radius plugins {} from {}'.format(load_types, default_plugins_dir))
        modules = (os.path.splitext(m)[0] for m in os.listdir(default_plugins_dir))
        for pgname in modules:
            try:
                pg_prefix = 'toughradius.modules.radius.plugins'
                add_plugin(importlib.import_module('{0}.{1}'.format(pg_prefix, pgname)))
            except Exception as err:
                logger.exception(err, trace='radius', tag='radius_plugins_load_error')

        self.auth_req_plugins = sorted(self.auth_req_plugins, key=lambda i: i.plugin_priority)
        self.acct_req_plugins = sorted(self.acct_req_plugins, key=lambda i: i.plugin_priority)
        self.auth_accept_plugins = sorted(self.auth_accept_plugins, key=lambda i: i.plugin_priority)

    def get_param_value(self, name, defval = None):

        def fetch_result():
            table = models.TrParam.__table__
            with self.db_engine.begin() as conn:
                return conn.execute(table.select().with_only_columns([table.c.param_value]).where(table.c.param_name == name)).scalar() or defval

        try:
            return self.mcache.aget(param_cache_key(name), fetch_result, expire=600)
        except Exception as err:
            logger.exception(err, trace='radius')
            return defval

    def is_trace_on(self):
        return int(self.get_param_value('radius_user_trace', 0))

    def user_exists(self, username):

        def fetch_result():
            table = models.TrAccount.__table__
            with self.db_engine.begin() as conn:
                val = conn.execute(table.select().where(table.c.account_number == username)).first()
                return val and Storage(val.items()) or None
            return

        return self.mcache.aget(account_cache_key(username), fetch_result, expire=600) is not None

    def log_trace(self, host, port, req, reply = None):
        """ 跟踪日志,需要开启全局开关
        """
        if not self.is_trace_on():
            return
        elif not self.user_exists(req.get_user_name()):
            return
        else:
            try:
                if reply is None:
                    msg = message.format_packet_log(req)
                    logger.info(u'Radius请求来自 Nas(%s:%s)  %s' % (host, port, utils.safeunicode(msg)), trace='radius', username=req.get_user_name())
                else:
                    msg = message.format_packet_log(reply)
                    logger.info(u'Radius响应至 Nas(%s:%s)  %s' % (host, port, utils.safeunicode(msg)), trace='radius', username=req.get_user_name())
            except Exception as err:
                logger.exception(err)

            return

    def find_nas(self, ip_addr):

        def fetch_result():
            table = models.TrBas.__table__
            with self.db_engine.begin() as conn:
                return conn.execute(table.select().where(table.c.ip_addr == ip_addr)).first()

        return self.mcache.aget(bas_cache_key(ip_addr), fetch_result, expire=600)


class RADIUSAuthWorker(TraceMix):
    """ 认证子进程，处理认证授权逻辑，把结果推送个 radius 协议处理主进程
    """

    def __init__(self, config, dbengine, radcache = None):
        self.config = config
        self.load_plugins(load_types=['radius_auth_req', 'radius_accept'])
        self.dict = dictionary.Dictionary(os.path.join(os.path.dirname(toughradius.__file__), 'dictionarys/dictionary'))
        self.db_engine = dbengine or get_engine(config)
        self.aes = utils.AESCipher(key=self.config.system.secret)
        self.mcache = radcache
        self.stat_pusher = ZmqPushConnection(ZmqFactory())
        self.zmqrep = ZmqREPConnection(ZmqFactory())
        self.stat_pusher.tcpKeepalive = 1
        self.zmqrep.tcpKeepalive = 1
        self.stat_pusher.addEndpoints([ZmqEndpoint('connect', config.mqproxy.task_connect)])
        self.zmqrep.addEndpoints([ZmqEndpoint('connect', config.mqproxy.auth_connect)])
        self.zmqrep.gotMessage = self.process
        self.reject_debug = int(self.get_param_value('radius_reject_debug', 0)) == 1
        logger.info('radius auth worker %s start' % os.getpid())
        logger.info('init auth worker : %s ' % self.zmqrep)
        logger.info('init auth stat pusher : %s ' % self.stat_pusher)

    def get_account_bind_nas(self, account_number):

        def fetch_result():
            with self.db_engine.begin() as conn:
                sql = '\n                select bas.ip_addr \n                from tr_bas as bas,tr_customer as cus,tr_account as user,tr_bas_node as bn\n                where cus.customer_id = user.customer_id\n                    and cus.node_id = bn.node_id\n                    and bn.bas_id = bas.id\n                    and user.account_number = :account_number\n                '
                cur = conn.execute(_sql(sql), account_number=account_number)
                ipaddrs = [ addr['ip_addr'] for addr in cur ]
                print ipaddrs
                return ipaddrs

        return self.mcache.aget(account_bind_basip_key(account_number), fetch_result, expire=600)

    def do_stat(self, code):
        try:
            stat_msg = {'statattrs': [],
             'raddata': {}}
            if code == packet.AccessRequest:
                stat_msg['statattrs'].append('auth_req')
            elif code == packet.AccessAccept:
                stat_msg['statattrs'].append('auth_accept')
            elif code == packet.AccessReject:
                stat_msg['statattrs'].append('auth_reject')
            else:
                stat_msg['statattrs'] = ['auth_drop']
            self.stat_pusher.push(msgpack.packb(stat_msg))
        except:
            pass

    def process(self, msgid, message):
        datagram, host, port = msgpack.unpackb(message)
        reply = self.processAuth(datagram, host, port)
        if not reply:
            return
        if reply.code == packet.AccessReject:
            logger.error(u'[Radiusd] :: Send Radius Reject %s' % repr(reply), tag='radius_auth_reject')
        else:
            logger.info(u'[Radiusd] :: Send radius response: %s' % repr(reply))
        if self.config.system.debug:
            logger.debug(reply.format_str())
        self.zmqrep.reply(msgid, msgpack.packb([reply.ReplyPacket(), host, port]))
        self.do_stat(reply.code)

    def createAuthPacket(self, **kwargs):
        vendor_id = kwargs.pop('vendor_id', 0)
        auth_message = message.AuthMessage(**kwargs)
        auth_message.vendor_id = vendor_id
        for plugin in self.auth_req_plugins:
            auth_message = plugin.plugin_func(auth_message)

        return auth_message

    def freeReply(self, req):
        reply = req.CreateReply()
        reply.vendor_id = req.vendor_id
        reply['Reply-Message'] = 'user:%s auth success' % req.get_user_name()
        reply.code = packet.AccessAccept
        reply_attrs = {'attrs': {}}
        reply_attrs['input_rate'] = int(self.get_param_value('radius_free_input_rate', 1048576))
        reply_attrs['output_rate'] = int(self.get_param_value('radius_free_output_rate', 4194304))
        reply_attrs['rate_code'] = self.get_param_value('radius_free_rate_code', 'freerate')
        reply_attrs['domain'] = self.get_param_value('radius_free_domain', 'freedomain')
        reply_attrs['attrs']['Session-Timeout'] = int(self.get_param_value('radius_max_session_timeout', 86400))
        for plugin in self.auth_accept_plugins:
            reply = plugin.plugin_func(reply, reply_attrs)

        return reply

    def rejectReply(self, req, errmsg = ''):
        reply = req.CreateReply()
        reply.vendor_id = req.vendor_id
        reply['Reply-Message'] = errmsg
        reply.code = packet.AccessReject
        return reply

    def processAuth(self, datagram, host, port):
        try:
            bas = self.find_nas(host)
            if not bas:
                raise PacketError('[Radiusd] :: Dropping packet from unknown host %s' % host)
            secret, vendor_id = bas['bas_secret'], bas['vendor_id']
            req = self.createAuthPacket(packet=datagram, dict=self.dict, secret=six.b(str(secret)), vendor_id=vendor_id)
            username = req.get_user_name()
            bypass = int(self.get_param_value('radius_bypass', 1))
            if req.code != packet.AccessRequest:
                raise PacketError('non-AccessRequest packet on authentication socket')
            self.log_trace(host, port, req)
            self.do_stat(req.code)
            if self.config.system.debug:
                logger.debug('[Radiusd] :: Received radius request: %s' % req.format_str())
            else:
                logger.info('[Radiusd] :: Received radius request: %s' % repr(req))
            if bypass == 2:
                reply = self.freeReply(req)
                self.log_trace(host, port, req, reply)
                return reply
            if not self.user_exists(username):
                errmsg = u'[Radiusd] :: user:%s not exists' % username
                reply = self.rejectReply(req, errmsg)
                self.log_trace(host, port, req, reply)
                return reply
            bind_nas_list = self.get_account_bind_nas(username)
            if not bind_nas_list or host not in bind_nas_list:
                errmsg = u'[Radiusd] :: nas_addr:%s not bind for user:%s node' % (host, username)
                reply = self.rejectReply(req, errmsg)
                self.log_trace(host, port, req, reply)
                return reply
            aaa_request = dict(account_number=username, domain=req.get_domain(), macaddr=req.client_mac, nasaddr=req.get_nas_addr(), vlanid1=req.vlanid1, vlanid2=req.vlanid2, bypass=bypass, radreq=req)
            auth_resp = RadiusAuth(self.db_engine, self.mcache, self.aes, aaa_request).authorize()
            if auth_resp['code'] > 0:
                reply = self.rejectReply(req, auth_resp['msg'])
                self.log_trace(host, port, req, reply)
                return reply
            reply = req.CreateReply()
            reply.code = packet.AccessAccept
            reply.vendor_id = req.vendor_id
            reply['Reply-Message'] = 'user:%s auth success' % username
            reply_attrs = {}
            reply_attrs.update(auth_resp)
            reply_attrs.update(req.resp_attrs)
            for plugin in self.auth_accept_plugins:
                reply = plugin.plugin_func(reply, reply_attrs)
            if not req.VerifyReply(reply):
                raise PacketError('[Radiusd] :: user:%s auth verify reply error' % username)
            self.log_trace(host, port, req, reply)
            return reply
        except Exception as err:
            if not self.reject_debug:
                self.do_stat(0)
                logger.exception(err, tag='radius_auth_error')
            else:
                reply = self.rejectReply(req, repr(err))
                self.log_trace(host, port, req, reply)
                return reply


class RADIUSAcctWorker(TraceMix):
    """ 记账子进程，处理计费逻辑，把结果推送个 radius 协议处理主进程，
    记账是异步处理的，即每次收到记账消息时，立即推送响应，然后在后台异步处理计费逻辑。
    """

    def __init__(self, config, dbengine, radcache = None):
        self.config = config
        self.load_plugins(load_types=['radius_acct_req'])
        self.db_engine = dbengine or get_engine(config)
        self.mcache = radcache
        self.dict = dictionary.Dictionary(os.path.join(os.path.dirname(toughradius.__file__), 'dictionarys/dictionary'))
        self.stat_pusher = ZmqPushConnection(ZmqFactory())
        self.zmqrep = ZmqREPConnection(ZmqFactory())
        self.stat_pusher.tcpKeepalive = 1
        self.zmqrep.tcpKeepalive = 1
        self.stat_pusher.addEndpoints([ZmqEndpoint('connect', config.mqproxy.task_connect)])
        self.zmqrep.addEndpoints([ZmqEndpoint('connect', config.mqproxy.acct_connect)])
        self.zmqrep.gotMessage = self.process
        self.acct_class = {STATUS_TYPE_START: RadiusAcctStart,
         STATUS_TYPE_STOP: RadiusAcctStop,
         STATUS_TYPE_UPDATE: RadiusAcctUpdate,
         STATUS_TYPE_ACCT_ON: RadiusAcctOnoff,
         STATUS_TYPE_ACCT_OFF: RadiusAcctOnoff}
        logger.info('radius acct worker %s start' % os.getpid())
        logger.info('init acct worker : %s ' % self.zmqrep)
        logger.info('init acct stat pusher : %s ' % self.stat_pusher)

    def do_stat(self, code, status_type = 0, req = None):
        try:
            stat_msg = {'statattrs': ['acct_drop'],
             'raddata': {}}
            if code in (4, 5):
                stat_msg['statattrs'] = []
                if code == packet.AccountingRequest:
                    stat_msg['statattrs'].append('acct_req')
                elif code == packet.AccountingResponse:
                    stat_msg['statattrs'].append('acct_resp')
                if status_type == 1:
                    stat_msg['statattrs'].append('acct_start')
                elif status_type == 2:
                    stat_msg['statattrs'].append('acct_stop')
                elif status_type == 3:
                    stat_msg['statattrs'].append('acct_update')
                    stat_msg['raddata']['input_total'] = req.get_input_total()
                    stat_msg['raddata']['output_total'] = req.get_output_total()
                elif status_type == 7:
                    stat_msg['statattrs'].append('acct_on')
                elif status_type == 8:
                    stat_msg['statattrs'].append('acct_off')
            self.stat_pusher.push(msgpack.packb(stat_msg))
        except:
            pass

    def process(self, msgid, message):
        datagram, host, port = msgpack.unpackb(message)
        reply = self.processAcct(datagram, host, port)
        self.zmqrep.reply(msgid, msgpack.packb([reply.ReplyPacket(), host, port]))

    def createAcctPacket(self, **kwargs):
        vendor_id = kwargs.pop('vendor_id', 0)
        acct_message = message.AcctMessage(**kwargs)
        acct_message.vendor_id = vendor_id
        for plugin in self.acct_req_plugins:
            acct_message = plugin.plugin_func(acct_message)

        return acct_message

    def processAcct(self, datagram, host, port):
        try:
            bas = self.find_nas(host)
            if not bas:
                raise PacketError('[Radiusd] :: Dropping packet from unknown host %s' % host)
            secret, vendor_id = bas['bas_secret'], bas['vendor_id']
            req = self.createAcctPacket(packet=datagram, dict=self.dict, secret=six.b(str(secret)), vendor_id=vendor_id)
            self.log_trace(host, port, req)
            self.do_stat(req.code, req.get_acct_status_type(), req=req)
            if self.config.system.debug:
                logger.debug('[Radiusd] :: Received radius request: %s' % req.format_str())
            else:
                logger.info('[Radiusd] :: Received radius request: %s' % repr(req))
            if req.code != packet.AccountingRequest:
                raise PacketError('non-AccountingRequest packet on authentication socket')
            if not req.VerifyAcctRequest():
                raise PacketError('VerifyAcctRequest error')
            status_type = req.get_acct_status_type()
            if status_type in self.acct_class:
                ticket = req.get_ticket()
                if not ticket.get('nas_addr'):
                    ticket['nas_addr'] = host
                acct_func = self.acct_class[status_type](self.db_engine, self.mcache, None, ticket).acctounting
                reactor.callLater(0.05, acct_func)
            else:
                raise ValueError('status_type <%s> not support' % status_type)
            reply = req.CreateReply()
            reactor.callLater(0.05, self.log_trace, host, port, req, reply)
            reactor.callLater(0.05, self.do_stat, reply.code)
            if self.config.system.debug:
                logger.debug('[Radiusd] :: Send radius response: %s' % reply.format_str())
            else:
                logger.info('[Radiusd] :: Send radius response: %s' % repr(reply))
            return reply
        except Exception as err:
            self.do_stat(0)
            logger.exception(err, tag='radius_acct_drop')

        return


def run_auth(config, **kwargs):
    auth_protocol = RADIUSMaster(config, service='auth')
    reactor.listenUDP(int(config.radiusd.auth_port), auth_protocol, interface=config.radiusd.host)


def run_acct(config, **kwargs):
    acct_protocol = RADIUSMaster(config, service='acct')
    reactor.listenUDP(int(config.radiusd.acct_port), acct_protocol, interface=config.radiusd.host)


def run_worker(config, dbengine, service = None, **kwargs):
    _cache = kwargs.pop('cache', CacheManager(redis_conf(config), cache_name='RadiusWorkerCache-%s' % os.getpid()))
    if not kwargs.get('standalone'):
        logger.info('start register radiusd events')
        dispatch.register(log_trace.LogTrace(redis_conf(config)), check_exists=True)
        if 'elasticsearch' in config:
            dispatch.register(eslogapi.EslogApi(config.elasticsearch))
        event_params = dict(dbengine=dbengine, mcache=_cache, aes=kwargs.pop('aes', None))
        event_path = os.path.abspath(os.path.dirname(toughradius.modules.events.__file__))
        dispatch.load_events(event_path, 'toughradius.modules.events', event_params=event_params)
    auth_worker = RADIUSAuthWorker(config, dbengine, radcache=_cache)
    acct_worker = RADIUSAcctWorker(config, dbengine, radcache=_cache)
    return