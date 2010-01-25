import things
import things.Faves

from django.utils import simplejson

class JSON (things.Request):

    def get(self):

        if not self.check_logged_in(self.min_perms) :
            self.redirect('/')
            return

        faves = things.Faves.faves_for_creator(self.user.nsid)
        faves = faves.fetch(faves.count())

        dump = []

        for f in faves:
            dump.append({
                    'creator_nsid' : f.creator_nsid,
                    'owner_nsid' : f.owner_nsid,
                    'commentor_nsid' : f.commentor_nsid,
                    'date_created' : str(f.date_created),
                    'category' : f.category,
                    'url' : f.url,
                    })

        self.response.headers['Content-Type'] = "text/json"

        try:
            print simplejson.dumps(dump)
        except Exception, e:
            pass

        return
