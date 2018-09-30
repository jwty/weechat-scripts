# -*- coding: utf-8 -*-
# install foo_controlserver (https://github.com/audiohead/foo_controlserver)
# set port to $foobar_port, delimiter to '|||' and enable server
# supported fields in $format: $artist, $albumartist, $date, $title, $album

import weechat as wc
from telnetlib import Telnet
from string import Template

name = 'foobar_np'
wc.register(name, 'janoosh', '2137', 'BSD-2c', 'foobar now playing', '', '')

def config(*args, **kwargs):
    options = {
        'foobar_host' : 'localhost',
        'foobar_port' : '3333',
        'format' : 'NP: $title by $artist from $album ($date)'
    }
    for option, default in options.items():
        if not wc.config_is_set_plugin(option):
            wc.config_set_plugin(option, default)
    return wc.WEECHAT_RC_OK

def np(*args, **kwargs):
    host = wc.config_get_plugin('foobar_host')
    port = wc.config_get_plugin('foobar_port')
    try:
        tn = Telnet(host, port, timeout=3)
    except Exception as error:
        wc.prnt(wc.current_buffer(), 'Cannot connect to foobar: {}'.format(error))
        return wc.WEECHAT_RC_ERROR
    tn.expect([b'11'])
    rawline = tn.read_until(b'\n', timeout=3)
    tn.close()
    rawline = rawline.decode('utf-8').split('|||')
    status = int(rawline[0])
    if status == 2:
        npstring = 'NP: nothing'
    else:
        fields = {
            'albumartist' : rawline[6],
            'album' : rawline[7],
            'date' : rawline[8],
            'title' : rawline[11],
            'artist' : rawline[12]
        }
        nptemplate = wc.config_get_plugin('format')
        npstring = Template(nptemplate).safe_substitute(fields)
    wc.command(wc.current_buffer(), '/me ' + npstring)
    return wc.WEECHAT_RC_OK

wc.hook_command('np', 'foobar now playing', '', '', '', 'np', '')
wc.hook_config('plugins.var.python.' + name + '.foobar_host', 'config', '')
wc.hook_config('plugins.var.python.' + name + '.foobar_port', 'config', '')
wc.hook_config('plugins.var.python.' + name + '.format', 'config', '')
config()
