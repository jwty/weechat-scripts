# -*- coding: utf-8 -*-

import subprocess
import fnmatch
import time
import weechat as wc

NAME = 'wsl_notify'
AUTHOR = 'janoosh'
VERSION = '1.1'
LICENSE = 'BSD-2c'
DESCRIPTION = 'send windows toast notifications on WSL systems'

cmd_help = """silent_mode - Toggles silent mode (notifications are sent but without sound) on and off.
You can `/alias add silentmode /wsl_notify silent_mode` for easier access with /silentmode command.

gen_appid_script - Generates powershell script which will install custom windows appid.
Without it it is not possible to manage wsl_notify notifications through, for example, focus assist
without affecting all pwsh notifications. When applied it creates it's own appid which can be managed separately.
"""

# dict for checking for booleans in config variables
true = { 'on': True, 'off': False }

# window focus status variable
is_focused = True

# windows path to image (automatically generated)
image = ''

# last notification time and notification min delay
last_notification_time = 0.0
notif_delay_time = 1 # 1 second seems to be a safe value

# valid sound values list
valid_sounds = ['Default', 'IM', 'Mail', 'Reminder', 'SMS',
    'Alarm', 'Alarm2', 'Alarm3', 'Alarm4', 'Alarm5', 'Alarm6', 'Alarm7', 'Alarm8', 'Alarm9', 'Alarm10',
    'Call', 'Call2', 'Call3', 'Call4', 'Call5', 'Call6', 'Call7', 'Call8', 'Call9', 'Call10']


def config(*args, **kwargs):
    options = {
        'sound': ('IM', "Notification sound, check readme for valid values."),
        'notify_highlight': ('on', "Send notifications on nick highlights."),
        'notify_query': ('on', "Send notifications on private messages."),
        'notify_when_away': ('on', "Send notifications when away."),
        'silent_mode': ('off', "Mute the notification sound."),
        'ignore_buffers': ('', "Comma separated list of buffers to ignore highlights on."),
        'icon_path': ('/usr/share/icons/hicolor/128x128/apps/weechat.png', "Icon to show in notification. If not found defaults to default BurntToast icon or appid icon."),
        'use_custom_AppID': ('off', "Use custom AppID for notifications, for example to manage them via focus assist. Make sure to generate custom AppID first."),
    }
    for option, default in options.items():
        if not wc.config_is_set_plugin(option):
            wc.config_set_plugin(option, default[0])
            wc.config_set_desc_plugin(option, default[1])
    return wc.WEECHAT_RC_OK


def gen_appid_script(*args, **kwargs):
    image = parse_wslpath()
    script = """
    if (-NOT ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {{
        $arguments = "& '" +$myinvocation.mycommand.definition + "'"
        Start-Process powershell -Verb runAs -ArgumentList $arguments
        Break
    }}
    $AppID = 'weechat.wsl_notify'
    $AppDisplayName = 'WeeChat (via wsl_notify)'
    $AppImage = '{}'

    $HKCR = Get-PSDrive -Name HKCR -ErrorAction SilentlyContinue
    If (!($HKCR)) {{
        New-PSDrive -Name HKCR -PSProvider Registry -Root HKEY_CLASSES_ROOT -Scope Script
    }}
    $AppRegPath = "HKCR:\\AppUserModelId"
    $RegPath = "$AppRegPath\\$AppID"
    If (!(Test-Path $RegPath)) {{
        New-Item -Path $AppRegPath -Name $AppID -Force
    }}
    $DisplayName = Get-ItemProperty -Path $RegPath -Name DisplayName -ErrorAction SilentlyContinue | Select -ExpandProperty DisplayName -ErrorAction SilentlyContinue
    If ($DisplayName -ne $AppDisplayName) {{
        New-ItemProperty -Path $RegPath -Name DisplayName -Value $AppDisplayName -PropertyType String -Force
    }}
    $ShowInSettingsValue = Get-ItemProperty -Path $RegPath -Name ShowInSettings -ErrorAction SilentlyContinue | Select -ExpandProperty ShowInSettings -ErrorAction SilentlyContinue
    If ($ShowInSettingsValue -ne $ShowInSettings) {{
        New-ItemProperty -Path $RegPath -Name ShowInSettings -Value 1 -PropertyType Dword -Force
    }}
    $IconUriValue = Get-ItemProperty -Path $RegPath -Name IconUri -ErrorAction SilentlyContinue | Select -ExpandProperty IconUri -ErrorAction SilentlyContinue
    If ($IconUriValue -ne $AppImage) {{
        New-ItemProperty -Path $RegPath -Name IconUri -Value $AppImage -PropertyType ExpandString -Force
    }}
    Remove-PSDrive -Name HKCR -Force
    """.format(image)
    file_name = 'AddUpdateWeechatAppID.ps1'
    userprofile = subprocess.check_output(['wslvar', 'USERPROFILE'], text=True)
    profile_path = subprocess.check_output(['wslpath', userprofile], text=True).strip('\n')
    with open(f'{profile_path}/{file_name}','w') as file:
        file.writelines(script)
    wc.prnt(wc.buffer_search_main(), f'wsl_notify: appid script written to {profile_path}/{file_name}')
    return wc.WEECHAT_RC_OK


def parse_wslpath():
    global image
    wslpath_cmd = ['wslpath', '-w', wc.config_get_plugin('icon_path')]
    p = subprocess.run(wslpath_cmd, capture_output=True, text=True)
    if p.stdout:
        image = p.stdout.strip('\n')
    if p.stderr:
        image = 'noicon' # reset Windows image path so user notices something is wrong without having to check core buffer
        wc.prnt(wc.buffer_search_main(), f'{wc.prefix("error")}wsl_notify: Image file not found - check path')
    return image


