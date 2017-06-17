#!/usr/bin/env python
# coding=utf-8
import json
import os

class ConfigDict(dict):

    def __getattr__(self, key):
        try:
            result = self[key]
            if result and isinstance(result, dict):
                result = ConfigDict(result)
            return result
        except KeyError as k:
            raise AttributeError, k

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError, k

    def __repr__(self):
        return '<ConfigDict ' + dict.__repr__(self) + '>'


class Config(ConfigDict):

    def __init__(self, conf_file = None, **kwargs):
        if not conf_file is not None:
            raise AssertionError
            print 'loading config {0}'.format(conf_file)
            print os.path.exists(conf_file) or 'config not exists'
            return
        else:
            with open(conf_file) as cf:
                self.update(json.loads(cf.read()))
            self.update(**kwargs)
            self.conf_file = conf_file
            return

    def save(self):
        print 'update config {0}'.format(self.conf_file)
        with open(self.conf_file, 'w') as cf:
            cf.write(json.dumps(self, ensure_ascii=True, indent=4, sort_keys=True))

    def __repr__(self):
        return '<Config ' + dict.__repr__(self) + '>'


def redis_conf(config):
    eredis_url = os.environ.get('REDIS_URL')
    eredis_port = os.environ.get('REDIS_PORT')
    eredis_pwd = os.environ.get('REDIS_PWD')
    eredis_db = os.environ.get('REDIS_DB')
    is_update = any([eredis_url,
     eredis_port,
     eredis_pwd,
     eredis_db])
    if eredis_url:
        config['redis']['host'] = eredis_url
    if eredis_port:
        config['redis']['port'] = int(eredis_port)
    if eredis_pwd:
        config['redis']['passwd'] = eredis_pwd
    if eredis_db:
        config['redis']['db'] = int(eredis_db)
    if is_update:
        config.save()
    return config['redis']


def find_config(conf_file = None):
    return Config(conf_file)


if __name__ == '__main__':
    cfg = find_config('/tmp/tpconfig21')
    print cfg
    admin = {}
    admin['host'] = '192.1.1.1'
    cfg.update(admin=admin)
    cfg.ccc = u'cc'
    cfg.save()
    print cfg