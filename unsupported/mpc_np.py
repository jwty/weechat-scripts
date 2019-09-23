# -*- coding: utf-8 -*-
# install requests, beautifulsoup4 and pyimgur (https://github.com/Damgaard/PyImgur)
# make sure mpc's web interface (and preview for screencaps) is enabled and listens on $mpc_port
# set $imgur_client_id to imgur client id from https://imgur.com/account/settings/apps
# supported fields in $format fields: $file, $percentage, $bar, $positionstring, $durationstring
# $url only supported in $format-ss

from bs4 import BeautifulSoup
from string import Template
import os
import pyimgur
import requests
import urllib
import weechat as wc

NAME = 'mpc_np'
wc.register(NAME, 'janoosh', '1.5', 'BSD-2c', 'mpc-hc now playing with optional screencap', '', '')

def config(*args, **kwargs):
    options = {
        'mpc_host' : 'localhost',
        'mpc_port' : '13579',
        'screencap_path' : '/tmp/screencap.jpg',
        'imgur_client_id' : 'client_id_here', # REMEMBER TO FILL THIS IN
        'format' : 'is watching \x02$file\x02 $bar [$positionstring/$durationstring]\x02',
        'format-ss' : '$url \x02$file\x02 $bar [$positionstring/$durationstring]\x02'
    }
    for option, default in options.items():
        if not wc.config_is_set_plugin(option):
            wc.config_set_plugin(option, default)
    return wc.WEECHAT_RC_OK


def mpc_info():
    host = wc.config_get_plugin('mpc_host')
    port = wc.config_get_plugin('mpc_port')
    try:
        r = requests.get('http://{}:{}/variables.html'.format(host, port), timeout=0.5)
        output = BeautifulSoup(r.content, 'html.parser')
    except:
        wc.prnt(wc.current_buffer(), 'MPC-HC timeout')
        return wc.WEECHAT_RC_ERROR
    info={}
    for prop in ['file', 'position', 'duration', 'positionstring', 'durationstring']:
        info['{}'.format(prop)] = output.find('p', id=prop).text
    info['position'] = float(info['position'])
    info['duration'] = float(info['duration'])
    percent = int((info['position']/info['duration']) * 100)
    info['percentage'] = percent
    bar_prog = int(round((info['position']/info['duration'])*15, 1))
    bar = '['+'>'*bar_prog+'-'*(15-bar_prog)+']'
    if percent < 10:
        bar = bar[:8] + str(percent) + '%' + bar[10:]
    elif percent > 99:
        bar = bar[:7] + str(percent) + '%' + bar[11:]
    else:
        bar = bar[:7] + str(percent) + '%' + bar[10:]
    info['bar'] = bar
    return info

def upload_ss(file, positionstring):
    filepath = wc.config_get_plugin('screencap_path')
    clientid = wc.config_get_plugin('imgur_client_id')
    host = wc.config_get_plugin('mpc_host')
    port = wc.config_get_plugin('mpc_port')
    im = pyimgur.Imgur(clientid)
    urllib.urlretrieve('http://{}:{}/snapshot.jpg'.format(host, port), filepath)
    posttitle = '{}_{}'.format(file.replace(' ', '_'), positionstring)
    try:
        screencap = im.upload_image(path=filepath, title=posttitle)
    except:
        wc.prnt(wc.current_buffer(), 'Failed to upload screencap, check main buffer.')
        return ''
    try:
        os.remove(filepath)
    except OSError as e:
        wc.prnt(wc.current_buffer(), 'Failed to delete tmpfile {}: {}'.format(e.filename, e.strerror))
    url = screencap.link
    return url

def mpc_np(*args, **kwargs):
    info = mpc_info()
    npstring = Template(wc.config_get_plugin('format')).safe_substitute(info)
    wc.command(wc.current_buffer(), '/me ' + npstring)
    return wc.WEECHAT_RC_OK

def mpc_np_ss(*args, **kwargs):
    info = mpc_info()
    info['url'] = upload_ss(info['file'], info['positionstring'])
    npstring = Template(wc.config_get_plugin('format-ss')).safe_substitute(info)
    wc.command(wc.current_buffer(), '/me ' + npstring)
    return wc.WEECHAT_RC_OK

wc.hook_command('vid', 'mpc-hc now playing', '', '', '', 'mpc_np', '')
wc.hook_command('vid-ss', 'mpc-hc now playing with screenshot', '', '', '', 'mpc_np_ss', '')
wc.hook_config('plugins.var.python.' + NAME + '.mpc_host', 'config', '')
wc.hook_config('plugins.var.python.' + NAME + '.mpc_port', 'config', '')
wc.hook_config('plugins.var.python.' + NAME + '.screencap_path', 'config', '')
wc.hook_config('plugins.var.python.' + NAME + '.imgur_client_id', 'config', '')
wc.hook_config('plugins.var.python.' + NAME + '.format', 'config', '')
wc.hook_config('plugins.var.python.' + NAME + '.format-ss', 'config', '')
config()
