from google.appengine.ext import db

class dbFaves (db.Model):
    creator_nsid = db.StringProperty()
    owner_nsid = db.StringProperty()
    commentor_nsid = db.StringProperty()

    category = db.CategoryProperty()
    url = db.LinkProperty()
    date_created = db.DateTimeProperty(auto_now_add=True)
