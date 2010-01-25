import things
import things.Faves

class Main (things.Request):

    def get(self):

        if not self.check_logged_in(self.min_perms) :
            self.display("main_logged_out.html")
            return

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
        self.display('main_logged_in.html')
        return

class Faves(things.Request):

    def get(self, who=None, what=None):

        creator_nsid = None

        if who == 'me':

            if not self.check_logged_in(self.min_perms) :
                self.display("main_logged_out.html")
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

        for f in faves:

            if self.user and self.user.nsid == f.creator_nsid:
                f.creator = 'you'
            else:
                creator = self.flickr_get_user_info(f.creator_nsid)
                f.creator = creator['username']['_content']

            if self.user and self.user.nsid == f.owner_nsid:
                f.owner = 'you'
            else:
                owner = self.flickr_get_user_info(f.owner_nsid)
                f.owner = owner['username']['_content']

            if f.commentor_nsid:

                if self.user and self.user.nsid == f.commentor_nsid:
                    f.commentor = 'you'
                else:
                    commentor = self.flickr_get_user_info(f.commentor_nsid)
                    f.commentor = commentor['username']['_content']

        self.assign('faves', faves)
        self.display('faves.html')
        return
