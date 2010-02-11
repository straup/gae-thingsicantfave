# http://code.google.com/appengine/docs/python/taskqueue/overview.html

from config import config

import things
import things.Faves
import base64
import urllib
import urllib2
import logging

logging.basicConfig(level=logging.DEBUG)

class Tweet (things.Request):

    def get(self):

        if not config['twitter_notify']:
            self.response.out.write('FAIL')
            return

        fave_id = self.request.get('fave_id')
        key = fave_id.replace("fave_", "")

        try:
            fave = things.Faves.fetch_by_key(key)
        except Exception, e:
            logging.warning('bogus fave ID: %s' % key)

            self.response.out.write('FAIL')
            return

        self.prepare_fave(fave)

        fave_url = fave.url

        msg = "#%s faved a %s by #%s" % (fave.creator, fave.category_singular, fave.owner)

        if config['twitter_shorten_urls']:

            # some day Flickr will have a generic URL shortener...

            try:
                data = urllib.urlencode({'url' : fave_url})
                req = urllib2.Request('http://bit.ly/api', data)
                res = urllib2.urlopen(req)
                short_url = res.read()

                if short_url != '':
                    fave_url = short_url

            except Exception, e:
                logging.warning("failed to retrieve bitly URL for %s: %s" % (fave_url, e))

        msg += ": %s" % fave_url

        url = 'http://twitter.com/statuses/update.json'
        data = {'status': msg}

        user = config['twitter_username']
        pswd = config['twitter_password']

        auth = base64.encodestring('%s:%s' % (user, pswd))[:-1]
        headers = {'Authorization' : 'Basic %s' % auth }

        try:
            data = urllib.urlencode({"status" : msg})
            req = urllib2.Request(url, data, headers)
            res = urllib2.urlopen(req)
        except Exception, e:
            logging.error('failed to tweet: %s' % e)

            self.response.out.write('FAIL')
            return

        logging.info(msg)

        self.response.out.write('OK')
        return

