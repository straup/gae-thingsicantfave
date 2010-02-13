from config import config

import things
import things.Faves

import urllib

import logging
logging.basicConfig(level=logging.INFO)

class Main (things.Request):

    def get(self):

        url = self.request.get('url')

        if not self.check_logged_in(self.min_perms) :

            # fix me: crumb breaks during this flow

            """
            if url:
                redir = '/?url=%s' % urllib.quote(url)
                self.do_flickr_auth(self.min_perms, redir)
                return
            """

            self.display("main_logged_out.html")
            return

        if url and self.is_flickr_url(url):
            self.assign('url', url)

        fave_crumb = self.generate_crumb(self.user, 'method=fave')
        self.assign('fave_crumb', fave_crumb)

        self.display("main_logged_in.html")
        return

    def post(self):

        if not self.check_logged_in(self.min_perms) :
            self.display("main_logged_out.html")
            return

        fave_crumb = self.generate_crumb(self.user, 'method=fave')
        self.assign('fave_crumb', fave_crumb)

        if not self.request.get('url'):
            self.assign('error', 'no_url')
            self.display('main_logged_in.html')
            return

        if not self.validate_crumb(self.user, 'method=fave', self.request.get('crumb')) :
            self.assign('error', 'invalid_crumb')
            self.display('main_logged_in.html')
            return

        try:
            thing = self.parse_url(self.request.get('url'))
        except things.ParseURLException, e:
            self.assign('error', 'cannot_parse')
            self.assign('parse_error', e.value)
            self.display('main_logged_in.html')
            return
        except Exception, e:
            self.assign('error', 'cannot_parse')
            self.assign('parse_error', 'unknown')
            self.display('main_logged_in.html')
            return

        if thing['category'] == 'comments':
            if thing['commentor_nsid'] == self.user.nsid:
                self.assign('error', 'is_own')
                self.display('main_logged_in.html')
                return
        elif thing['owner_nsid'] == self.user.nsid:
            self.assign('error', 'is_own')
            self.display('main_logged_in.html')
            return
        else:
            pass

        if things.Faves.has_faved(self.user.nsid, thing['url']):
            self.assign('error', 'already_faved')
            self.display('main_logged_in.html')
            return

        try:
            thing['creator_nsid'] = self.user.nsid
            fave = things.Faves.fave_thing(thing)
        except Exception, e:
            logging.error('failed to add %s : %s' % (thing['url'], e))

            self.assign('error', 'cannot_add')
            self.display('main_logged_in.html')
            return

        if config['twitter_notify']:

            try:
                from google.appengine.api.labs import taskqueue

                fave_key = str(fave.key())
                fave_id = 'fave_%s' % fave_key

                task_url = '/queue/tweet?fave_id=%s' % fave_id
                taskqueue.add(url=task_url, method='GET')

                logging.debug('Registed tweet task for key: %s' % fave_id)

            except Exception, e:
                logging.error('Failed to schedule tweet: %s' % e)

        self.assign('faved', True)
        self.assign('fave', fave)

        self.display('main_logged_in.html')
        return

class RecentFaves(things.Request):

    def get(self, who=None, what=None):

        self.check_logged_in(self.min_perms)

        faves = things.Faves.recently_faved()
        faves = faves.fetch(20)

        self.prepare_faves(faves)

        self.assign("rss_feed", "http://thingsicantfave.appspot.com/rss/faves")

        if self.user:
            delete_crumb = self.generate_crumb(self.user, 'method=delete')
            self.assign('delete_crumb', delete_crumb)

        self.assign('faves', faves)
        self.display('recently_faved.html')
        return

class FavedBy(things.Request):

    def get(self, who=None, what=None):

        self.check_logged_in(self.min_perms)
        creator_nsid = None

        if who:
            who = urllib.unquote(who)

        if what:
            what = urllib.unquote(what)

        if who == 'me':

            if not self.check_logged_in(self.min_perms) :
                self.redirect('/faves')
                return

            creator_nsid = self.user.nsid

        else:

            if self.is_nsid(who):
                creator_nsid = who
            else:
                creator = self.find_user(who)
                logging.info("%s: %s" % (who, creator))
                creator_nsid = creator['user']['id']

        faves = things.Faves.faves_for_creator(creator_nsid, what)
        self.assign("count_faves", faves.count())

        faves = faves.fetch(100)
        self.prepare_faves(faves)

        if self.user and creator_nsid == self.user.nsid:
            self.assign('who', 'You')

            delete_crumb = self.generate_crumb(self.user, 'method=delete')
            self.assign('delete_crumb', delete_crumb)

        else:
            user = self.flickr_get_user_info(creator_nsid)
            self.assign('who', user['username']['_content'])

        self.assign('what', what)

        rss_feed = "http://thingsicantfave.appspot.com/rss/faves/%s" % creator_nsid

        if what:
            rss_feed += "/%s" % what

        self.assign("who_nsid", creator_nsid)
        self.assign("rss_feed", rss_feed)

        self.assign('faves', faves)
        self.display('faved_by.html')
        return

class Faved(things.Request):

    def get(self, who=None, what=None):

        self.check_logged_in(self.min_perms)
        owner_nsid = None

        if who:
            who = urllib.unquote(who)

        if what:
            what = urllib.unquote(what)

        is_commentor = False

        if what == 'comments':
            is_commentor = True

        if who == 'me':

            if not self.check_logged_in(self.min_perms) :
                self.redirect('/faves')
                return

            owner_nsid = self.user.nsid

        else:

            if self.is_nsid(who):
                owner_nsid = who
            else:
                creator = self.find_user(who)
                logging.info("%s: %s" % (who, creator))
                owner_nsid = creator['user']['id']

        faves = things.Faves.faves_for_owner(owner_nsid, what, is_commentor)
        self.assign("count_faves", faves.count())

        faves = faves.fetch(100)
        self.prepare_faves(faves)

        if self.user and owner_nsid == self.user.nsid:
            self.assign('who', 'You')

            delete_crumb = self.generate_crumb(self.user, 'method=delete')
            self.assign('delete_crumb', delete_crumb)

        else:
            user = self.flickr_get_user_info(owner_nsid)
            self.assign('who', user['username']['_content'])

        self.assign('what', what)

        rss_feed = "http://thingsicantfave.appspot.com/rss/faved/%s" % owner_nsid

        if what:
            rss_feed += "/%s" % what

        self.assign("who_nsid", owner_nsid)
        self.assign("rss_feed", rss_feed)

        self.assign('faves', faves)
        self.display('faved.html')
        return

class About(things.Request):

    def get(self):

        self.check_logged_in(self.min_perms)

        self.display("about.html")
        return
