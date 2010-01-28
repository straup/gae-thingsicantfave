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

	# This hasn't been tested yet...
	# self.set_handler('POST', 'delete', 'api_delete_fave')

    def api_delete_fave(self):

	if not self.check_logged_in(self.min_perms) :
	    self.api_error(403)
	    return

	required = ('crumb', 'fave_id')

	if not self.ensure_args(required) :
	    return

	if not self.ensure_crumb('method=delete') :
	    return

	fave = things.Faves.fetch_by_key(self.request.get('fave_id'))

	if not fave:
		self.api_error(1, 'Invalid fave ID')
		return

	if fave['category'] == 'comments':
		if fave['commentor_nsid'] != self.user.nsid:
			self.api_error(2, 'Insufficient permissions')
			return
	else:
		if fave['creator_nsid'] != self.user.nsid:
			self.api_error(2, 'Insufficient permissions')
			return

	try:
		fave.delete()
	except Exception, e:
		self.api_error(3, 'There was a problem deleting the fave')
		return

	self.api_ok()
	return
