import Dexie from "dexie";
import riot = require('riot');
import _ = require('lodash');

class Filters {
    filters: object;
    offset: number = 0;
    limit: number = 10;
    reverse: boolean = false;
    order_by: string = 'name.en';
    count: number = 0;
    constructor(readonly table: Dexie.Table<any, number>) {}

    private static apply_one_filter(t, i, f, p) : any[] {
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
    private apply (): Promise<any> {
        const promises: Array<any> = _.map(this.filters, (index, ix) => _.map(index, (p, func) => Filters.apply_one_filter(this.table, ix, func, p)));
        return Promise.all<void>(_.flatten(promises));
    }
    results() : any {
        const self = this;
        const order = self.order_by;
        if (self.offset < 0) {
            self.offset = 0;
        }
        if (_.keys(this.filters).length === 0) {
            this.table.count().then(function (c) {
                self.count = c;
            });
            if (self.reverse){
                return this.table.orderBy(order).reverse().offset(self.offset).limit(self.limit).toArray();
            }
            return this.table.orderBy(order).offset(self.offset).limit(self.limit).toArray();
        }

        return this.apply().then(function (a) {
            let filtered;
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