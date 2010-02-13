from FlickrApp.Handlers import FlickrAppRequest
from config import config

import urlparse
import re

re_comment = re.compile(r'comment\d+')
re_nsid = re.compile(r'\d+@N\d+')

import logging
logging.basicConfig(level=logging.INFO)

class ParseURLException (Exception) :
  def __init__(self, value):
    self.value = value

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
            logging.warning('Failed to parse URL %s: %s' % (url, e))
            raise ParseURLException, 'url'

        valid_hosts = ('flickr.com', 'www.flickr.com')

        if not obj.hostname in valid_hosts:
            logging.warning('Invalid URL %s' % url)
            raise ParseURLException, 'invalid'

        if obj.hostname == 'flickr.com':
            url = url.replace('flickr.com', 'www.flickr.com')

        path = obj.path

        if path.startswith("/"):
            path = path[1:]

        parts = path.split("/")

        if not parts[0] in ('photos', 'groups', 'people') :
            raise ParseURLException, 'other'

        if parts[0] == 'photos' and len(parts) == 2:
          parts[0] = 'people'

        # groups

        if parts[0] == 'groups':

          try:
            method = 'flickr.urls.lookupGroup'
            args = { 'url' : url }
            rsp = self.api_call(method, args)
          except Exception, e:
            raise ParseURLException, 'group'

          if rsp['stat'] != 'ok':
            raise ParseURLException, 'group'

          name = rsp['group']['groupname']['_content']

          """
          try:
            method = 'flickr.groups.members.getList'
            args = { 'group_id' : rsp['group']['id'], 'membertypes' : 4 }
            rsp = self.proxy_api_call(method, args, 600)
          except Exception, e:
            raise ParseURLException, 'group_noinfo'
          """

          # HOW TO: ensure group owner is not self.user.nsid

          return {
            'url' : 'http://www.flickr.com/groups/%s' % rsp['group']['id'],
            'category' : 'groups',
            'owner_nsid' : rsp['group']['id'],
            }

        # people

        elif parts[0] == 'people':

          try:
            method = 'flickr.urls.lookupUser'
            args = { 'url' : url }
            rsp = self.api_call(method, args)
          except Exception, e:
            raise ParseURLException, 'user'

          if rsp['stat'] != 'ok':
            raise ParseURLException, 'user'

          if rsp['user']['id'] == self.user.nsid:
            raise ParseURLException, 'user_same'

          return {
            'url' : 'http://www.flickr.com/people/%s' % rsp['user']['id'],
            'category' : 'people',
            'owner_nsid' : rsp['user']['id'],
            }

        # photos

        else:
          try:
            owner = self.find_user(parts[1])
          except Exception, e:
            logging.error('Failed to retrieve user %s: %s' % (parts[1], e))
            raise ParseURLException, 'owner'

          if not owner:
            logging.error('Unknown user %s' % parts[1])
            raise ParseURLException, 'owner_unknown'

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

          comment_id = None

          if re_comment.match(parts[3]):
            comment_id = parts[3]
          elif re_comment.match(obj.fragment):
            comment_id = obj.fragment
          else:
            pass

          if comment_id:

            data = {
              'url' : url,
              'owner_nsid' : owner['user']['id'],
              'category' : 'comments',
              }

            try:
              method = 'flickr.photos.comments.getList'
              args = { 'photo_id' : parts[2] }
              # rsp = self.proxy_api_call(method, args, 300)
              rsp = self.api_call(method, args)

              for c in rsp['comments']['comment']:
                if c['permalink'].endswith(comment_id):
                  data['commentor_nsid'] = c['author']

            except Exception, e:
              logging.warning('Failed to retrieve comment owner for %s' % parts[2])
              raise ParseURLException, 'comment'

            return data

          raise ParseURLException, 'other'

    def prepare_faves(self, faves):

        for f in faves:
            self.prepare_fave(f)

    def prepare_fave(self, f):

        if f.category == 'comments':
            f.category_singular = 'comment'
        elif f.category == 'galleries':
            f.category_singular = 'gallery'
        elif f.category == 'sets':
            f.category_singular = 'set'
        elif f.category == 'collections':
            f.category_singular = 'collection'
        elif f.category == 'people':
            f.category_singular = 'person'
        elif f.category == 'groups':
            f.category_singular = 'group'

        if f.category == 'groups':

          try:
            method = 'flickr.groups.getInfo'
            args = { 'group_id' : f.owner_nsid }
            rsp = self.proxy_api_call(method, args, 600)

            f.owner = rsp['group']['name']['_content']
          except Exception, e:
            f.owner = 'something'

          if self.user and self.user.nsid == f.creator_nsid:
            f.creator = 'You'
          else:
            try:
              creator = self.flickr_get_user_info(f.creator_nsid)
              f.creator = creator['username']['_content']
            except Exception, e:
              f.creator = 'Someone'

        else:

          if self.user and self.user.nsid == f.creator_nsid:
            f.creator = 'You'
          else:
            try:
              creator = self.flickr_get_user_info(f.creator_nsid)
              f.creator = creator['username']['_content']
            except Exception, e:
              f.creator = 'someone'

          if self.user and self.user.nsid == f.owner_nsid:
            f.owner = 'You'
          else:
            try:
              owner = self.flickr_get_user_info(f.owner_nsid)
              f.owner = owner['username']['_content']
            except Exception, e:
              f.owner = 'someone'

          if f.commentor_nsid:

            if self.user and self.user.nsid == f.commentor_nsid:
              f.commentor = 'You'
            else:
              try:
                commentor = self.flickr_get_user_info(f.commentor_nsid)
                f.commentor = commentor['username']['_content']
              except Exception, e:
                f.commentor = 'someone'

    def is_nsid(self, str):

        if re_nsid.match(str):
            return True

        return False

    def find_user(self, name):

        method = 'flickr.urls.lookupUser'
        args = { 'url' : 'http://www.flickr.com/photos/%s' % name }

        json = self.proxy_api_call(method, args, 1209600)
        return json
