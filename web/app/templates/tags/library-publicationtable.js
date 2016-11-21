    var tag = this;
    tag.store = stores.publicationStore;

    tag.filter = tag.store.set_filter;
    tag.page = tag.store.page;

    tag.store.on('publications_refreshed', function(){
        tag.update();
    });

    tag.list = function(objects){
        returns = _.map(objects, 'name');
        return returns;
    };

