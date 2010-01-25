from FlickrApp.Handlers import FlickrAppRequest
from config import config

from google.appengine.api import memcache
from django.utils import simplejson
import urllib
import urllib2
import urlparse
import re

re_comment = re.compile(r'comment\d+')

class Request (FlickrAppRequest) :

    def __init__ (self) :
        FlickrAppRequest.__init__(self, config)

    def check_logged_in (self, min_perms) :

        if not FlickrAppRequest.check_logged_in(self, min_perms) :
            return False

        return True

    def is_flickr_url(self, url):

        try:
            obj = urlparse.urlparse(url)
        except Exception, e:
            return False

        valid_hosts = ('flickr.com', 'www.flickr.com')

        if not obj.hostname in valid_hosts:
            return False

        return True

    def parse_url(self, url):

        if url.endswith("/"):
            url = url[:-1]

        try:
            obj = urlparse.urlparse(url)
        except Exception, e:
            return None

        valid_hosts = ('flickr.com', 'www.flickr.com')

        if not obj.hostname in valid_hosts:
            return None

        if obj.hostname == 'flickr.com':
            url = url.replace('flickr.com', 'www.flickr.com')

        path = obj.path

        if path.startswith("/"):
            path = path[1:]

        parts = path.split("/")

        if len(parts) < 4:
            return None

        if parts[0] != 'photos':
            return None

        try:
            owner = self.find_user(parts[1])
        except Exception, e:
            return None

        if not owner:
            return None

        """
        if owner['user']['id'] == self.user.nsid:
            return None
        """

        buckets = ('galleries', 'sets', 'collections')

        if parts[2] in buckets:

            # http://www.flickr.com/photos/straup/galleries/72157622732572228/#comment72157623019473750
            # also, sets...

            return {
                'url' : url,
                'owner_nsid' : owner['user']['id'],
                'category' : parts[2],
                }

        if re_comment.match(parts[3]):

            data = {
                'url' : url,
                'owner_nsid' : owner['user']['id'],
                'category' : 'comments',
                }

            try:
                method = 'flickr.photos.comments.getList'
                args = { 'photo_id' : parts[2] }

                rsp = self.proxy_api_call(method, args, 86400)

                for c in rsp['comments']['comment']:
                    if c['permalink'].endswith(parts[3]):
                        data['commentor_nsid'] = c['author']

            except Exception, e:
                pass

            return data

        return None

    def prepare_faves(self, faves):

        for f in faves:

            if f.category == 'comments':
                f.category_singular = 'comment'
            elif f.category == 'galleries':
                f.category_singular = 'gallery'
            elif f.category == 'sets':
                f.category_singular = 'set'
            elif f.category == 'collections':
                f.category_singular = 'collection'

            if self.user and self.user.nsid == f.creator_nsid:
                f.creator = 'You'
            else:
                creator = self.flickr_get_user_info(f.creator_nsid)
                f.creator = creator['username']['_content']

            if self.user and self.user.nsid == f.owner_nsid:
                f.owner = 'You'
            else:
                owner = self.flickr_get_user_info(f.owner_nsid)
                f.owner = owner['username']['_content']

            if f.commentor_nsid:

                if self.user and self.user.nsid == f.commentor_nsid:
                    f.commentor = 'You'
                else:
                    commentor = self.flickr_get_user_info(f.commentor_nsid)
                    f.commentor = commentor['username']['_content']

    def find_user(self, name):

        memkey = "%s_%s" % ('flickr.urls.lookupUser', name)
        cache = memcache.get(memkey)

        if cache :
            return cache

        # this a hack to account for the fact that Flickr.API
        # doesn't seem to play nicely with methods that have
        # a 'url' arguments. Specifically, the urllib* libraries
        # think that's what they need to fetch...

        url = 'http://www.flickr.com/photos/%s' % name

        # FIX ME

        enc_url = url
        enc_apikey = config['flickr_apikey']

        req = 'http://api.flickr.com/services/rest/?method=flickr.urls.lookupUser&api_key=%s&url=%s&format=json&nojsoncallback=1' % (enc_apikey, enc_url)

        try:
            res = urllib2.urlopen(req)
            json = simplejson.loads(res.read())
        except Exception, e:
            return None

        if json['stat'] != 'ok':
            return None

        memcache.add(memkey, json, 1209600)
        return json
