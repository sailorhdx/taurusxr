#!/usr/bin/env python
# coding=utf-8
import os
import json
import requests
import cyclone.auth
import cyclone.escape
import cyclone.web
from toughradius.modules.base import BaseHandler, authenticated
from toughradius.modules import models
from toughradius.toughlib.permit import permit
from toughradius.toughlib import dispatch, db_cache
from toughradius.modules.settings import *
from toughradius.toughlib import utils, logger
from toughradius.modules.resource.menutpl import menutpl_str
from wechat_sdk import WechatBasic, WechatConf
import functools
if os.environ.get('LICENSE_TYPE') != 'community':

    @permit.suproute('/admin/mps/menus', u'微信公众号菜单', MenuRes, order=7.00001, is_menu=True)

    class MenusHandler(BaseHandler):

        def __init__(self, *argc, **argkw):
            super(MenusHandler, self).__init__(*argc, **argkw)
            self.MpsMenuCacheKey = 'toughee.cache.mps.menus'
            try:
                token = self.get_param_value('mps_token')
                appid = self.get_param_value('mps_appid')
                appsecret = self.get_param_value('mps_apisecret')
                encrypt_mode = self.get_param_value('mps_encrypt_mode', 'normal')
                encoding_aes_key = self.get_param_value('mps_encoding_aes_key', '')
                wechat_conf = WechatConf(token=token, appid=appid, appsecret=appsecret, encrypt_mode=encrypt_mode, encoding_aes_key=encoding_aes_key, access_token_getfunc=functools.partial(self.mpsapi.get_access_token, appid, appsecret), access_token_setfunc=self.mpsapi.set_access_token)
                self.wechat = WechatBasic(conf=wechat_conf)
            except Exception as err:
                logger.exception(err)

        def get_menu_data(self, mps_apiurl):
            try:
                _fetch_result = lambda : self.wechat.get_menu().get('menu')
                menus_obj = self.cache.aget(self.MpsMenuCacheKey, _fetch_result, expire=86400)
                if isinstance(menus_obj, (str, unicode)):
                    menus_obj = json.loads(menus_obj)
                logger.debug(menus_obj)
                return menus_obj
            except Exception as err:
                logger.exception(err)
                mstr = menutpl_str.replace('{mps_apiurl}', mps_apiurl)
                return json.loads(utils.safestr(mstr))

        @authenticated
        def get(self, template_variables = {}):
            """ 查询菜单，从数据库解析json字符串发送到页面初始化 """
            mps_apiurl = self.get_param_value('mps_apiurl', '')
            menus_obj = self.get_menu_data(mps_apiurl)
            menu_buttons_array = menus_obj['button']
            menudata = {}
            _midx = 1
            for mbs in menu_buttons_array:
                midx = 'menu%s' % _midx
                menudata['%s_name' % midx] = mbs['name']
                menudata['%s_type' % midx] = mbs.get('type', '')
                menudata['%s_key' % midx] = mbs.get('key', '')
                menudata['%s_url' % midx] = mbs.get('url', '')
                sub_buttons = mbs.get('sub_button', [])
                _idx = 1
                for sbmenu in sub_buttons:
                    menudata['%s_sub%s_type' % (midx, _idx)] = sbmenu['type']
                    menudata['%s_sub%s_name' % (midx, _idx)] = sbmenu['name']
                    menudata['%s_sub%s_key' % (midx, _idx)] = sbmenu.get('key', '')
                    menudata['%s_sub%s_url' % (midx, _idx)] = sbmenu.get('url', '')
                    _idx += 1

                _midx += 1

            menu_str = json.dumps(menudata, ensure_ascii=False).replace('"', '\\"')
            self.render('mps_menus.html', menudata=menu_str)

        @authenticated
        def post(self, *args, **kwargs):
            """ 更新菜单，保存菜单数据为json字符串 """
            menudata = self.get_argument('menudata')
            menu_json = json.loads(menudata)
            try:
                menu_object = {'button': []}
                for menu in ['menu1', 'menu2', 'menu3']:
                    menu_buttons = {'name': menu_json['%s_name' % menu]}
                    menu_type = menu_json.get('%s_type' % menu)
                    menu_url = menu_json.get('%s_url' % menu)
                    menu_key = menu_json.get('%s_key' % menu)
                    if all([menu_type, menu_url]) or all([menu_type, menu_key]):
                        menu_buttons['type'] = menu_type
                        if 'click' in menu_type:
                            menu_buttons['key'] = menu_key
                        else:
                            menu_buttons['url'] = menu_url
                        menu_object['button'].append(menu_buttons)
                        continue
                    menu_buttons['sub_button'] = []
                    for ms in range(1, 6):
                        menu_button = {}
                        _menu_type = menu_json['%s_sub%s_type' % (menu, ms)]
                        _menu_name = menu_json['%s_sub%s_name' % (menu, ms)]
                        _menu_key = menu_json['%s_sub%s_key' % (menu, ms)]
                        _menu_url = menu_json['%s_sub%s_url' % (menu, ms)]
                        if len(_menu_name) > 1:
                            menu_button['type'] = _menu_type
                            menu_button['name'] = _menu_name
                            if 'click' in _menu_type:
                                menu_button['key'] = _menu_key
                            else:
                                menu_button['url'] = _menu_url
                            menu_buttons['sub_button'].append(menu_button)

                    menu_object['button'].append(menu_buttons)

                menu_result = json.dumps(menu_object, ensure_ascii=False, sort_keys=True, indent=4, separators=(',', ': '))
                logger.info(menu_result)
                self.cache.set(self.MpsMenuCacheKey, menu_result)
                _resp = self.wechat.create_menu(menu_object)
                if int(_resp.get('errcode')) > 0:
                    logger.error(u'同步菜单失败，' + _resp.get('errmsg'))
                    logger.error(menu_result)
                    return self.render_json(code=0, msg=u'同步微信菜单失败了［%s］，请检查错误再试试' % _resp.get('errmsg'))
            except:
                logger.exception(u'更新菜单失败')
                return self.render_json(code=0, msg=u'更新菜单失败')

            self.render_json(code=0, msg=u'更新菜单成功')