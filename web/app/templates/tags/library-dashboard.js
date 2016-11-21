    var tag = this;
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