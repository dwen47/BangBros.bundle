# BangBros-Content
import re
import random
import os
from datetime import datetime

VERSION_NO = '1.2018.01.01.1'
SEARCHURL = 'https://bangbros.com/search/' 
USER_AGENT = ''.join(['Mozilla/5.0 (Windows NT 6.1) ',
                      'AppleWebKit/537.36 (KHTML, like Gecko) ',
                      'Chrome/41.0.2228.0 ',
                      'Safari/537.36'])
REQUEST_DELAY = 9
NC17 ='NC-17'
StudioName = "BangBros"

XPATHS = {
    'search-titles': '//div[contains(@class,"echThumb")]//span[contains(@class,"thmb_ttl")]',
    'search-dates': '//div[contains(@class,"echThumb")]//span[contains(@class,"thmb_mr_2 ")]//span',
    'search-links': '//div[contains(@class,"echThumb")]//a[contains(@class,"thmb_lnk")]',
    'video-title': '//div[contains(@class,"ps-vdoHdd")]//h1',
    'video-actor': '//div[contains(@class,"vdoCast")]//a[contains(@href,"/model")]',
    'video-site': '//div[contains(@class,"vdoCast")]//a[contains(@href,"/websites/")]',
    'video-filename': '//div[contains(text(),"Release:")]',  #Release: bpov16428
    'video-description': '//div[contains(@class,"vdoDesc")]',
    'video-tags': '//div[contains(@class,"vdoTags")]//a[contains(@href,"/category")]',
    'video-images': '//img[contains(@src,"bangbros/big")]',
    'video-poster': '//video',
    'actor-image': '//div[contains(@class,"profilePic_in")]//img',
    'actor-name': '//div[contains(@class,"profileCont_hdd")]//h1'
}

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

