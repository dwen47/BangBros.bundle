# RealityKings-Content
import re
import random
import os
import urllib
from datetime import datetime

DEBUGTHIS = False
VERSION_NO = '1.2018.01.01.1'
SEARCHURL = 'https://www.realitykings.com/tour/search/all/' 
USER_AGENT = ''.join(['Mozilla/5.0 (Windows NT 6.1) ', 'AppleWebKit/537.36 (KHTML, like Gecko) ', 'Chrome/41.0.2228.0 ', 'Safari/537.36'])
REQUEST_DELAY = 9
NC17 ='NC-17'
StudioName = "RealityKings"
WebsitePrefix = "https://www.realitykings.com"

xpathSearchVideoLinksFirstSingleText = '//p[@class="card-info__title"]//a[@title="{search}")]//@href'
xpathSearchVideoTitlesTextList = '//p[@class="card-info__title"]//a//text()'
xpathVideoTitleSingleText = '//h1[@class="section_title"][1]//text()'
xpathVideoSummarySingleText = '//div[@id="trailer-desc-txt"][1]//p[1]//text()'
xpathVideoActorLinks = '//div[@id="trailer-desc-txt"][1]//h2//a//@href' 
xpathVideoWebsiteSingleText = '//div[@id="trailer-desc-txt"][1]//h3[1]//text()'
#xpathVideoDateSingleText = '//span[contains(@class,"lc_info mas_description")][1]/text()' 		
xpathVideoArtworkLinksList = '//video//@data-bind'
xpathVideoPosterLinkSingleText = '//video//@poster'
#xpathVideoTagsList = '//p[@class="tags"]//a/text()'
xpathActorImageSrcSingleSingleText='//div[@class="model-picture-inner"]//img[@class="js-lazy"]//@src'
xpathActorNameSingleSingleText='//h1[@class="model-bio__name"][1]//text()'

SITETITLEREPLACEWITH = "-"
SITETITLEREPLACE = {
    " ": SITETITLEREPLACEWITH,
    ".": SITETITLEREPLACEWITH
}

COM2COLLECTION = {
    'com-folder-name': 'Collection name',
}


def Start():
    HTTP.CacheTime = 0
    HTTP.SetHeader('User-agent', USER_AGENT)


