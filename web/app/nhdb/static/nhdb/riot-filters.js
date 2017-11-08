define(["require", "exports", "riot", "lodash"], function (require, exports, riot, _) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    var Filters = (function () {
        function Filters(table) {
            this.table = table;
            this.offset = 0;
            this.limit = 10;
            this.reverse = false;
            this.order_by = 'name';
        }
        Filters.prototype.apply_one_filter = function (t, i, f, p) {
            var where = _.invoke(t, 'where', i);
            var filter = _.invoke(where, f, p);
            return filter.toArray();
        };
        Filters.prototype.clear = function () { this.offset = 0; this.filters = {}; };
        Filters.prototype.unset = function (i, f) {
            _.unset(this, ['filters', i, f]);
            if (_.has(this, ['filters', i]) && _.keys(_.get(this, ['filters', i])).length === 0) {
                _.unset(this, ['filters', i]);
            }
        };
        Filters.prototype.set = function (i, f, p) { this.offset = 0; _.set(this, ['filters', i, f], p); };
        Filters.prototype.set_order_by = function (p) { this.order_by = p; };
        Filters.prototype._apply = function () {
            var _this = this;
            var promises = _.map(this.filters, function (index, ix) {
                return _.map(index, function (p, func) { return _this.apply_one_filter(_this.table, ix, func, p); });
            });
            return Promise.all(_.flatten(promises));
        };
        Filters.prototype.results = function () {
            var table = this.table;
            var self = this;
            var order = self.order_by;
            if (self.offset < 0) {
                self.offset = 0;
            }
            if (_.keys(this.filters).length === 0) {
                table.count().then(function (c) {
                    self.count = c;
                });
                if (self.reverse) {
                    return table.orderBy(order).reverse().offset(self.offset).limit(self.limit).toArray();
                }
                return table.orderBy(this.order_by).offset(self.offset).limit(self.limit).toArray();
            }
            return this._apply().then(function (a) {
                var filtered;
                a.push('pk');
                filtered = _.intersectionBy.apply(this, a);
                self.count = _.size(filtered);
                if (self.reverse) {
                    return _(filtered).sortBy(order).reverse().slice(self.offset, self.offset + self.limit).value();
                }
                return _(filtered).sortBy(order).slice(self.offset, self.offset + self.limit).value();
            });
        };
        return Filters;
    }());
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
                tag.update({ results: results });
            });
        }
    });
});
//# sourceMappingURL=riot-filters.js.map