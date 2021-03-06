# -*- coding: utf-8 -*-
import re
import PAsearchSites
import re
import PAgenres
import PAutils


def search(results, encodedTitle, searchTitle, siteNum, lang, searchDate):
    sceneID = None
    splited = searchTitle.split(' ')
    if unicode(splited[0], 'utf8').isdigit():
        sceneID = splited[0]
        searchTitle = searchTitle.replace(sceneID, '', 1).strip()
        req = PAutils.HTTPRequest(PAsearchSites.getSearchBaseURL(siteNum) + '/vrpornvideo/' + sceneID)
        searchResults = HTML.ElementFromString(req.text)
        titleNoFormatting = searchResults.xpath('//h1[contains(@class, "video-title")]')[0].text_content()
        curID = PAutils.Encode(PAsearchSites.getSearchBaseURL(siteNum) + '/vrpornvideo/' + sceneID)
        girlName = ''

        releaseDate = ''
        date = searchResults.xpath('//p[@itemprop="uploadDate"]/@content')
        if date:
            releaseDate = parse(date[0]).strftime('%Y-%m-%d')

        score = 100
        results.Append(MetadataSearchResult(id='%s|%d' % (curID, siteNum), name='[%s] %s in %s %s' % (PAsearchSites.getSearchSiteName(siteNum), girlName, titleNoFormatting, releaseDate), score=score, lang=lang))
    else:
        req = PAutils.HTTPRequest(PAsearchSites.getSearchSearchURL(siteNum) + encodedTitle)
        searchResults = HTML.ElementFromString(req.text)
        for searchResult in searchResults.xpath('//div[@class="tile-grid-item"]'):
            data = searchResult.xpath('.//a[contains(@class, "video-card-title")]')[0]
            titleNoFormatting = searchResult.xpath('.//a[contains(@class, "video-card-title")]/@title')[0]
            curID = PAutils.Encode(searchResult.xpath('.//a[contains(@class, "video-card-title")]/@href')[0])
            releaseDate = ''
            date = searchResult.xpath('.//span[@class="video-card-upload-date"]/@content')
            if date:
                releaseDate = parse(date[0]).strftime('%Y-%m-%d')
            girlName = searchResult.xpath('.//a[@class="video-card-link"]')[0].text_content()
            if searchDate and releaseDate:
                score = 100 - Util.LevenshteinDistance(searchDate, releaseDate)
            else:
                score = 100 - Util.LevenshteinDistance(searchTitle.lower(), titleNoFormatting.lower())
            results.Append(MetadataSearchResult(id='%s|%d' % (curID, siteNum), name='[%s] %s in %s %s' % (PAsearchSites.getSearchSiteName(siteNum), girlName, titleNoFormatting, releaseDate), score=score, lang=lang))

    return results


def update(metadata, siteID, movieGenres, movieActors):
    metadata_id = str(metadata.id).split('|')
    sceneURL = PAutils.Decode(metadata_id[0])
    if not sceneURL.startswith('http'):
        sceneURL = PAsearchSites.getSearchBaseURL(siteID) + sceneURL
    req = PAutils.HTTPRequest(sceneURL)
    detailsPageElements = HTML.ElementFromString(req.text)

    # Title
    metadata.title = detailsPageElements.xpath('//div[@class="video-rating-and-details"]/h1')[0].text_content()

    # Summary
    metadata.summary = detailsPageElements.xpath('//p[@class="video-description"]')[0].text_content().strip()

    # Studio
    metadata.studio = 'Badoink VR'

    # Tagline and Collection
    metadata.collections.clear()
    tagline = PAsearchSites.getSearchSiteName(siteID)
    metadata.tagline = tagline
    metadata.collections.add(tagline)

    # Release Date
    sceneDate = detailsPageElements.xpath('//p[@itemprop="uploadDate"]/@content')
    if sceneDate:
        date_object = parse(sceneDate[0])
        metadata.originally_available_at = date_object
        metadata.year = metadata.originally_available_at.year

    # Genres
    movieGenres.clearGenres()
    resolution = ''
    degree = ''
    for tag in detailsPageElements.xpath('//img[@class="video-format-image"]'):
        text = tag.get('alt')
        if 'K' in text:
            resolution = text
        if '°' in text:
            degree = text
    movieGenres.addGenre(resolution)
    movieGenres.addGenre(degree)
    for genreLink in detailsPageElements.xpath('//a[@class="video-tag"]'):
        genreName = genreLink.text_content().strip()

        movieGenres.addGenre(genreName)

    # Actors
    movieActors.clearActors()
    for actorLink in detailsPageElements.xpath('//a[contains(@class,"video-actor-link")]'):
        actorName = actorLink.text_content().strip()

        actorPageURL = PAsearchSites.getSearchBaseURL(siteID) + actorLink.get('href')
        req = PAutils.HTTPRequest(actorPageURL)
        actorPage = HTML.ElementFromString(req.text)
        actorPhotoURL = actorPage.xpath('//img[@class="girl-details-photo"]/@src')[0].split('?')[0]

        movieActors.addActor(actorName, actorPhotoURL)

    # Posters
    art = []
    xpaths = [
        '//div[contains(@class,"gallery-item")]/@data-big-image',
        '//img[@class="video-image"]/@src'
    ]

    try:
        posterUrl = detailsPageElements.xpath('//img[@class="video-image"]/@src')[0].split('?')[0]
        Log('Background: ' + posterUrl)
        metadata.art[posterUrl] = Proxy.Media(
            HTTP.Request(posterUrl, headers={'Referer': 'http://www.google.com'}).content, sort_order=1)
    except:
        pass

    refUrl = detailsPageElements.xpath('//div[contains(@class,"gallery-item")]/@data-big-image')[1].split('?')[0]
    refUrl = re.sub('[0-9].jpg', '', refUrl)
    Log('posterUrl: ' + posterUrl)
    try:
        for idx in range(1, 100):
            posterUrl = refUrl + str(idx) + '.jpg'
            Log('posterUrl: ' + posterUrl)
            image = PAutils.HTTPRequest(posterUrl, headers={'Referer': 'http://www.google.com'})
            im = StringIO(image.content)
            resized_image = Image.open(im)
            width, height = resized_image.size
            # Add the image proxy items to the collection
            if height > width:
                # Item is a poster
                metadata.posters[posterUrl] = Proxy.Media(image.content, sort_order=idx+1)
            else:
                # Item is an art item
                metadata.art[posterUrl] = Proxy.Media(image.content, sort_order=idx+1)
    except:
        pass

    return metadata
