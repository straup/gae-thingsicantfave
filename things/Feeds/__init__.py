import things
import things.Faves
from ext.PyRSS2Gen import RSS2, RSSItem, Guid

import StringIO
import datetime

class Syndicate (things.Request):

    def get_recent(self, who=None, what=None):

        if who:

            if who.rfind("@N") > 0:
                creator_nsid = who
            else:
                creator = self.find_user(who)
                creator_nsid = creator['user']['id']

            faves = things.Faves.faves_for_creator(creator_nsid, what)
        else :
            faves = things.Faves.recently_faved()

        faves = faves.fetch(15)
        self.prepare_faves(faves)

        return faves

class RSS (Syndicate):

    def get(self, who=None, what=None):

        faves = self.get_recent(who, what)
        items = []

        for fv in faves:

            if fv.commentor_nsid:
                title = '%s faved a %s by %s' % (fv.creator, fv.category_singular, fv.commentor)
            else:
                title = '%s faved a %s by %s' % (fv.creator, fv.category_singular, fv.owner)

            items.append(RSSItem(
                    title = title,
                    link = fv.url,
                    guid = Guid('x-urn:thingsicantfave:%s' % fv.key()),
                    ))

        feed_title = 'things I can\'t fave'
        feed_link = 'http://thingsicantfave.appspot.com/faves'

        if who:
            feed_title += ' - %s' % who
            feed_link += '/%s' % who

            if what:
                feed_title += ' (%s)' % what
                feed_link += '/%s' % what

        rss = RSS2(
            title = feed_title,
            link = feed_link,
            description = "",
            lastBuildDate = datetime.datetime.now(),
            items = items)

        fh = StringIO.StringIO()
        rss.write_xml(fh, 'UTF-8')

        self.response.headers['Content-Type'] = "application/xml"
        self.response.out.write(fh.getvalue())
        return
