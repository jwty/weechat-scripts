# Unsupported plugins

## mpc_np.py
```
# install requests, beautifulsoup4 and pyimgur (https://github.com/Damgaard/PyImgur)
# make sure mpc's web interface (and preview for screencaps) is enabled and listens on $mpc_port
# set $imgur_client_id to imgur client id from https://imgur.com/account/settings/apps
# supported fields in $format fields: $file, $bar, $positionstring, $durationstring
# $url only supported in $format-ss  
```
### Usage
`/vid` will say now playing video: `/me is watching video.mp4 [-------0%------] [00:00:01/01:45:00]`

`/vid-ss` will say now playing video but also include url to a screencap (if web interface preview is enabled): `/me https://i.imgur.com/example.jpg video.mp4 [-------0%------] [00:00:01/01:45:00]`

## mpv_np.py
```
# install pyimgur (https://github.com/Damgaard/PyImgur)
# make sure you start mpv with --input-ipc-server or set it in config
# set $mpv_socket to mpv socket path and $screenshot_path_capture to path with write access
# set $imgur_client_id to imgur client id from https://imgur.com/account/settings/apps
# supported fields in $format fields: $filename, $mediatitle, $percentage, $bar, $playbacktime, $duration
# $mediatitle will default to $filename if no media title available
# $url only supported in $format-ss
```
### Usage
Behaves the same as `mpc_np.py` with the exception of `/vid` becoming `/mpv` and different format fields. See below for WSL instructions.
### WSL instructions
They get their own section. This is still a bit wonky solution (especially the paths) so I will probably improve it someday™.
```
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
```
