# weechat-scripts
Various weechat scripts I use.

## wsl_notify.py
You need to install [BurntToast](https://github.com/Windos/BurntToast) first and modify it to work with WSL UNC paths (at least until WSL team fixes their shit). After installation find (`(Get-Module -ListAvailable BurntToast).path`, on my machine it's in `C:\Program Files\WindowsPowerShell\Modules\BurntToast`) and edit BurntToast.psm1 file. Edit lines 9 and 15 (as of 2020-11-24) so the `Optimize-BTImageSource` function looks somewhat like this (note `$Source -like '\\wsl$\*'` added to if statemets as *first* condition):
```
function Optimize-BTImageSource {
    param (
        [Parameter(Mandatory)]
        [String] $Source,

        [Switch] $ForceRefresh
    )
    if ($Source -like '\\wsl$\*' -or [bool]([System.Uri]$Source).IsUnc -or $Source -like 'http?://*') {
        $RemoteFileName = $Source -replace '/|:|\\', '-'

        $NewFilePath = '{0}\{1}' -f $Env:TEMP, $RemoteFileName

        if (!(Test-Path -Path $NewFilePath) -or $ForceRefresh) {
(...)
```
Then make sure you have `wslpath` and `wslvar` available on your WSL installation. I *think* `wslpath` is standard and `wslvar` is available by default on Ubuntu and maybe others but if it's not installed on your then grab it [here](https://github.com/wslutilities/wslu).

Then install the script as you would any other weechat python script and make sure `plugins.var.python.wsl_notify.icon_path` points to a valid icon (not sure if SVGs work), by default it points to 128x128 weechat icon on a standard Arch installation.

Then, [if you want to](https://www.youtube.com/watch?v=D58rGFasJAI), you can run `/wsl_notify gen_appid_script` in weechat and run the generated powershell script to register a separate appid for this script so it can be managed separately by windows focus assist and similar without affecting all powershell notifications. Remember to set `plugins.var.python.wsl_notify.use_custom_appid` to `on` so the script will actually use it.

## mpv_np.py
```
# make sure you start mpv with --input-ipc-server or set it in config
# set $mpv_socket to mpv socket path and $screenshot_path_capture to path with write access
# $post_url should be set to url to which POST request will be sent (for example https://example.com/upload.php)
# $upload_data is data sent with POST request, a dictionary in string form (to allow it to be stored in weechat config, later converted to dict)
# default dictionary only includes a secret field, which might not even be needed in some cases
# $file_form_name is the name of field in which screenshot will be POSTed (usually something like "upload")
# $url_field_name is used to extract url from response, this plugin excepts JSON response so set it to the name of JSON field containing url
# supported fields in $format fields: $filename, $mediatitle, $percentage, $bar, $playbacktime, $duration
# $mediatitle will default to $filename if no media title available
# $url only supported in $format-ss
```
### Usage
`/mpv` will say now playing video: `/me is watching example.mp4 [>>>>>>87%>>>>--] [10:59/12:30]`

`/mpv-ss` will say now playing video and also include url to a screenshot: `/me https://i.nicedomain.club/example.jpg video.mp4 [-------0%------] [00:00:01/01:45:00]`

Screenshots are send as a POST request so make sure you set all the config options properly. Default (mostly nonexistant) options will *not* work. Hosting services not responding in JSON are not supported (line 85 is the one you need to modify if you want to adapt it).

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
## foobar_np.py
```
# install foo_controlserver (https://github.com/audiohead/foo_controlserver)
# set port to $foobar_port, delimiter to '|||' and enable server
# enable utf-8 output/input for non-ascii characters support
# supported fields in $format: $artist, $albumartist, $date, $title, $album
```
### Usage
`/np` will say now playing track: `/me NP: "What If (Soman Remix)" by DYM from The Technocratic Deception (2012)`

## Unsupported directory
This directory contains plugins which I no longer use and do not plan on updating. For archival and reference purposes.