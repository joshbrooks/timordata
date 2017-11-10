<search-choice>
    <label>{opts.label}</label>

    <div class="dropdown {open:dropdown_open}">

        <button class="buttontext btn btn-block btn-default" type="button" onclick="{toggle_dropdown}" disabled="{opts.is_disabled}">
            <span>{ opts.label }: {_.size(selected_choices) > 1 ? '('+_.size(selected_choices)+')' : ''} { selected || 'All' }</span>
            <span if="{opts.show_code}" class="small"></span>
            <span class="right"><span class="caret"></span></span>
        </button>

        <ul if="{dropdown_open}" class="dropdown-menu">

            <div class="input-group search">
                <input type="text" class="form-control" placeholder="{opts.placeholder|| 'Search for...'}" ref="searchbox" oninput="{ search }">
                <div class="input-group-addon"><span class="glyphicon glyphicon-search"></span></div>
            </div>

            <li onclick="{clear_choices}">
                <a>
                    Clear
                </a>
            </li>
            <li class="divider"></li>
            <li each="{option in choice}" onclick="{cowsay}">
                <a>
                        {option.name}
                    <span class="glyphicon glyphicon-ok" onclick="{nope}" if="{_.includes(selected_choices, option)}" aria-hidden="true"></span>
                </a>
            </li>
            <li if="{has_overflow}" class="disabled">
                <a>
                    Some options are not displayed. Use the search filter to show other options.
                </a>
            </li>

        </ul>
    </div>

    <style>
        .buttontext {
          width: 95%;
          overflow: hidden;
          white-space: nowrap;
          display: block;
          text-overflow: ellipsis;
        }​,
        .search {
            margin-left: 10px; margin-right:10px; margin-bottom:10px;
                 }
    </style>

    <script>
        var tag = this;
        tag.selected_choices = tag.opts.selected_choices || [];

        tag.cowsay = function cowsay(e){
            e.stopPropagation()
            tag.onselect(e.item.option);};

        function clear_choices(){tag.onselect();}
        /**
         * Toggle dropdown options open or cloded
         */
        function toggle_dropdown() {
            if (tag.dropdown_open === false) {
                tag.update({dropdown_open: true});
                tag.one('updated', function () {
                    $('input[ref="searchbox"]', tag.root).focus();
                });
            } else {
                tag.search('__CLEAR__');
                tag.update({dropdown_open: false});
            }
        }
        function make_option(option){
            var name;
            var choice;
            if (tag.opts.display_property){name = _.get(option, tag.opts.display_property)}
            else if ( _.isUndefined(option.name)){ name = '?'}
            else name = option.name.en || option.name.tet || option.name.name || option.name || '?';
            choice = {pk: option.pk || option.code, name: name};
            if (_.includes(tag.selected_choices , choice)){choice.active=true}
            return choice
        }
        function make_options(options){
            return _.map(options, make_option)
        }
        function searchValue(){return tag.refs.searchbox.value}
        function overflow(choices){return (!_.isUndefined(tag.opts.number_of_choices) && _.size(choices) > _.toInteger(tag.opts.number_of_choices))}
        function slice(choices, page){return _.slice(choices, page || 0, _.toInteger(tag.opts.number_of_choices))}
        function setChoices(choices){
            var has_overflow = overflow(choices);

            if (has_overflow){choices = slice(choices)}
            var processed_choices = make_options(choices);
            // Things get interesting here with multiple languages
            // Hence , 'uniqBy'
            processed_choices =  _.compact(_.uniqBy(processed_choices, 'pk'));
            tag.update({choice: processed_choices, has_overflow:has_overflow})
        }
        function search(value){
            var searchvalue = searchValue();
            var promise;
            if (value === '__CLEAR__' || searchvalue === ''){
                promise = tag.opts.related_table.toArray();
            } else {
                promise = tag.opts.related_table.where(tag.opts.index).startsWithIgnoreCase(tag.refs.searchbox.value).toArray();
            }
            promise.then(function(choice){setChoices(choice)})
        }
        function onselect(choice){
            var clear_choices = _.isUndefined(choice);
            var selected = _.includes(tag.selected_choices, choice);
            if (!tag.opts.multiple || _.isUndefined(choice)){
                _.each(tag.selected_choices, function(c){c.active = false});
                tag.selected_choices = []}
            if (selected) {choice.active = false; _.pull(tag.selected_choices, choice)}
            else if (!clear_choices) {choice.active = true; tag.selected_choices.push(choice)}

            var opts = tag.opts;

            var i = opts.filter_table_index; // Which index on the target table to filter on
            var cb = opts.func; // Callback function on selection
            var cast_int = opts.int; // Should we expect all values to be integers (ie index key type)
            var multi = opts.multiple; // Should we have multiple options (ie array)
            var val =  _.map(tag.selected_choices, 'pk');

            // Coercion and casting of types to integer
            if (!multi && cast_int){val = _.toInteger(val)}
            if (multi && cast_int){val = _.map(val, _.toInteger)}
            if (multi){val = _.compact(val)}

            function set(val){window.project_app.trigger('set_filter' , i, cb, val) }
            function unset(){window.project_app.trigger('unset_filter', i, cb);}
            function do_unset(){ // "Unset" filter if an empty-is value is given
                if (!multi && val === '') { return true;}
                if (multi && _.size(val) === 1 && val[0] === ""){return true}
                if (multi && _.size(val) === 0){return true}
            }

            if (do_unset()) {unset();}
            else {set(val)}
            return tag.update({selected: _(tag.selected_choices).map('name').join(', ')});
        }

        tag.on('before-mount', function() {
            tag.dropdown_open = false;
            var related_table = tag.opts.related_table;
            if (_.isUndefined(related_table)){console.warn('Related_table is undefined')}
            if (!_.isFunction(related_table.toArray)) {return {}} // This is NOT a table probably
            related_table.toArray().then(function (choice) {setChoices(choice)})
        });

        function handleClickOutside(e) {

            /* Click outside the dropdown to close it, unless the target of the click is a "show_more" or "show_less" button */
            if (!tag.root.contains(e.target) && tag.dropdown_open)
                 {
                toggle_dropdown();
            }
        }

        tag.on('mount', function () {
            document.addEventListener('click', handleClickOutside);
        });

        tag.on('unmount', function () {
            document.removeEventListener('click', handleClickOutside);
        });


        tag.toggle_dropdown = toggle_dropdown;
        tag.onselect = onselect;
        tag.search = search;
        tag.clear_choices = clear_choices;

    </script>
</search-choice>

<search-input>
    <label>{opts.label}
        <input ref="input" oninput="{oninput}" placeholder="{opts.placeholder}">
    </label>
    <script>
        var tag = this;
        tag.oninput = function(e){
            var val = tag.refs.input.value;
            if (val === ''){
                window.project_app.trigger('unset_filter', tag.opts.index, tag.opts.func);
                return;
            }
            if (opts.int){val = _.toInteger(val)}
            window.project_app.trigger('set_filter', tag.opts.index, tag.opts.func, val)
        }

    </script>
</search-input>