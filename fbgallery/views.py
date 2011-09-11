import urllib2, urllib
import django.utils.simplejson as json
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext, defaultfilters
from django.http import HttpResponse, Http404
from django.core.cache import cache
 
from django.conf import settings

fql_url = 'https://api.facebook.com/method/fql.query'
cache_expires = getattr(settings, 'CACHE_EXPIRES', 30)

def get_fql_result(fql):
    cachename = 'fbgallery_cache_' + defaultfilters.slugify(fql)
    data = None
    if cache_expires > 0:
        data = cache.get(cachename)
    if data == None: 
        options ={
            'query':fql,
            'format':'json',
        }
        f = urllib2.urlopen(urllib2.Request(fql_url, urllib.urlencode(options)))
        response = f.read()
        f.close()
        data = json.loads(response)
        if cache_expires > 0:
            cache.set(cachename, data, cache_expires*60)
    return data
    
def display_albums(request, fb_id):
    """ Fetch all facebook albums for specified id """

    fql = "select aid, cover_pid, name from album where owner=%s" % fb_id;
    albums = get_fql_result(fql)
    for i in range(len(albums)):
        fql = "select src from photo where pid = '%s'" % albums[i]['cover_pid'];
        [item for sublist in get_fql_result(fql) for item in sublist]
        albums[i]['src'] = sublist['src']
          
    data = RequestContext(request, {
        'albums':albums,
        })
    
    return render_to_response('fbgallery/albums.html', context_instance=data)
    
    
def display_album(request,album_id,fb_id):
    """ Display a facebook album, first check that the album id belongs to the page id specified """
    fql = "select aid, name from album where owner=%s and aid='%s'" % (fb_id, album_id)
    valid_album = get_fql_result(fql)
    if valid_album:
        fql = "select pid, src, src_small, src_big, caption from photo where aid = '%s'  order by created desc" % album_id
        album = get_fql_result(fql)
        [item for album_detail in valid_album for item in album_detail]       
    else:
        raise Http404
    
    data = RequestContext(request, {
        'album':album,
        'album_detail':album_detail,
        })
    return render_to_response('fbgallery/album.html', context_instance=data)


