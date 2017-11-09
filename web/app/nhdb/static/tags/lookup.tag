<lookup-value>
    <span if="{!resolved}">{opts.placeholder || 'loading'}<br></span>
    <span if="{resolved}">{resolved}<br></span>
    <script>
        var tag = this;
        tag.resolved = false;

        function lookup_value() {
            tag.promise = new Promise(function (resolve, reject) {
                tag.opts.table.where('pk').equals(tag.opts.lookupvalue).first()
                    .then(function (a) {
                        resolve(_.get(a, tag.opts.display_attribute));
                    }).catch(function (a) {
                    reject([]);
                });
            });
        }
        tag.on('mount', function(){ lookup_value(); tag.promise.then(function(r){tag.update({resolved:r})});});

    </script>
</lookup-value>

<lookup-array>
    <span if="{!resolved}">{opts.placeholder || 'loading'}</span>
    <span class="tag" if="{resolved}" each="{tag, number in resolved}">{tag}<virtual if="{number < count - 1}"> / </virtual></span>

    <script>
        var tag = this;

        function lookup_array() {
            return new Promise(function (resolve, reject) {
                tag.opts.table.where('pk').anyOf(_.compact(tag.opts.array)).toArray()
                    .then(function (a) {
                        resolve(_.map(a, tag.opts.display_attribute));
                    }).catch(function (a) {
                    reject([]);
                });
            });
        }

        tag.on('mount', function(){ lookup_array().then(function(r){tag.update({resolved:r, count:_.size(r)})});});

    </script>

</lookup-array>