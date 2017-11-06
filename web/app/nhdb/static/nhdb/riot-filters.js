var Filters = function (table) {
    this.filters = {};
    this.table = table;
    this.offset = 0;
    this.limit = 10;
    this.order_by = 'name';
};

function apply_one_filter(t, i, f, p) {
    var where = _.invoke(t, 'where', i);
    var filter = _.invoke(where, f, p);
    return filter.toArray();
}

Filters.prototype.clear = function () {
    this.offset = 0;
    _.set(this, 'filters', {});
};
Filters.prototype.unset = function (i, f) {
    this.offset = 0;
    _.unset(this, ['filters', i, f]);
    if (_.has(this, ['filters', i]) && _.keys(_.get(this, ['filters', i])).length === 0) {
        _.unset(this, ['filters', i]);
    }
};
Filters.prototype.set = function (i, f, p) {
    this.offset = 0;
    _.set(this, ['filters', i, f], p);
};
Filters.prototype.set_order_by = function(p){
    this.order_by = p;
};

Filters.prototype._apply = function () {
    var t = this.table;
    var filters = this.filters;
    var promises = _.map(filters, function (index, ix) {
        return _.map(index, function (p, func) {
            return apply_one_filter(t, ix, func, p);
        });
    });
    return Promise.all(_.flatten(promises));
};
Filters.prototype.results = function () {
    var table = this.table;
    var self = this;
    if (self.offset < 0) {
        self.offset = 0;
    }
    if (_.keys(this.filters).length === 0) {
        table.count().then(function (c) {
            self.count = c;
        });
        if (self.reverse){return table.orderBy(this.order_by).reverse().offset(self.offset).limit(self.limit).toArray();}
        return table.orderBy(this.order_by).offset(self.offset).limit(self.limit).toArray();
    }

    return this._apply().then(function (a) {
        var filtered;
        a.push('pk');
        filtered = _.intersectionBy.apply(this, a);
        self.count = _.size(filtered);
        if (self.reverse){return _(filtered).sortBy(this.order_by).reverse().slice(self.offset, self.offset + self.limit).value();}
        return _(filtered).sortBy(this.order_by).slice(self.offset, self.offset + self.limit).value();
    });
};

riot.mixin('tableFilterMixin', {
    init: function () {
        var tag = this;
        tag.filters = new Filters(tag.opts.table);
        tag.filters.limit = tag.opts.limit || tag.filters.limit;
        tag.filters.offset = tag.opts.offset || tag.filters.offset;
        tag.filters.order_by = tag.order_by || tag.opts.order_by || tag.filters.order_by;
    },
    get_results: function () {
        var tag = this;
        tag.filters.results().then(function (results) {
            tag.update({results: results});
        });
    }
});
