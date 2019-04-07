# -*- coding: utf-8 -*-
# install pyimgur (https://github.com/Damgaard/PyImgur)
# make sure you start mpv with --input-ipc-server or set it in config
# set $mpv_socket to mpv socket path and $screenshot_path_capture to path with write access
# set $imgur_client_id to imgur client id from https://imgur.com/account/settings/apps
# supported fields in $format fields: $filename, $mediatitle, $percentage, $bar, $playbacktime, $duration
# $mediatitle will default to $filename if no media title available
# $url only supported in $format-ss
# WSL ONLY INSTRUCTIONS (weechat in WSL, mpv on windows) (are you a masochist? because i am):
# * instead of unix socket use a named pipe path in --input-ipc-server (for example \\.\pipe\mpv-pipe)
# * install npiperelay (https://github.com/jstarks/npiperelay) and socat
# * route pipe to $mpv_socket, for example:
#   `socat UNIX-LISTEN:/tmp/mpvsocket,fork EXEC:"npiperelay.exe -ep -s //./pipe/mpv-pipe",nofork`
# * $screenshot_path_capture is passed to mpv on windows so path must be windows-style but with *forward* slashes
#   and mpv must have write access there (idk how exactly this works, best to just set it to mpv install dir)
# * $screenshot_path_upload points to screenshot from WSL perspective, so unix-style path is required
#   for example '/mnt/c/mpv/screenshot.jpg'
# * if $screenshot_path_upload does not match $screenshot_path_capture the screenshot will not upload:
#   'Failed to upload screenshot: [Errno 2] No such file or directory: '/mnt/c/mpv/np_screenshot.jpg''
#   (this applies to other path mistakes so check them carefully, script will skip $url if upload errors out)
# TODO:
# * option to keep captured screenshots with timestamps etc.
# * better WSL handling i guess

import sys
from string import Template
import weechat as wc
import json
import os
import pyimgur
import re
import socket
import time

reload(sys)
sys.setdefaultencoding('utf-8') #what a hack
NAME = 'mpv_np'
wc.register(NAME, 'janoosh', '1.2', 'BSD-2c', 'mpv now playing with optional screenshot (and WSL support)', '', '')
# import pybuffer # debug, install pybuffer script to use
# debug = pybuffer.debugBuffer(globals(), "mpv_np")

def config(*args, **kwargs):
    options = {
        'mpv_socket' : '/tmp/mpvsocket',
        'screenshot_path_capture' : '/tmp/mpv-screenshot.jpg',
        'screenshot_path_upload' : '', # leave empty unless using WSL; refer to readme
        'imgur_client_id' : 'client_id_here', # REMEMBER TO FILL THIS IN
        'format' : 'is watching \x02$mediatitle\x02 $bar [$playbacktime/$duration]\x02',
        'format-ss' : '$url \x02$mediatitle\x02 $bar [$playbacktime/$duration]\x02'
    }
    for option, default in options.items():
        if not wc.config_is_set_plugin(option):
            wc.config_set_plugin(option, default)
    return wc.WEECHAT_RC_OK

def mpv_take_screenshot(filename, playbacktime):
    mpv_socket = wc.config_get_plugin('mpv_socket')
    imgur_id = wc.config_get_plugin('imgur_client_id')
    filepath_screenshot = wc.config_get_plugin('screenshot_path_capture')
    filepath_upload = wc.config_get_plugin('screenshot_path_upload')
    filepath_upload = filepath_upload if filepath_upload else filepath_screenshot
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(mpv_socket)
    request = '{"command": ["screenshot-to-file","%s"]}\n' %filepath_screenshot
    client.send(request)
    for retries in range(0,10):
        try:
            client.recv(512)
            break
        except Exception as e:
            # wc.prnt(wc.current_buffer(), 'recv error (screenshot): {}'.format(e)) #debug
            continue
    client.close()
    im = pyimgur.Imgur(imgur_id)
    posttitle = '{}_{}'.format(filename.replace(' ', '_'), playbacktime)
    try:
        for retries in range(0,10):
            try:
                screenshot = im.upload_image(path=filepath_upload, title=posttitle)
                break
            except Exception as e:
                # wc.prnt(wc.current_buffer(), 'Failed to connect: {}'.format(e)) # debug
                continue
    except Exception as e:
        wc.prnt(wc.current_buffer(), 'Failed to upload screenshot: {}'.format(e))
        return ''
    try:
        os.remove(filepath_upload)
    except OSError as e:
        wc.prnt(wc.current_buffer(), 'Failed to delete screenshot {}: {}'.format(e.filename, e.strerror))
    url = screenshot.link
    return url

