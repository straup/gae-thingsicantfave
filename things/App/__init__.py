import things
import things.Faves

class Main (things.Request):

    def get(self):

        if not self.check_logged_in(self.min_perms) :
            self.display("main_logged_out.html")
            return

        url = self.request.get('url')

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

        thing = self.parse_url(self.request.get('url'))

        if not thing:
            self.assign('error', 'cannot_parse')
            self.display('main_logged_in.html')
            return

        if things.Faves.has_faved(self.user.nsid, thing['url']):
            self.assign('error', 'already_faved')
            self.display('main_logged_in.html')
            return

        try:
            thing['creator_nsid'] = self.user.nsid
            fave = things.Faves.fave_thing(thing)
        except Exception, e:
            self.assign('error', 'cannot_add')
            self.display('main_logged_in.html')
            return

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

        self.assign('faves', faves)
        self.display('recently_faved.html')
        return

class FavedBy(things.Request):

    def get(self, who=None, what=None):

        self.check_logged_in(self.min_perms)
        creator_nsid = None

        if who == 'me':

            if not self.check_logged_in(self.min_perms) :
                self.redirect('/faves')
                return

            creator_nsid = self.user.nsid

        else:

            if who.rfind("@N") > 0:
                creator_nsid = who
            else:
                creator = self.find_user(who)
                creator_nsid = creator['user']['id']

        faves = things.Faves.faves_for_creator(creator_nsid, what)
        self.assign("count_faves", faves.count())

        faves = faves.fetch(100)
        self.prepare_faves(faves)

        if self.user and creator_nsid == self.user.nsid:
            self.assign('who', 'You')
        else:
            user = self.flickr_get_user_info(creator_nsid)
            self.assign('who', user['username']['_content'])

        self.assign('what', what)

        rss_feed = "http://thingsicantfave.appspot.com/rss/faves/%s" % creator_nsid

        if what:
            rss_feed += "/%s" % what

        self.assign("rss_feed", rss_feed)

        self.assign('faves', faves)
        self.display('faved_by.html')
        return