class AssylumAgent(Agent.Movies):
    
    name = 'RealityKings'
    languages = [Locale.Language.English]
    accepts_from = ['com.plexapp.agents.localmedia']
    primary_provider = True
    prev_search_provider = 0
    

    # PLUGIN: Search Function Entry Point
    def search(self, results, media, lang):
        
        Log('Search: ------------')
        self.logMediaMetaInfo(media, None)
        foldername = self.setFolderNamesFromMediaFilePath(media)
        medianame = self.cleanFolderName(foldername)
        contentURL = SEARCHURL;       

        contentURL = self.searchForVideo(foldername, None, contentURL)
        if contentURL is None:    
            Log('No Title Match - Video not found')
            return None
        else:
            
            # Get video info webpage
            try:
                html = HTML.ElementFromURL(contentURL)
            except Exception, e:
                Log.Error("Error getting video info page:Error: " + e.message)
                return None
 
            # Get Video Title from video info page 
            title = self.getXpathSingleText(html, xpathVideoTitleSingleText, '', 'Found Video Title: %s', None)
            
            results.Append( MetadataSearchResult(id=title, name=title, score='100', lang=lang) )
            Log('End Search: ------------')



    # PLUGIN: Update Function Entry Point
    def update(self, metadata, media, lang):   

        Log('Update: ------------')
        self.logMediaMetaInfo(media, metadata)
        foldername = self.setFolderNamesFromMediaFilePath(media)
        medianame = self.cleanFolderName(foldername)
        metadata.id = foldername
        metadata.title = foldername
        metadata.studio = StudioName
        metadata.content_rating = NC17

        clearyear = Datetime.ParseDate('1900-01-01').date()
        metadata.originally_available_at = clearyear
        metadata.year = 1900
        metadata.tagline = ""
        metadata.summary = ""
        self.clearCollections(metadata)

        contentURL = SEARCHURL + medianame;

        contentURL = self.searchForVideo(foldername, None, contentURL)

        if contentURL is None:    
            Log.Error('Video-Search: Result title not found')
            return None

        else:

            # Get video info webpage
            try:
                html = HTML.ElementFromURL(contentURL)
            except Exception, e:
                Log.Error("Error getting video info page:Error: " + e.message)
                return None
 
            # Get Video Title from video info page 
            metadata.title = self.getXpathSingleText(html, xpathVideoTitleSingleText, '', 'Found Video Title: %s', None)
            metadata.tagline = contentURL

            # Get Video Summary from video info page 
            metadata.summary = self.getXpathSingleText(html, xpathVideoSummarySingleText, "", "Found Video Summary", "Video Summary: %s")


            # Get Actors
            for starurl in self.getXpathTextList(html, xpathVideoActorLinks, "Found [%i] Video Actors", None):
                try:
                    if not starurl.startswith('http'):                        
                        starurl = WebsitePrefix + starurl
                    actorhtml = HTML.ElementFromURL(starurl)
                    starrname = self.getXpathSingleText(actorhtml, xpathActorNameSingleSingleText, None, "Found Actor: %s", None)
                    if starrname is not None:
                        role = metadata.roles.new()
                        role.name = starrname
                        starphotourl = self.getXpathSingleText(actorhtml, xpathActorImageSrcSingleSingleText, None, "Found Actor Photo Url: %s", None)
                        if starphotourl is not None:
                            if not starphotourl.startswith("http"):                        
                                starphotourl = WebsitePrefix + starphotourl
                            role.photo = starphotourl 
                except Exception, e:
                    Log.Error("Error getting Actor Details: " + e.message)

            #videoPosterSrc:{src: 'https://photo-ec.realitykingscontent.com/rk/bignaturals/faces/brookewylde3-screencap.jpg', 
            #srcFallback: 'https://photo-ec.realitykingscontent.com/rk/bignaturals/faces/brookewylde3.pick0.jpg'}
            # Get Video Artwork
            posters = self.getXpathSingleText(html, xpathVideoArtworkLinksList, None, None)
            if posters is not None:
                artUrl = posters.split("'")[3]
                Log("Found Video Artwork: " + artUrl)
                self.addArt(artUrl, contentURL, metadata)

            # Get Video Poster      
            posterUrl = self.getXpathSingleText(html, xpathVideoPosterLinkSingleText, None, None, None)
            if posterUrl is not None:
                posterUrl=posterUrl.strip().split("'")[1]
                self.addPoster(posterUrl, contentURL, metadata) 

            # Get Genres               
            #for genreName in self.getXpathTextList(html, xpathVideoTagsList, "Found [%i] Video Genres", None):
            #    metadata.genres.add(genreName)
   
            # Add Website to Collection
            websitename = self.getXpathSingleText(html, xpathVideoWebsiteSingleText, None, 'Found Website Name: %s', None)
            if websitename is not None:                               
                metadata.collections.add(websitename)                     
            metadata.collections.add(StudioName)

            Log('Updated Meta Data:')
            self.logMediaMetaInfo(media, metadata)
            Log('End Update: ------------')



    def searchForVideo(self, findtitle, metadata, contentURL):
    
        Log('Finding: ' + findtitle + ' with ' + contentURL)

        # Get search result
        try:
            html = HTML.ElementFromURL(contentURL)
        except Exception, e:
            Log.Error("Error getting video info page:Error: " + e.message)
            return None

        # Get titles on page X
        titles = self.getXpathTextList(html, xpathSearchVideoTitlesTextList, None, None)
        foundtitle=None
        if titles is None:
            return None
        if len(titles)==0:
            return None
        for title in titles:
            if title.replace(":","").replace('"','').replace('.','').lower()==findtitle.replace('.','').lower():
                foundtitle = title

        if foundtitle is None:  
            return None
            # parts = contentURL.split('&p=')
            # page = int(parts[1]) + 1
            # netlink = parts[0] + '&p=' + str(page)
            # return self.searchForVideo(findtitle, metadata, netlink)
        else:   
            foundtitle = foundtitle.replace('"','')
            contentURL = self.getXpathSingleText(html, xpathSearchVideoLinksFirstSingleText.format(search=foundtitle), None, 'Video-Search-VideoInfoLink-Found: %s', None)
            if contentURL.startswith('.'):
                contentURL = contentURL.replace('.',WebsitePrefix)
            Log("Video Info Url: " + contentURL)
            if metadata is not None:                 
                metadata.title = title
                metadata.tagline = contentURL
            return contentURL

    def getXpathElementList(self, html, xpath, logmsg, debugmsg):
        result = []
        narray = html.xpath(xpath)    
        if len(narray)>0:
            for item in narray:
                result.append(item)
        self.logit(logmsg, debugmsg, len(result))
        return result

    def getXpathTextList(self, html, xpath, logmsg, debugmsg):
        result = []
        narray = html.xpath(xpath)    
        if len(narray)>0:
            for item in narray:
                result.append(item.strip())
        self.logit(logmsg, debugmsg, len(result))
        return result

    def getXpathSingleText(self, html, xpath, nullvalue, logmsg, debugmsg):
        #Log("getXpathSingleText-XAPTH: " + xpath)
        result = nullvalue
        narray = html.xpath(xpath)    
        if len(narray)>0:
            result = narray[0].strip()      
        self.logit(logmsg, debugmsg, result)
        return result
        
    def logit(self, msg, debugmsg, value):
        if msg is not None:
            if "%" in msg:
                Log(msg, value)
            else:
                Log(msg)
        if DEBUGTHIS==True and debugmsg is not None:
            if "%" in debugmsg:
                Log(debugmsg, value)
            else:
                Log(debugmsg)


    def addPoster(self, url, refererurl, metadata):
        try:
            url = url.strip()
            refererurl = refererurl.strip()
            if url in metadata.posters.keys():
                Log('AddPoster():KeyExists[' + url + ']')
            imageproxy = Proxy.Media( HTTP.Request(url, headers={'Referer': refererurl}).content, sort_order = len(metadata.posters)+1 )
            metadata.posters[url] = imageproxy   
        except Exception, e:
            Log("AddPoster():Error: " + e.message)

    def addArt(self, url, refererurl, metadata):
        try:
            url = url.strip()
            refererurl = refererurl.strip()
            if url in metadata.posters.keys():
                Log('AddArt():KeyExists[' + url + ']')
            imageproxy = Proxy.Media( HTTP.Request(url, headers={'Referer': refererurl}).content, sort_order = len(metadata.art)+1 )
            metadata.art[url] = imageproxy        
        except Exception, e:
            Log("AddArt():Error: " + e.message)


    def logMediaMetaInfo(self, media, metadata):
        Log('Assylum.Version : ' + VERSION_NO)
        Log('Media.Id: ' + str(media.id))
        Log('Media.Title: ' + str(media.title))
        if metadata is not None:
            Log('MetaData.Title: ' + str(metadata.title))
            Log('MetaData.ID: ' + str(metadata.id))
            Log('MetaData.Release Date: ' + str(metadata.originally_available_at))
            Log('MetaData.Year: ' + str(metadata.year))
            Log('MetaData.TagLine: ' + str(metadata.tagline))
            Log('MetaData.Studio: ' + str(metadata.studio))
            Log('MetaData.Geres: [' + str(len(metadata.genres)) + ']')
            for x in range(len(metadata.collections)):
                Log('MetaData.Collection: ' + metadata.collections[x])
            for x in range(len(metadata.roles)):
                Log('MetaData.Starring: ' + metadata.roles[x].name)
            for key in metadata.posters.keys():
                Log('MetaData.PosterURL: ' + key)
            for key in metadata.art.keys():
                Log('MetaData.ArtURL: ' + key)

    def clearCollections(self, metadata):
        for key in metadata.posters.keys():
            del metadata.posters[key]
        for key in metadata.art.keys():
            del metadata.art[key]
        metadata.genres.clear()
        metadata.collections.clear()
        metadata.roles.clear()

    def setFolderNamesFromMediaFilePath(self, media):
        MediaPart = media.items[0].parts[0]
        ThisFilePath = MediaPart.file
        ThisFolderPath = os.path.dirname(ThisFilePath)
        ThisFolderName = os.path.basename(ThisFolderPath)
        ThisFolderName = ThisFolderName.split(" D18 ")[0].strip()
        Log('Media folder: ' + ThisFolderName)
        ParentFolderPath = os.path.dirname(ThisFolderPath) 
        ParentFolderName = os.path.basename(ParentFolderPath)
        Log('Media parent folder: ' + ParentFolderName)
        return ThisFolderName

    def cleanFolderName(self, foldername):
        foldername = foldername.split(" D18 ")[0].strip()
        for key in SITETITLEREPLACE:
            foldername = foldername.replace(key,SITETITLEREPLACE[key])      
        return foldername

    def mapCOM2Collection(self, comname):
        comname = comname.lower()
        for key in COM2COLLECTION:
            if key.lower()==comname:
                Log('Site maps to collection: ' + COM2COLLECTION[key])
                return COM2COLLECTION[key]
        return '-No COM2COL Map-'

