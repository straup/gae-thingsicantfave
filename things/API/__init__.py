from FlickrApp.API import FlickrAppAPI
from config import config
import things
import things.Faves
import time
import md5

class Dispatch (things.Request, FlickrAppAPI) :

    def __init__(self):

	things.Request.__init__(self)
	FlickrAppAPI.__init__(self)

        self.set_handler('POST', 'delete', 'api_delete_fave')

    def api_delete_fave(self):

	if not self.check_logged_in(self.min_perms) :
	    self.api_error(403)
	    return

        if self.user.nsid != '35034348999@N01':
            self.api_error(403)
            return

	required = ('crumb', 'fave_id')

	if not self.ensure_args(required) :
	    return

	if not self.ensure_crumb('method=delete') :
	    return

        fave_id = self.request.get('fave_id')
        key = fave_id.replace("fave_", "")

        try:
            fave = things.Faves.fetch_by_key(key)
        except Exception, e:
            self.api_error(1, 'Fave ID not found')
            return

	if not fave:
		self.api_error(2, 'Invalid fave ID')
		return

        if fave.creator_nsid != self.user.nsid:
            self.api_error(3, 'Insufficient permissions')
            return

	try:
		fave.delete()
	except Exception, e:
		self.api_error(4, 'There was a problem deleting the fave')
		return

        faves = things.Faves.faves_for_creator(self.user.nsid)
        count = faves.count()

	self.api_ok({'count' : count})
	return
