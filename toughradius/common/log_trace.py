#!/usr/bin/env python
# coding=utf-8
from toughradius.toughlib import utils
from toughradius.toughlib import logger
import logging
import json
try:
    import redis
except:
    pass

class LogTrace(object):
    radius_key = 'toughradius.syslog.trace.radius.{0}'.format
    userlog_key = 'toughradius.syslog.trace.userlog.{0}'.format
    trace_key = 'toughradius.syslog.trace.{0}'.format

    def __init__(self, cache_config, db = 2):
        self.cache_config = cache_config
        self.redis = redis.StrictRedis(host=cache_config.get('host'), port=cache_config.get('port'), password=cache_config.get('passwd'), db=db)
        logger.info('LogTrace connected')

    def count(self):
        """ 日志缓存总数
        """
        return self.redis.dbsize()

    def clean(self):
        """ 日志清理缓存
        """
        logger.info('clear system trace')
        return self.redis.flushdb()

    def trace_radius(self, username, message):
        """ 跟踪用户 radius 消息
        
        :param username: 用户账号
        :type username: string
        :param message: 用户 radius 消息内容
        :type message: string
        """
        key = self.radius_key(username)
        if self.redis.llen(key) >= 512:
            self.redis.ltrim(key, 0, 511)
        self.redis.lpush(key, message)

    def trace_userlog(self, username, message):
        """ 跟踪用户诊断消息
        
        :param username: 用户账号
        :type username: string
        :param message: 用户 radius 消息内容
        :type message: string
        """
        key = self.userlog_key(username)
        if self.redis.llen(key) >= 512:
            self.redis.ltrim(key, 0, 511)
        self.redis.lpush(key, message)

    def trace_log(self, name, message):
        """ 跟踪系统日志
        
        :param name: 日志名称 (info,debug,error,exception,event,api)
        :type name: string
        :param message: 日志消息
        :type message: string
        """
        key = self.trace_key(name)
        if self.redis.llen(key) >= 512:
            self.redis.ltrim(key, 0, 511)
        self.redis.lpush(key, message)

    def list_radius(self, username):
        """ 查询用户 radius 日志
        
        :param username: 用户账号
        :type username: string        
        """
        key = self.radius_key(username)
        return [ utils.safeunicode(v) for v in self.redis.lrange(key, 0, 512) ]

    def list_userlog(self, username):
        """ 查询用户诊断日志
        
        :param username: 用户账号
        :type username: string    
        """
        key = self.userlog_key(username)
        return [ utils.safeunicode(v) for v in self.redis.lrange(key, 0, 512) ]

    def list_trace(self, name):
        """ 查询系统日志
        
        :param name: 日志名称 (info,debug,error,exception,event,api)
        :type name: string      
        """
        key = self.trace_key(name)
        return [ utils.safeunicode(v) for v in self.redis.lrange(key, 0, 512) ]

    def delete_radius(self, username):
        """ 删除用户日志
        
        :param username: 用户账号
        :type username: string          
        """
        key = self.radius_key(username)
        return self.redis.delete(key)

    def delete_trace(self, name):
        """ 删除系统日志
        
        :param name: 日志名称 (info,debug,error,exception,event,api)
        :type name: string      
        """
        key = self.trace_key(name)
        return self.redis.delete(key)

    def event_syslog_trace(self, name, message, **kwargs):
        """ syslog trace event """
        message = u'%s - %s' % (utils.get_currtime(), message)
        if 'username' in kwargs:
            self.trace_userlog(kwargs['username'], message)
        if name == 'radius' and 'username' in kwargs:
            self.trace_radius(kwargs['username'], message)
        else:
            self.trace_log(name, message)


if __name__ == '__main__':
    pass