class BangBrosAgent(Agent.Movies):
    name = 'BangBros'
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
        contentURL = SEARCHURL + medianame       

        try:
            Log('Searching with: ' + medianame)
            html = HTML.ElementFromURL(contentURL)
            titles = html.xpath(XPATHS['search-titles'])
            if len(titles)>0: 
                title = titles[0].text_content()
                if len(title)>0: 
                    title = title.split(" | ")[1].strip()                  
                    Log('Found: ' + title)
        except Exception, e:
            Log.Error('Error getting video info page:Error:[%s] ', e.message)

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
        contentURL = SEARCHURL + medianame
        metadata.tagline = contentURL

        # Get search result
        try:
            html = HTML.ElementFromURL(contentURL)
        except Exception, e:
            Log.Error('Error getting video info page:Error:[%s] ', e.message)
            return None
          
        # Get search link to video
        searchLinks = html.xpath(XPATHS['search-links'])
        if len(searchLinks)==0:
            Log.Error('Update: Title not found')
            return None
        else:
            searchLink = searchLinks[0]

        # Get search date - not in video info
        try:
            dates = html.xpath(XPATHS['search-dates'])
            if len(dates)==0:
                Log.Error('Update: release date not found')
            else:
                date = dates[0].text_content()
                curdate = Datetime.ParseDate(date).date()
                metadata.originally_available_at = curdate
                metadata.year = metadata.originally_available_at.year
                Log('Found Release Date: ' + str(curdate))
        except Exception, e:
            Log.Error('Error getting Release Date:[%s] ', e.message)

        # Get link to video info page
        contentURL = searchLink.get('href')
        if not contentURL.startswith('http'):                        
            contentURL = 'https://bangbros.com' + contentURL
        metadata.tagline = contentURL
        html = HTML.ElementFromURL(contentURL)

        # Get video info webpage
        try:
            html = HTML.ElementFromURL(contentURL)
        except Exception, e:
            Log.Error('Error getting video info page:Error:[%s] ', e.message)
            return None
 

        # Get Title
        try:
            html = HTML.ElementFromURL(contentURL)
            titles = html.xpath(XPATHS['video-title'])
            if len(titles)>0: 
                title = titles[0].text_content()
                if len(title)>0: 
                    title = title.split(" | ")[1].strip()                  
                    Log('Found Title: ' + title)
        except Exception, e:
            Log.Error('Error getting Title:[%s] ', e.message)

        self.clearCollections(metadata)

        # Get Summary.
        try:
            metadata.summary = ""
            metadata.summary = html.xpath(XPATHS['video-description'])[0].text_content()
            Log('Found Summary')
        except Exception, e:
            Log.Error('Error getting Summary:[%s] ', e.message)


        # Get artwork
        try:
            posterimgs = html.xpath(XPATHS['video-images'])
            if len(posterimgs)>0: 
                for posterimg in posterimgs:            
                    posterUrl = posterimg.get('src')
                    if len(posterUrl)>0:
                        if not posterUrl.startswith('http'):                        
                            posterUrl = 'https:' + posterUrl
                        self.addPosterArt(posterUrl,contentURL,metadata)
            posterimgs = html.xpath(XPATHS['video-poster'])
            if len(posterimgs)>0:            
                posterUrl = posterimgs[0].get('poster')
                if len(posterUrl)>0:
                    if not posterUrl.startswith('http'):                        
                        posterUrl = 'https:' + posterUrl
                    self.addPosterArt(posterUrl,contentURL,metadata) 
        except Exception, e:
            Log.Error('Error getting images:[%s] ', e.message)


        # Get Actors
        try:
            stars = html.xpath(XPATHS['search-actor-links'])
            if len(stars) > 0:
                for star in stars:
                    try:                      
                        starurl = star.get('href')
                        if not starurl.startswith('http'):                        
                            starurl = 'https://bangbros.com' + starurl
                        actorhtml = HTML.ElementFromURL(starurl)
                        starrnames = actorhtml.xpath(XPATHS['actor-name'])
                        if len(starrnames)>0:
                            starrname = starrnames[0].text_content().strip()
                            role = metadata.roles.new()
                            role.name = starrname
                            Log('Found Actor: ' + starrname)                                  
                            photoimages = actorhtml.xpath(XPATHS['actor-image'])
                            if len(photoimages) == 0:
                                photoimages = actorhtml.xpath(XPATHS['actor-image2'])
                            if len(photoimages) > 0 : 
                                starphotourl = photoimages[0].get('src0_1x')                                
                                if starphotourl is None:                         
                                    starphotourl = photoimages[0].get('src0') 
                                if starphotourl is None:    
                                    starphotourl = photoimages[0].get('src')                                          
                                if starphotourl is not None:             
                                    Log('Found Actor: ' + starrname + ' Photo Url : ' + str(starphotourl))
                                    role.photo = str(starphotourl)   

                    except Exception, e:
                        Log.Error('Error getting Actor Details:[%s] ', e.message)

        except Exception, e:
            Log.Error('Error getting Actors [%s] ', e.message)

        # Get Genres
        try:
            genres = html.xpath(XPATHS['search-tags'])
            if len(genres) > 0:
                for genreLink in genres:
                    genreName = genreLink.text_content().strip()
                    if len(genreName) > 0:
                        metadata.genres.add(genreName)
                Log('Found Genres: [' + str(len(metadata.genres)) + ']')                       
        except Exception, e:
                    Log.Error('Error getting Genres:[%s] ', e.message)


        # Collection
        try: 
            collink = html.xpath(XPATHS['search-site'])
            if len(collink)==0:
                collink = html.xpath(XPATHS['search-site2'])
            if len(collink)==0:
                collink = html.xpath(XPATHS['search-site3'])    
            collection = collink[0].text_content().replace('.com','').replace('Site:','').strip()          
            colmap = self.mapCOM2Collection(collection)            
            metadata.collections.add(colmap)      
            Log('Found Collection: ' + colmap)
        except:
            pass

        Log('Updated Meta Data:')
        self.logMediaMetaInfo(media, metadata)
        Log('End Update: ------------')


    def addPosterArt(self, url, refererurl, metadata):
        try:
            url = url.strip()
            refererurl = refererurl.strip()
            if url in metadata.posters.keys():
                Log('AddPosterArt():KeyExists[' + url + ']')
            imageproxy = Proxy.Media( HTTP.Request(url, headers={'Referer': refererurl}).content, sort_order = len(metadata.posters)+1 )
            metadata.posters[url] = imageproxy
            metadata.art[url] = imageproxy        
        except Exception, e:
            Log.Error('AddPosterArt():Error:[%s] ', e.message)


    def logMediaMetaInfo(self, media, metadata):
        Log('BangBros.Version : ' + VERSION_NO)
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

