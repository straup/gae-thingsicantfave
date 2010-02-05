if (! info){
    var info = {};
}

if (! info.aaronland){
    info.aaronland = {};
}

if (! info.aaronland.things){
    info.aaronland.things = {};
}

info.aaronland.things.Faves = function(args){
    this.args = args;

    var api_args = {
        'host' : this.args['host'],
    };

    this.api = new info.aaronland.flickrapp.API(api_args);
};

info.aaronland.things.Faves.prototype.delete = function(fave_id){

    var _self = this;

    var doThisOnSuccess = function(rsp){
	var li = $('#' + fave_id);
	li.fadeOut();

	var remaining = rsp['count'];
	console.log(remaining);
    };

    var doThisIfNot = function (rsp){
	var e = $('#error');
	e.html('There was a problem deleting that fave: ' + rsp['error']['message']);
	e.show();

	e.fadeOut(10000);
    };

    var args = {
        'crumb' : this.args['delete_crumb'],
	'fave_id' : fave_id,
        'format' : 'json',
    }

    this.api.api_call('delete', args, doThisOnSuccess, doThisIfNot);
};