def mpv_info():
    mpv_socket = wc.config_get_plugin('mpv_socket')
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    client.connect(mpv_socket)
    info = {}
    for prop in ['filename', 'media-title', 'playback-time', 'duration']:
        request = '{"command": ["get_property", "%s"]}\n' %prop
        client.send(request)
        for retries in range(0,10):
            try:
                info[prop] = json.loads(client.recv(1024))['data']
                break
            except Exception as e:
                # wc.prnt(wc.current_buffer(), 'recv error: {}'.format(e)) # debug
                continue

    client.close()
    duration = info['duration']
    wc.prnt(wc.current_buffer(), 'duration: {}'.format(info['duration']))
    percent = int((info['playback-time']/info['duration']) * 100)
    info['percentage'] = percent
    bar_prog = int(round((info['playback-time']/info['duration'])*15, 1))
    bar = '['+'>'*bar_prog+'-'*(15-bar_prog)+']'
    if percent < 10:
        bar = bar[:8] + str(percent) + '%' + bar[10:]
    elif percent > 99:
        bar = bar[:7] + str(percent) + '%' + bar[11:]
    else:
        bar = bar[:7] + str(percent) + '%' + bar[10:]
    info['bar'] = bar
    info['filename'] = info['filename'].replace('_', ' ').encode("utf-8")
    # hyphen removal necessary because of string.Template restrictions
    info['mediatitle'] = info.pop('media-title').replace('_', ' ').encode("utf-8")
    if info['duration'] > 3600:
        time_string = "%H:%M:%S"
    else:
        time_string = "%M:%S"
    info['playbacktime'] = time.strftime(time_string, time.gmtime(info.pop('playback-time')))
    info['duration'] = time.strftime(time_string, time.gmtime(info['duration']))
    return info

def mpv_np(*args, **kwargs):
    try:
        info = mpv_info()
    except Exception as e:
        wc.prnt(wc.current_buffer(), 'Failed to get mpv info (is socket available?): {}'.format(e))
        return wc.WEECHAT_RC_ERROR
    npstring = Template(wc.config_get_plugin('format')).safe_substitute(info)
    wc.command(wc.current_buffer(), '/me ' + npstring)
    return wc.WEECHAT_RC_OK

def mpv_np_screenshot(*args, **kwargs):
    try:
        info = mpv_info()
        info['url'] = mpv_take_screenshot(info['filename'], info['playbacktime'])
    except Exception as e:
        wc.prnt(wc.current_buffer(), 'Failed to get mpv info (is socket available?): {}'.format(e))
        return wc.WEECHAT_RC_ERROR
    npstring = Template(wc.config_get_plugin('format-ss')).safe_substitute(info)
    wc.command(wc.current_buffer(), '/me ' + npstring)
    return wc.WEECHAT_RC_OK

wc.hook_command("mpv", "Now playing mpv", "", "", "", "mpv_np", "")
wc.hook_command("mpv-ss", "Now playing mpv with screenshot", "", "", "", "mpv_np_screenshot", "")
wc.hook_config('plugins.var.python.' + NAME + '.mpv_socket', 'config', '')
wc.hook_config('plugins.var.python.' + NAME + '.screenshot_path_capture', 'config', '')
wc.hook_config('plugins.var.python.' + NAME + '.screenshot_path_upload', 'config', '')
wc.hook_config('plugins.var.python.' + NAME + '.imgur_client_id', 'config', '')
wc.hook_config('plugins.var.python.' + NAME + '.format', 'config', '')
wc.hook_config('plugins.var.python.' + NAME + '.format-ss', 'config', '')
config()
