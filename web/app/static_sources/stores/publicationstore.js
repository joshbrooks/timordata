function PublicationStore() {
    var store = this;
    riot.observable(store);
    store.publications = [];
    store.url_function = Urls['library:publication-list'];
    store.url = store.url_function();
    store.url_args = {};
    store.per_page = 25;
    store.current_page = 1;
    store.last_page = 1;
    store.filters = {};
    store.current_sort = 'name';
    store.current_sort_reverse = false;

    store.sort = {
        name: function(){
            if (store.current_sort != 'name') {
                store.current_sort = 'name';
                store.trigger('refresh')
            }
            else (store.sort.reverse());
        },
        year: function() {
            if (store.current_sort != 'year') {
                store.current_sort = 'year';
                store.refresh_data();
            }
            else (store.sort.reverse());
        },
        reverse: function() {
            store.current_sort_reverse = !store.current_sort_reverse;
            store.refresh_data();
        }
    };

    store.filter = function(){
        var results = _(store.initial_data.results);
        var apply_filter = function(r, filter, filter_value){
            return _(r).filter(function(result){return _.some(result[filter],{pk: filter_value})});
        };
        for (var filter in store.filters){
            results = apply_filter(results, filter, store.filters[filter]);
        }
        return results.value();
    };

    store.refresh_data = function(){
        
        var organization;
        var sector;
        var author;
        var tag;
        var counts = {};
        var listed = {};
        var filtered_results;
        var sorted_results;
        var paginated_results;
        var first_result;
        var last_result;
        var order;

        store.data = store.initial_data;
        filtered_results = store.filter();
        store.listed = {};
        store.counts = {};
        
        organization = _.flatten(_.map(filtered_results, 'organization'));
        counts.organization = _.map(_.countBy(organization, 'name'), function(i, j){return {'name':j, 'count':i}});
        listed.organization = _.uniqBy(organization, 'pk');

        author = _.flatten(_.map(filtered_results, 'author'));
        counts.author = _.map(_.countBy(author, 'name'), function(i, j){return {'name':j, 'count':i}});
        listed.author = _.uniqBy(author, 'pk');
        
        sector = _.flatten(_.map(filtered_results, 'sector'));
        counts.sector = _.map(_.countBy(sector, 'name'), function(i, j){return {'name':j, 'count':i}});
        listed.sector = _.uniqBy(sector, 'pk');
        
        tag = _.flatten(_.map(filtered_results, 'tag'));
        counts.tag = _.map(_.countBy(tag, 'name'), function(i, j){return {'name':j, 'count':i}});
        listed.tag = _.uniqBy(tag, 'pk');

        store.counts = counts;
        store.listed = listed;

        order = store.current_sort_reverse ? 'desc' : 'asc';

        sorted_results = _(filtered_results).orderBy(store.current_sort, order);

        store.last_page = Math.floor(sorted_results.value().length / store.per_page) + 1;
        store.current_page = Math.min(store.current_page, store.last_page);
        store.current_page = Math.max(store.current_page, 1);
        first_result = (store.current_page - 1) * store.per_page;
        last_result = (store.current_page + 0) * store.per_page;

        paginated_results = _(sorted_results).slice(first_result, last_result);
        store.results = paginated_results.value();
        store.message = '';
        store.trigger('publications_refreshed')
    };

    store.more_data = function(result, tag) {
        console.log('getting more data for result');

        result.request = $.ajax({
            dataType: 'json',
            contentType: 'application/json',
            method: 'GET',
            url: Urls['library:publication_versions_list']()+result.id+ '/',
            headers: {'X-CSRFTOKEN': Cookies.get('csrftoken')}
        });

        result.request.done(function(){
            result.request.json = JSON.parse(result.request.responseText);
            tag.update();
        })
    };

    store.find = function (object_type, object_id){
        return _(store.listed[object_type]).find({pk:object_id})
    };

    store.find_by_name = function (object_type, object_name){
        return _(store.listed[object_type]).find({name:object_name})
    };

    store.add_filter = function(name, pk){
        store.filters[name] = pk;
        store.refresh_data();
    };

    store.clear_filter = function(e) {
        store.set_filter.clear(e.item.category)
    };

    store.set_filter = {
        clear: function (e) {
            _.unset(store.filters, e.item.key || e.item.category);
            store.trigger('refresh')
        },
        clearAll: function () {
            store.filters = {};
            store.trigger('refresh')
        },
        organization: function (e) {
            store.add_filter('organization', e.item.organization.pk);
        },
        author: function (e) {
            store.add_filter('author', e.item.author.pk);
        },
        tag: function (e) {
            store.add_filter('tag', e.item.tag.pk);
        },
        sector: function (e) {
            store.add_filter('sector', e.item.sector.pk);
        }
    };

    store.page = {
        first: function() {store.current_page = 1; store.refresh_data();},
        next: function() {store.current_page += 1; store.refresh_data();},
        previous: function() {store.current_page -= 1; store.refresh_data();},
        last: function() {store.current_page = store.last_page; store.refresh_data();}
    };


    store.on('refresh', function() {
        store.refresh_data();
    });

    store.on('reload', function () {
        store.message="Loading data...";
        store.initial_data = [];
        store.data = [];
        store.trigger('publications_refreshed')
        var xhr = $.ajax({
            dataType: 'json',
            contentType: 'application/json',
            method: 'GET',
            url: store.url + '?' + decodeURIComponent($.param(store.url_args)),
            headers: {'X-CSRFTOKEN': Cookies.get('csrftoken')}
        });
        xhr.done(function(returned_data){
            console.log('success');
            store.initial_data = returned_data;
            store.refresh_data();
        })
    });

}