def parse_message(data, _buffer, date, tags, displayed, highlight, prefix, message):
    highlight = bool(highlight) and true[wc.config_get_plugin('notify_highlight')]
    notify_query = true[wc.config_get_plugin('notify_query')]
    notify_when_away = true[wc.config_get_plugin('notify_when_away')]
    buffer_type = wc.buffer_get_string(_buffer, 'localvar_type')
    buffer_name = wc.buffer_get_string(_buffer, 'short_name')
    server_name = wc.buffer_get_string(_buffer, 'localvar_server')
    away = wc.buffer_get_string(_buffer, 'localvar_away')
    own_nickname = 'nick_' + wc.buffer_get_string(_buffer, 'localvar_nick')
    safe_message = message.replace("'", "''")
    if _buffer == wc.current_buffer() and is_focused:
        return wc.WEECHAT_RC_OK
    if away and not notify_when_away:
        return wc.WEECHAT_RC_OK
    if own_nickname in tags.split(','):
        return wc.WEECHAT_RC_OK
    if buffer_name in wc.config_get_plugin('ignore_buffers').split(','):
        return wc.WEECHAT_RC_OK
    if buffer_type == 'private' and notify_query:
        notify([f'{buffer_name} @ {server_name}', safe_message, buffer_name])
    elif buffer_type == 'channel' and highlight:
        notify([f'{prefix} @ {buffer_name} ({server_name})', safe_message, buffer_name])
    return wc.WEECHAT_RC_OK


def notify(notif_data):
    global last_notification_time
    if time.time() - last_notification_time < notif_delay_time:
        wc.prnt(wc.buffer_search_main(), f'wsl_notify: notification from buffer "{notif_data[2]}" suppressed - sending notifications too fast!')
        return wc.WEECHAT_RC_OK
    sound = wc.config_get_plugin('sound')
    if sound not in valid_sounds:
        wc.prnt(wc.buffer_search_main(), f'{wc.prefix("error")}wsl_notify: Invalid sound, valid sounds are: {valid_sounds}')
        sound = 'Default'
    if true[wc.config_get_plugin('silent_mode')]:
        audio_cmd = 'New-BTAudio -Silent'
    else:
        if fnmatch.fnmatch(sound, 'Alarm*') or fnmatch.fnmatch(sound, 'Call*'):
            audio_cmd = f"New-BTAudio -Source 'ms-winsoundevent:Notification.Looping.{sound}'"
        else:
            audio_cmd = f"New-BTAudio -Source 'ms-winsoundevent:Notification.{sound}'"
    appID = "-AppId 'weechat.wsl_notify'" if true[wc.config_get_plugin('use_custom_AppID')] else ''
    command = ( f"$Text1 = New-BTText -Content '{notif_data[0]}';"
        f"$Text2 = New-BTText -Content '{notif_data[1]}';"
        f"$ImagePath = '{parse_wslpath()}';"
        "$AppLogo = New-BTImage -Source $ImagePath -AppLogoOverride;"
        f"$Audio = {audio_cmd};"
        "$Binding = New-BTBinding -Children $Text1, $Text2 -AppLogoOverride $AppLogo;"
        "$Visual = New-BTVisual -BindingGeneric $Binding;"
        "$Content = New-BTContent -Visual $Visual -Audio $Audio;"
        f"Submit-BTNotification -Content $Content {appID};")
    subprocess.Popen(['powershell.exe', '-command', command], stdout=subprocess.DEVNULL)
    last_notification_time = time.time()
    return wc.WEECHAT_RC_OK


def wsl_notify_command_cb(data, buffer, args):
    if args == 'silent_mode':
        toggle_silent()
    elif args == 'gen_appid_script':
        gen_appid_script()
    else:
        wc.prnt(wc.buffer_search_main(), f'{wc.prefix("error")}wsl_notify: specify a valid command')
    return wc.WEECHAT_RC_OK


def toggle_silent():
    toggled_value = wc.config_get_plugin('silent_mode')
    toggled_value = 'on' if toggled_value == 'off' else 'off'
    wc.config_set_plugin('silent_mode', toggled_value)
    wc.prnt(wc.current_buffer(), f'wsl_notify: Silent mode is now {toggled_value}')
    return wc.WEECHAT_RC_OK


def parse_key_combos(data, signal, signal_data):
    # this method sometimes works unreliably when minimising terminal window by clicking on its icon in taskbar but I blame windows
    global is_focused
    if signal_data == '\x01[[I':
        is_focused = True
    elif signal_data == '\x01[[O':
        is_focused = False
    return wc.WEECHAT_RC_OK


wc.register(NAME, AUTHOR, VERSION, LICENSE, DESCRIPTION, '', '')
wc.command(wc.buffer_search_main(), "/print -stdout \033[?1004h") # as weechat.prnt cannot print to stdout which is required to enable focus events
wc.hook_config('plugins.var.python.' + NAME + '.*', 'config', '')
config()
wc.hook_command('wsl_notify', DESCRIPTION, 'silent_mode, gen_appid_script', cmd_help, 'silent_mode || gen_appid_script', 'wsl_notify_command_cb', '')
wc.hook_print('', '', '', 1, 'parse_message', '')
wc.hook_signal('key_combo_default', 'parse_key_combos', '')
