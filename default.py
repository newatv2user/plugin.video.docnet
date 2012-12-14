import urllib, urllib2, re, sys, cookielib, os
import xbmc, xbmcgui, xbmcplugin, xbmcaddon, xbmcvfs
import CommonFunctions
import hosts

# plugin constants
version = "0.0.1"
plugin = "Documentary.Net - " + version
#pluginHandle = int(sys.argv[1])

__settings__ = xbmcaddon.Addon(id='plugin.video.docnet')
rootDir = __settings__.getAddonInfo('path')
if rootDir[-1] == ';':
    rootDir = rootDir[0:-1]
rootDir = xbmc.translatePath(rootDir)
settingsDir = __settings__.getAddonInfo('profile')
settingsDir = xbmc.translatePath(settingsDir)
cacheDir = os.path.join(settingsDir, 'cache')

dbg = False # Set to false if you don't want debugging
dbglevel = 3 # Do NOT change from 3

common = CommonFunctions#.CommonFunctions()
common.plugin = plugin

common.dbg = False

programs_thumb = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'programs.png')
topics_thumb = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'topics.png')
search_thumb = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'search.png')
next_thumb = os.path.join(__settings__.getAddonInfo('path'), 'resources', 'media', 'next.png')

pluginhandle = int(sys.argv[1])

########################################################
## URLs
########################################################
SITE = 'http://documentary.net'
BROWSE = '/category/films/about/'
SEARCHURL = '/?s=%s&searchsubmit='

########################################################
## Modes
########################################################
M_DO_NOTHING = 0
M_Browse = 1
#M_Browse_All = 2
M_Search = 3
M_GET_VIDEO_LINKS = 4
M_Categories = 7

##################
## Class for items
##################
class VideoItem:
    def __init__(self):
        self.Title = ''
        self.Plot = ''
        self.Image = ''
        self.Url = ''
        
## Get URL
def getURL( url ):
    print plugin + ' getURL :: url = ' + url
    cj = cookielib.LWPCookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2;)')]
    usock=opener.open(url)
    response=usock.read()
    usock.close()
    return response

# Save page locally
def save_web_page(url):
    f = open(os.path.join(cacheDir, 'docnet.html'), 'w')
    data = getURL(url)
    f.write(data)
    f.close()
    return data
    
# Read from locally save page
def load_local_page():
    f = open(os.path.join(cacheDir, 'docnet.html'), 'r')
    data = f.read()
    f.close()
    return data

# Remove HTML codes
def cleanHtml( dirty ):
    clean = re.sub('&quot;', '\"', dirty)
    clean = re.sub('&#039;', '\'', clean)
    clean = re.sub('&#215;', 'x', clean)
    clean = re.sub('&#038;', '&', clean)
    clean = re.sub('&#8216;', '\'', clean)
    clean = re.sub('&#8217;', '\'', clean)
    clean = re.sub('&#8211;', '-', clean)
    clean = re.sub('&#8220;', '\"', clean)
    clean = re.sub('&#8221;', '\"', clean)
    clean = re.sub('&#8212;', '-', clean)
    clean = re.sub('&amp;', '&', clean)
    clean = re.sub("`", '', clean)
    clean = re.sub('<em>', '[I]', clean)
    clean = re.sub('</em>', '[/I]', clean)
    clean = re.sub('&lt;', '<', clean)
    return clean

########################################################
## Mode = None
## Build the main directory
########################################################
def BuildMainDirectory():
    Browse('')

