    var tag = this;
    tag.sort = {};
    tag.store = stores.publicationStore;

    tag.filter = tag.store.set_filter;
    tag.page = tag.store.page;

    tag.store.on('publications_refreshed', function(){
        tag.update();
    });

    tag.filter_by_category = function(e) {
        var tag = this;
        var category = tag.parent.category;
        var call = {item:{}};
        call.item[category] = {pk:tag.store.find_by_name(category, e.item.name).pk};
        tag.filter[category](call)
    };

    tag.orderby_count = function(e){
        tag.orderby(e.item.category, 'count');
    };

    tag.orderby_name = function(e) {
        tag.orderby(e.item.category, 'name');
    };

    tag.orderby = function(category, iteratee){
        var tag = this;

        if (tag.sort.category === category){
            if (tag.sort.order === 'asc')  {tag.sort.order = 'desc'}
            else if (tag.sort.order === 'desc') {tag.sort.order =  'asc'}
            else if (tag.sort.order === undefined) {tag.sort.order = 'asc'}
        } else if (tag.sort.category !== category){
            tag.sort.order = 'asc';
        }

        tag.sort.category = category;
        tag.sort.iteratee = iteratee;


        tag.store.counts[tag.sort.category] = _.orderBy(tag.store.counts[tag.sort.category], [tag.sort.iteratee], [tag.sort.order])
    };