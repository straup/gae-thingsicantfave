from things.Tables import dbFaves
from google.appengine.ext import db

def has_faved(creator_nsid, url):

    gql = "SELECT * FROM dbFaves WHERE creator_nsid = :1 AND url = :2"
    res = db.GqlQuery(gql, creator_nsid, url)

    return res.count()

def fave_thing(args):

    thing = dbFaves()
    thing.creator_nsid = args['creator_nsid']
    thing.owner_nsid = args['owner_nsid']
    thing.category = db.Category(args['category'])
    thing.url = db.Link(args['url'])

    if args.get('commentor_nsid', False):
        thing.commentor_nsid = args['commentor_nsid']

    thing.put()
    return thing

def recently_faved():

    gql = "SELECT * FROM dbFaves ORDER BY date_created DESC"
    res = db.GqlQuery(gql)

    return res

def fetch_by_key(key):

    db_key = db.Key(key)

    gql = "SELECT * FROM dbFaves WHERE key= :1"
    res = db.GqlQuery(gql, db_key)
    return ref.fetch()

def faves_for_creator(owner_nsid, category=None):

    params = [ owner_nsid ]

    gql = "SELECT * FROM dbFaves WHERE creator_nsid = :1"

    if category:
        gql += " AND category = :2"
        params.append(category)

    gql += " ORDER BY date_created DESC"

    res = db.GqlQuery(gql, *params)
    return res

def faves_for_owner(owner_nsid, category=None, is_commentor=False):

    params = [ owner_nsid]

    gql = "SELECT * FROM dbFaves"

    if is_commentor:
        gql += " WHERE commentor_nsid = :1"
    else:
        gql += " WHERE owner_nsid = :1"

    if category:
        gql += " AND category = :2"
        params.append(category)

    gql += " ORDER BY date_created DESC"

    res = db.GqlQuery(gql, *params)
    return res
