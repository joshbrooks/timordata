import Table from "dexie";
import riot = require('riot');
import _ = require('lodash');

class Filters {
    filters: object;
    offset: number = 0;
    limit: number = 10;
    count: number;
    reverse: boolean = false;
    order_by: string = 'name';
    constructor(readonly table: Table) {}

    private apply_one_filter(t, i, f, p) : any[] {
        const where = _.invoke(t, 'where', i);
        const filter = _.invoke(where, f, p);
        return filter.toArray();
    }

    clear(): void { this.offset = 0; this.filters = {}}
    unset(i, f): void {
        _.unset(this, ['filters', i, f]);
        if (_.has(this, ['filters', i]) && _.keys(_.get(this, ['filters', i])).length === 0) {
            _.unset(this, ['filters', i]);
        }
    }
    set(i, f, p): void {this.offset = 0; _.set(this, ['filters', i, f], p)}
    set_order_by(p): void {this.order_by = p;}
    _apply (): Promise {
        const promises = _.map(this.filters, (index, ix) =>
            _.map(index, (p, func) => this.apply_one_filter(this.table, ix, func, p)));
        return Promise.all(_.flatten(promises));
    }
    results() : void {
        const table = this.table;
        const self = this;
        const order = self.order_by;
        if (self.offset < 0) {
            self.offset = 0;
        }
        if (_.keys(this.filters).length === 0) {
            table.count().then(function (c) {
                self.count = c;
            });
            if (self.reverse){return table.orderBy(order).reverse().offset(self.offset).limit(self.limit).toArray();}
            return table.orderBy(this.order_by).offset(self.offset).limit(self.limit).toArray();
        }

        return this._apply().then(function (a) {
            let filtered : array;
            a.push('pk');
            filtered = _.intersectionBy.apply(this, a);
            self.count = _.size(filtered);
            if (self.reverse){return _(filtered).sortBy(order).reverse().slice(self.offset, self.offset + self.limit).value();}
            return _(filtered).sortBy(order).slice(self.offset, self.offset + self.limit).value();
        });
    }
}

riot.mixin('tableFilterMixin', {
    init: function () {
        const tag = this;
        tag.filters = new Filters(tag.opts.table);
        tag.filters.limit = tag.opts.limit || tag.filters.limit;
        tag.filters.offset = tag.opts.offset || tag.filters.offset;
        tag.filters.order_by = tag.order_by || tag.opts.order_by || tag.filters.order_by;
    },
    get_results: function () {
        const tag = this;
        tag.filters.results().then(function (results) {
            tag.update({results: results});
        });
    }
});
