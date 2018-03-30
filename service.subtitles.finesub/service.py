# -*- coding: utf-8 -*-

import re
import os
import sys
import xbmc
import json
import urllib
import urllib2
import xbmcvfs
import requests
import xbmcaddon
import lib.opensubtitles
import xbmcgui,xbmcplugin
from bs4 import BeautifulSoup
from lib.zimuku import Zimuku

__addon__ = xbmcaddon.Addon()
__author__     = __addon__.getAddonInfo('author')
__scriptid__   = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__    = __addon__.getAddonInfo('version')
__language__   = __addon__.getLocalizedString

__cwd__        = xbmc.translatePath( __addon__.getAddonInfo('path') ).decode("utf-8")
__profile__    = xbmc.translatePath( __addon__.getAddonInfo('profile') ).decode("utf-8")
__resource__   = xbmc.translatePath( os.path.join( __cwd__, 'resources', 'lib' ) ).decode("utf-8")
__temp__       = xbmc.translatePath( os.path.join( __profile__, 'temp') ).decode("utf-8")

sys.path.append (__resource__)

UserAgent  = 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'

def log(module, msg):
    if isinstance(msg, unicode): msg = msg.encode("utf-8")
    xbmc.log("{0}::{1} - {2}".format(__scriptname__,module,msg) ,level=xbmc.LOGDEBUG )

def normalizeString(str):
    return str

def search_default(search_str):
    return Zimuku(search_str).fetch_subs_list()

def search_IMDB(full_file_path):
    OS = lib.opensubtitles.OpenSubtitles(full_file_path)
    movie_info = OS.movie_info()
    log( sys._getframe().f_code.co_name ,"Get movie info from opensubtitles: <<%s>>" % json.dumps(movie_info))
    if not movie_info:
        return []
    imdb_id = movie_info.get("SeriesIMDBParent", movie_info.get("IDMovieImdb"))
    if not imdb_id:
        return []

    return search_default("tt"+imdb_id)

def Search( item ):
    subtitles_list = []
    log( sys._getframe().f_code.co_name ,"Search for [%s] by name" % (os.path.basename(item['file_original_path'])))
    if item['mansearch']:
        search_str = item['mansearchstr']
    #elif len(item['tvshow']) > 0:
    #    search_str = item['tvshow']
    #else:
    #    search_str = item['title']
        subtitles_list = search_default(search_str)

    #log( sys._getframe().f_code.co_name ,"Search result by name <<%s>>" % (subtitles_list))
    if not len(subtitles_list):
        log( sys._getframe().f_code.co_name ,"Search by imdb <<%s>>" % (json.dumps(item)))
        subtitles_list = search_IMDB(item["file_original_path"])
        log( sys._getframe().f_code.co_name ,"Search result by imdb <<%s>>" % (subtitles_list))

    if subtitles_list:
        log( sys._getframe().f_code.co_name ,"Find Subtitles <<%s>>" % (json.dumps(subtitles_list))) 
        for it in subtitles_list:
            listitem = xbmcgui.ListItem(label=it["language_name"],
                                  label2=it["filename"],
                                  iconImage=it["rating"],
                                  thumbnailImage=it["language_flag"]
                                  )

            listitem.setProperty( "sync", "false" )
            listitem.setProperty( "hearing_imp", "false" )

            url = "plugin://%s/?action=download&link=%s&lang=%s&referer=%s" % (__scriptid__,
                                                                        it["link"],
                                                                        it["lang"],
                                                                        it["referer"]
                                                                        )
            xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=url,listitem=listitem,isFolder=False)

def rmtree(path):
    if isinstance(path, unicode):
        path = path.encode('utf-8')
    dirs, files = xbmcvfs.listdir(path)
    for dir in dirs:
        rmtree(os.path.join(path, dir))
    for file in files:
        xbmcvfs.delete(os.path.join(path, file))
    xbmcvfs.rmdir(path)