###########################################################
## Mode == M_Categories
## Browse all documentaries
###########################################################
def Categories():
    contents = load_local_page()
    Categories_List = []
    sidebarshell = common.parseDOM(contents, "div", attrs={"id": "sidebar-shell-1"})[0]
    catDOM = common.parseDOM(sidebarshell, "a")
    hrefDOM = common.parseDOM(sidebarshell, "a", ret="href")
    #print 'Debug Info - catDOM length: ' + str(len(catDOM))
    i = 0
    for dCat in catDOM:
        #print 'Debug Info: ' + dCat
        if dCat is None or dCat == '':
            continue        
        #Title = common.stripTags(dCat)
        Title = dCat
        Title = cleanHtml(Title)
        #href = common.parseDOM(dCat, "a", ret="href")
        '''if len(href) > 1:
            continue
        if href[0].find('films') == -1:
            continue'''
        #Url = href[0]
        Url = hrefDOM[i]
        catItem = VideoItem()
        catItem.Title = Title
        catItem.Url = Url
        Categories_List.append(catItem)
        i += 1
        
    #print 'Number of Cats: ' + str(len(Categories_List))
    for CatItem in Categories_List:
        problemTitle = ''
        try:
            problemTitle = CatItem.Title.encode('utf-8')
        except:
            problemTitle = CatItem.Title
        #print problemTitle
        if CatItem.Url == '':
            mode = M_DO_NOTHING
        else:
            mode = M_Browse
        #xbmc.log(CatItem.Url)
        addDir(problemTitle, CatItem.Url, mode, CatItem.Image, '', '', CatItem.Plot)
        
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

###########################################################
## Mode == M_Browse
## Browse documentaries. All or by categories
###########################################################   
def Browse(url):
    #print 'Ready to browse now.'
    # set content type so library shows more views and info
    xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    if url == '':
        url = SITE + BROWSE
        contents = save_web_page(url)
    else: 
        contents = getURL(url)
    
    itemsDOM = common.parseDOM(contents, "article", attrs = { "class": 'suf-tile [^"]+'})
    for item in itemsDOM:
        #print 'WTF: ' + item
        listItem = VideoItem()
        Title = common.parseDOM(item, "img", ret="alt")
        #print Title
        Title1 = common.replaceHTMLCodes(common.stripTags(Title[0]))
        Title2 = cleanHtml(Title1)
        listItem.Title = Title2
        #xbmc.log(Title[0])
            
        Plot = common.parseDOM(item, "p")
        Plot1 = common.replaceHTMLCodes(common.stripTags(Plot[0]))
        Plot2 = cleanHtml(Plot1)
        listItem.Plot = Plot2
        #xbmc.log(common.stripTags(Plot[0]))
            
        Image = common.parseDOM(item, "img", ret="src")
        listItem.Image = Image[0]
            
        Url = common.parseDOM(item, "a", ret="href")
        listItem.Url = Url[0]
        #Featured_List.append(listItem)
        #xbmc.log(listItem.Title)
        addDir(listItem.Title, listItem.Url, M_GET_VIDEO_LINKS, listItem.Image, '', '', listItem.Plot)
    
    try:
        currentPage = common.parseDOM(contents, "span", attrs={ "class": "page-numbers current"})[0]
        currentPage = int(currentPage)
        nextPage = common.parseDOM(contents, "a", attrs={ "class": "page-numbers"})[0]
        nextPage = int(nextPage)
        #nextPage = re.compile('class="next page-numbers" href="([^"]+)"').findall(contents)
        #for url in nextPage:
        #    addDir('Next', SITE + url, M_Browse, next_thumb, '', '', '')
        if nextPage > currentPage:
            url = common.parseDOM(contents, "a", attrs={ "class": "page-numbers"}, ret="href")[0]
            addDir('Next', SITE + url, M_Browse, next_thumb, '', '', '')
    except:
        pass
    # Other Menu Items
    bottom = [
        (__settings__.getLocalizedString(30014), topics_thumb, M_Categories),
        (__settings__.getLocalizedString(30015), search_thumb, M_Search)
        ]
    for name, thumbnailImage, mode in bottom:
        addDir(name, '', mode, thumbnailImage, '', '', '')

    xbmcplugin.endOfDirectory(int(sys.argv[1]))
    SetViewMode()

