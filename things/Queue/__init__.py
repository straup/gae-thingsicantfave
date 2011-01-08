# http://code.google.com/appengine/docs/python/taskqueue/overview.html

from config import config

import things
import things.Faves
import logging

import time
import httplib
import httplib2
import oauth2

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

        creator = fave.creator.encode('ascii', 'replace')
        category = fave.category_singular.encode('ascii', 'replace')
        owner = fave.owner.encode('ascii', 'replace')
        owner = owner.replace(" ", "")
        owner = owner.lower()

        msg = "#%s faved a %s by #%s" % (creator, category, owner)

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

        try:
            rsp = self.send_tweet(msg)
            self.response.out.write(rsp)

        except Exception, e:
            logging.error('failed to post tweet (%s) : %s' % (msg, e))
            self.response.out.write(e)

        return

    def send_tweet(self, msg):

        host = 'api.twitter.com'
        endpoint = '/1/statuses/update.json'

        url = 'http://' + host + endpoint

        token = oauth2.Token(key=config['twitter_access_token'], secret=config['twitter_access_secret'])
        consumer = oauth2.Consumer(key=config['twitter_consumer_token'], secret=config['twitter_consumer_secret'])

        params = {
            'status' : msg,
            'oauth_token' : token.key,
            'oauth_consumer_key' : consumer.key,
            'oauth_nonce' : oauth2.generate_nonce(),
            'oauth_timestamp' :int(time.time()),
            }

        req = oauth2.Request(method="POST", url=url, parameters=params)

        signature_method = oauth2.SignatureMethod_HMAC_SHA1()
        req.sign_request(signature_method, consumer, token)

        body = req.to_postdata()

        conn = httplib.HTTPConnection('api.twitter.com')
        conn.request('POST', '/1/statuses/update.json', body)

        rsp = conn.getresponse()
        return rsp.status
