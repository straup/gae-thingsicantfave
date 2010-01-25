#!/usr/bin/env python

import wsgiref.handlers
from google.appengine.ext import webapp

import things.App
import things.Auth

if __name__ == '__main__':

  handlers = [
    ('/', things.App.Main),
    (r'/faves/?$', things.App.RecentFaves),
    (r'/faves/([^/]+)(?:/(galleries|sets|collections|comments))?/?$', things.App.FavedBy),
    ('/signout', things.Auth.Signout),
    ('/signin', things.Auth.Signin),
    ('/auth', things.Auth.TokenDance),
]

  application = webapp.WSGIApplication(handlers, debug=False)
  wsgiref.handlers.CGIHandler().run(application)