###########################################################
## Mode == M_GET_VIDEO_LINKS
## Try to get a list of playable items and play it.
###########################################################
def Playlist(url):
    #print 'Fetching links from ' + url
    Matches = None
    try:
        xbmc.executebuiltin( "ActivateWindow(busydialog)" )
        contents = getURL(url)
    
        itemsDOM = common.parseDOM(contents, "div", attrs = { "id": "vidback"})
        Matches = hosts.resolve(itemsDOM[0])
    except:
        pass
    finally:
        xbmc.executebuiltin( "Dialog.Close(busydialog)" )
    if Matches == None or len(Matches) == 0:
        xbmcplugin.setResolvedUrl(pluginhandle, False, 
                                  xbmcgui.ListItem())
        dialog = xbmcgui.Dialog()
        ok = dialog.ok('Nothing to play', 'A playable url could not be found.')
        return
    #print Matches[0]
    if Matches[0].find('playlist') > 0:
        #print Matches[0]
        #listitem = xbmcgui.ListItem(path=Matches[0])
        #listitem.setProperty("IsPlayable", "true")
        #return xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)
        return xbmc.executebuiltin("xbmc.PlayMedia("+Matches[0]+")")
        #return xbmcplugin.setResolvedUrl(pluginhandle, True, 
        #                          xbmcgui.ListItem(path=Matches[0]))
        
    playList = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playList.clear()
    for PlayItem in Matches:
        #print PlayItem
        listitem = xbmcgui.ListItem('Video')
        listitem.setInfo( type="video", infoLabels={ "Title": name } )
        listitem.setProperty("IsPlayable", "true")
        playList.add(url=PlayItem, listitem=listitem)
    xbmcPlayer = xbmc.Player()
    xbmcPlayer.play(playList)
    #playList.clear()

# Set View Mode selected in the setting
def SetViewMode():
    try:
        # if (xbmc.getSkinDir() == "skin.confluence"):
        if __settings__.getSetting('view_mode') == "1": # List
            xbmc.executebuiltin('Container.SetViewMode(502)')
        if __settings__.getSetting('view_mode') == "2": # Big List
            xbmc.executebuiltin('Container.SetViewMode(51)')
        if __settings__.getSetting('view_mode') == "3": # Thumbnails
            xbmc.executebuiltin('Container.SetViewMode(500)')
        if __settings__.getSetting('view_mode') == "4": # Poster Wrap
            xbmc.executebuiltin('Container.SetViewMode(501)')
        if __settings__.getSetting('view_mode') == "5": # Fanart
            xbmc.executebuiltin('Container.SetViewMode(508)')
        if __settings__.getSetting('view_mode') == "6":  # Media info
            xbmc.executebuiltin('Container.SetViewMode(504)')
        if __settings__.getSetting('view_mode') == "7": # Media info 2
            xbmc.executebuiltin('Container.SetViewMode(503)')
            
        if __settings__.getSetting('view_mode') == "0": # Default Media Info for Quartz
            xbmc.executebuiltin('Container.SetViewMode(52)')
    except:
        print "SetViewMode Failed: " + __settings__.getSetting('view_mode')
        print "Skin: " + xbmc.getSkinDir()