def Download(url,lang, referer):
    try: rmtree(__temp__)
    except: pass
    try: os.makedirs(__temp__)
    except: pass

    subtitle_list = []
    exts = [".srt", ".sub", ".smi", ".ssa", ".ass" ]
    log( sys._getframe().f_code.co_name ,"Download page: %s" % (url))
    data = ""
    filename = ""
    try:
        req = urllib2.Request(url)
        req.add_header('User-Agent', UserAgent)
        req.add_header('Referer', referer)
        socket = urllib2.urlopen(req)
        data = socket.read()
        filename = socket.headers['Content-Disposition'].split('filename=')[1]
        filename = filename.strip('"')
    except:
        log( sys.exc_info()[2].tb_frame.f_code.co_name, "(%d) [%s]" % (
            sys.exc_info()[2].tb_lineno,
            sys.exc_info()[1]
            ))
        return []

    log( sys._getframe().f_code.co_name ,"Downloaded filename: %s, data:%s" % (filename, len(data)))
    if len(data) < 1024:
        return []
    tempfile = os.path.join(__temp__, "subtitles%s" % os.path.splitext(filename)[1])
    with open(tempfile, "wb") as subFile:
        subFile.write(data)
    xbmc.sleep(500)
    if data[:4] == 'Rar!' or data[:2] == 'PK':
        xbmc.executebuiltin(('XBMC.Extract("%s","%s")' % (tempfile,__temp__,)).encode('utf-8'), True)
    path = __temp__
    dirs, files = xbmcvfs.listdir(path)
    if len(dirs) > 0:
        path = os.path.join(__temp__, dirs[0].decode('utf-8'))
        dirs, files = xbmcvfs.listdir(path)
    list = []
    for subfile in files:
        if (os.path.splitext( subfile )[1] in exts):
            list.append(subfile.decode('utf-8'))
    if len(list) == 1:
        subtitle_list.append(os.path.join(path, list[0]))
    else:
        sel = xbmcgui.Dialog().select('请选择压缩包中的字幕', list)
        if sel == -1:
            sel = 0
        subtitle_list.append(os.path.join(path, list[sel]))

    return subtitle_list

def get_params():
    param=[]
    paramstring=sys.argv[2]
    log( sys._getframe().f_code.co_name ,"script paramstring: %s" % (paramstring))
    if len(paramstring)>=2:
        params=paramstring
        cleanedparams=params.replace('?','')
        if (params[len(params)-1]=='/'):
            params=params[0:len(params)-2]
        pairsofparams=cleanedparams.split('&')
        param={}
        for i in range(len(pairsofparams)):
            splitparams={}
            splitparams=pairsofparams[i].split('=')
            if (len(splitparams))==2:
                param[splitparams[0]]=splitparams[1]

    return param

params = get_params()
if params['action'] == 'search' or params['action'] == 'manualsearch':
    item = {}
    item['temp']               = False
    item['rar']                = False
    item['mansearch']          = False
    item['year']               = xbmc.getInfoLabel("VideoPlayer.Year")                           # Year
    item['season']             = str(xbmc.getInfoLabel("VideoPlayer.Season"))                    # Season
    item['episode']            = str(xbmc.getInfoLabel("VideoPlayer.Episode"))                   # Episode
    item['tvshow']             = normalizeString(xbmc.getInfoLabel("VideoPlayer.TVshowtitle"))   # Show
    item['title']              = normalizeString(xbmc.getInfoLabel("VideoPlayer.OriginalTitle")) # try to get original title
    item['file_original_path'] = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))  # Full path of a playing file
    item['3let_language']      = []

    if 'searchstring' in params:
        item['mansearch'] = True
        item['mansearchstr'] = params['searchstring']

    for lang in urllib.unquote(params['languages']).decode('utf-8').split(","):
        item['3let_language'].append(xbmc.convertLanguage(lang,xbmc.ISO_639_2))

    if item['title'] == "":
        item['title']  = xbmc.getInfoLabel("VideoPlayer.Title")                       # no original title, get just Title
        if item['title'] == os.path.basename(xbmc.Player().getPlayingFile()):         # get movie title and year if is filename
            title, year = xbmc.getCleanMovieTitle(item['title'])
            item['title'] = normalizeString(title.replace('[','').replace(']',''))
            item['year'] = year

    if item['episode'].lower().find("s") > -1:                                        # Check if season is "Special"
        item['season'] = "0"                                                          #
        item['episode'] = item['episode'][-1:]

    if ( item['file_original_path'].find("http") > -1 ):
        item['temp'] = True

    elif ( item['file_original_path'].find("rar://") > -1 ):
        item['rar']  = True
        item['file_original_path'] = os.path.dirname(item['file_original_path'][6:])

    elif ( item['file_original_path'].find("stack://") > -1 ):
        stackPath = item['file_original_path'].split(" , ")
        item['file_original_path'] = stackPath[0][8:]

    Search(item)

elif params['action'] == 'download':
    subs = Download(params["link"], params["lang"], params["referer"])
    for sub in subs:
        listitem = xbmcgui.ListItem(label=sub)
        xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]),url=sub,listitem=listitem,isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))
