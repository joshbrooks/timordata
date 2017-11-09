import riot = require('riot');
import _ = require('lodash');

riot.mixin('tagExtensions', {
    init: function() {},
    list_child_tags: function () {
        const tag = this;
        let child_returns = [];
        let returns = _(tag.tags).values().flatten().value();
        _.remove(returns, _.isUndefined);
        _.each(returns, function (child) {
            if (_.isFunction(child.list_child_tags)) {
                child_returns = child.list_child_tags();
                returns = _.concat(returns, child_returns)
            }
            return returns;
        });
        return _.flatten(_.concat(returns));
    },
});