# Search documentaries
def SEARCH(url):
        # set content type so library shows more views and info
        xbmcplugin.setContent(int(sys.argv[1]), 'movies')
    
        if url is None or url == '':
            keyb = xbmc.Keyboard('', 'Search Documentary.net')
            keyb.doModal()
            if (keyb.isConfirmed() == False):
                return
            search = keyb.getText()
            if search is None or search == '':
                return
            encSrc = urllib.quote(search)
            url = SITE + SEARCHURL % encSrc
        contents = getURL(url)
        itemsDOM = common.parseDOM(contents, "div", attrs = { "class": "post-[0-9]{1,} post.+?"})
        for item in itemsDOM:
            #print item
            listItem = VideoItem()
            Title = common.parseDOM(item, "a", attrs = { "class": "entry-title" }, ret="title")
            Title1 = common.replaceHTMLCodes(common.stripTags(Title[0]))
            Title2 = cleanHtml(Title1)
            listItem.Title = Title2
            #xbmc.log(Title[0])
            
            Plot = common.parseDOM(item, "p")
            Plot1 = common.replaceHTMLCodes(common.stripTags(Plot[0]))
            Plot2 = cleanHtml(Plot1)
            listItem.Plot = Plot2
            #xbmc.log(common.stripTags(Plot[0]))
            
            Image = common.parseDOM(item, "img", ret="src")
            if Image:
                listItem.Image = Image[0]
            else:
                listItem.Image = ''
            
            Url = common.parseDOM(item, "a", attrs = { "class": "entry-title" }, ret="href")
            listItem.Url = Url[0]
            #Featured_List.append(listItem)
            #xbmc.log(listItem.Title)
            addDir(listItem.Title, listItem.Url, M_GET_VIDEO_LINKS, listItem.Image, '', '', listItem.Plot)
        
        nextPage = re.compile('class="next page-numbers" href="([^"]+)"').findall(contents)
        for url in nextPage:
            url = cleanHtml(url)
            addDir('Next', SITE + url, M_Search, next_thumb, '', '', '')
        # Other Menu Items
        bottom = [
                  (__settings__.getLocalizedString(30014), topics_thumb, M_Categories),
                  (__settings__.getLocalizedString(30015), search_thumb, M_Search)
                  ]
        for name, thumbnailImage, mode in bottom:
            addDir(name, '', mode, thumbnailImage, '', '', '')
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
        SetViewMode()

## Get Parameters
def get_params():
        param = []
        paramstring = sys.argv[2]
        if len(paramstring) >= 2:
                params = sys.argv[2]
                cleanedparams = params.replace('?', '')
                if (params[len(params) - 1] == '/'):
                        params = params[0:len(params) - 2]
                pairsofparams = cleanedparams.split('&')
                param = {}
                for i in range(len(pairsofparams)):
                        splitparams = {}
                        splitparams = pairsofparams[i].split('=')
                        if (len(splitparams)) == 2:
                                param[splitparams[0]] = splitparams[1]
        return param

def addDir(name, url, mode, thumbnail, genre, year, plot):
    ok = True
    isfolder = True   
    try:
        u = sys.argv[0] + "?url=" + urllib.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.quote_plus(name) #.encode('utf-8')
        if year == '':
            intYear = 0
        else:
            intYear = int(year)
        liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=thumbnail)
        liz.setInfo(type="Video", infoLabels={"Title":name, "Genre":genre, "Year":intYear, "Plot":plot})
        if mode == M_GET_VIDEO_LINKS:
            isfolder = False
            #liz.setProperty("IsPlayable", "true");
        ok = xbmcplugin.addDirectoryItem(handle=pluginhandle, url=u, listitem=liz, isFolder=isfolder)
    except:
        pass
    return ok

if not os.path.exists(settingsDir):
    os.mkdir(settingsDir)
if not os.path.exists(cacheDir):
    os.mkdir(cacheDir)
                    
params = get_params()
url = None
name = None
mode = None
titles = None
try:
        url = urllib.unquote_plus(params["url"])
except:
        pass
try:
        name = urllib.unquote_plus(params["name"])
except:
        pass
try:
        mode = int(params["mode"])
except:
        pass
try:
        titles = urllib.unquote_plus(params["titles"])
except:
        pass

xbmc.log( "Mode: " + str(mode) )
print "URL: " + str(url)
print "Name: " + str(name)
print "Title: " + str(titles)

if mode == None: #or url == None or len(url) < 1:
        #print "Top Directory"
        BuildMainDirectory()
elif mode == M_DO_NOTHING:
    print 'Doing Nothing'
elif mode == M_Categories:
    #print 'Categories'
    Categories()
elif mode == M_Browse:
    #print 'Browse'
    Browse(url)
elif mode == M_Search:
        #print "SEARCH  :" + url
        SEARCH(url)
elif mode == M_GET_VIDEO_LINKS:
    #print 'Trying to get the links and play it.'
    Playlist(url)
