#!/usr/bin/env python

import wsgiref.handlers
from google.appengine.ext import webapp

import things.API
import things.App
import things.Auth
import things.Export
import things.Feeds

if __name__ == '__main__':

  handlers = [
    ('/', things.App.Main),
    (r'/about/?$', things.App.About),

    (r'/fave(?:s|d)/?$', things.App.RecentFaves),
    (r'/faves/([^/]+)(?:/(galleries|sets|collections|comments|people|groups))?/?$', things.App.FavedBy),
    (r'/faved/([^/]+)(?:/(galleries|sets|collections|comments|people|groups))?/?$', things.App.Faved),

    (r'/rss/faves/?$', things.Feeds.RSS),
    (r'/rss/faves/([^/]+)(?:/(galleries|sets|collections|comments|people|groups))?/?$', things.Feeds.RSS),

    ('/export', things.Export.JSON),
    ('/signout', things.Auth.Signout),
    ('/signin', things.Auth.Signin),
    ('/auth', things.Auth.TokenDance),

    ('/api', things.API.Dispatch),
]

  application = webapp.WSGIApplication(handlers, debug=False)
  wsgiref.handlers.CGIHandler().run(application)
