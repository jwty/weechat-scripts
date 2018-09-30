# weechat-plugins
Various weechat plugins
## foobar_np.py
```
# install foo_controlserver (https://github.com/audiohead/foo_controlserver)
# set port to $foobar_port, delimiter to '|||' and enable server
# enable utf-8 output/input for non-ascii characters support
# supported fields in $format: $artist, $albumartist, $date, $title, $album
```
### Usage
`/np` will say now playing track: `/me NP: "What If (Soman Remix)" by DYM from The Technocratic Deception (2012)`

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
