    var tag = this;
    tag.store = stores.publicationStore;
    tag.expanded = [];

    tag.filter = tag.store.set_filter;
    tag.page = tag.store.page;

    tag.store.on('publications_refreshed', function(){
        tag.update();
    });

    tag.list = function(objects){
        returns = _.map(objects, 'name');
        return returns;
    };

    tag.toggle_expand_result = function(e){
        var id = e.item.result.id;
        if (_.indexOf(tag.expanded, id) == -1){
            tag.expanded.push(id);
            if (e.item.result.versions === undefined) {
                tag.store.more_data(e.item.result, tag)
            }


            return}
        if (_.indexOf(tag.expanded, id) != -1){_.pull(tag.expanded, id);}
    };
