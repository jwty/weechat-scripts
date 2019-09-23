# weechat-plugins
Various weechat plugins. No warranty, provided as-is, etc.

## Unsupported directory
This directory contains plugins which I no longer use and do not plan on updating. For archival and reference purposes.

## foobar_np.py
```
# install foo_controlserver (https://github.com/audiohead/foo_controlserver)
# set port to $foobar_port, delimiter to '|||' and enable server
# enable utf-8 output/input for non-ascii characters support
# supported fields in $format: $artist, $albumartist, $date, $title, $album
```
### Usage
`/np` will say now playing track: `/me NP: "What If (Soman Remix)" by DYM from The Technocratic Deception (2012)`
