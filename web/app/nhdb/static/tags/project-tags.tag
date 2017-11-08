
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

<project-app>
    <router>
        <route path="list"><project-list ref="project_list"/></route>
        <route path="project/*"><<project-detail/></route>
    </router>
    <script>
        var tag = this;
        tag.on('mount', function(){
            window.project_app = tag;
        });
        tag.on('set_filter', function(index, func, param){
            var list = tag.tags.router.tags.route[0].refs.project_list;
            list.filters.set(index, func, param);
            list.trigger('refresh_list');
        });

        tag.on('unset_filter', function(index, func){
            var list = tag.tags.router.tags.route[0].refs.project_list;
            list.filters.unset(index, func);
            list.trigger('refresh_list');
        })

    </script>

</project-app>

<project-filter>
    <div class="col col-sm-4">
        <h3>Filter</h3>
        <span data-is="search-choice"
              multiple="1"
              label="Beneficiary"
              int=true
              func="anyOf"
              index="searchIndex"
              filter_table_index="beneficiary_s"
              filter_table="{db.Project}"
              related_table="{db.Beneficiary}"
              number_of_choices=8
        ></span>

        <span data-is="search-choice"
              multiple=1
              label="Sector"
              int=true
              func="anyOf"
              index="searchIndex"
              filter_table_index="sector_s"
              filter_table="{db.Project}"
              related_table="{db.Sector}"
              number_of_choices=8
        ></span>

        <span data-is="search-choice"
              multiple=1
              label="Activity"
              int=true
              func="anyOf"
              index="searchIndex"
              filter_table_index="activity_s"
              filter_table="{db.Project}"
              related_table="{db.Activity}"
              number_of_choices=8
        ></span>

        <span data-is="search-choice"
              multiple=1
              label="Organizations"
              int=true
              func="anyOf"
              index="name"
              filter_table_index="orgs"
              filter_table="{db.Project}"
              related_table="{db.Organization}"
              number_of_choices=8
        ></span>

        <span data-is="search-choice"
              multiple=1
              label="Status"
              func="anyOf"
              index="status"
              filter_table_index="status"
              display_property="description"
              filter_table="{db.Project}"
              related_table="{db.ProjectStatus}"
              number_of_choices=8
        ></span>
        <span data-is="search-input" label="Name" placeholder="By Name" func="startsWithIgnoreCase" index="name"></span>
    </div>


</project-filter>

<project-list>

    <project-filter/>

    <div class="col col-sm-8">
    <h3>List of Projects</h3>

    {object_name || 'Projects'} {filters.offset + 1} to {filters.offset + filters.limit + 1} of { filters.count }


    <div class="btn-group" role="group" aria-label="...">
      <button type="button" class="btn btn-default {active: filters.order_by=='name'}" onclick="{order_by_name}">Name</button>
      <button type="button" class="btn btn-default {active: filters.order_by=='startdate'}" onclick="{order_by_date}">Start Date</button>
    </div>

        <table ref='project_list_table' if={!loading} class='table table-condensed table-bordered table-striped'>
            <thead>
                <tr>
                    <th>Name</th>
                    <th>Organisations</th>
                    <th>Sector</th>
                    <th>Beneficiary</th>
                    <th>Activity</th>
                    <th>Dates</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr onclick="{detail}" each="{project in projects}">
                    <td data-is="translated-field" field="{project.name}"></td>
                    <td data-is="lookup-array" array="{project.orgs}" table="{db.Organization}" display_attribute="name"></td>
                    <td data-is="lookup-array" array="{project.sector_s}" table="{db.Sector}" display_attribute="name.en"></td>
                    <td data-is="lookup-array" array="{project.beneficiary_s}" table="{db.Beneficiary}" display_attribute="name.en"></td>
                    <td data-is="lookup-array" array="{project.activity_s}" table="{db.Activity}" display_attribute="name.en"></td>
                    <td>{project.startdate || ""} - {project.enddate || ""}</td>
                    <td data-is="lookup-value" lookupvalue="{project.status}" table="{db.ProjectStatus}" display_attribute="description"></td>
                </tr>
            </tbody>
        </table>

        <button onclick="{page.up}"> Up </button>
        <button onclick="{page.down}"> Down </button>
    </div>

    <style>
        h5 {color: blue;}

    </style>

    <script type="text/javascript">
        var tag = this;
        tag.opts.table = db.Project;
        tag.mixin('tableFilterMixin');
        tag.order_by='date';

        tag.order_by_date = function(){tag.filters.set_order_by('startdate'); tag.trigger('refresh_list')}
        tag.order_by_name = function(){tag.filters.set_order_by('name'); tag.trigger('refresh_list')}
        //tag.order_by_reverse = function(){tag.filters.reverse  = !tag.filters.reverse; tag.trigger('refresh_list')}

        tag.table = window.db.Project;
        tag.one('mount', function () {
            tag.filters.limit = tag.opts.limit || tag.filters.limit;
            tag.filters.offset = tag.opts.offset || tag.filters.offset;
            tag.trigger('refresh_list');
        });
        tag.on('refresh_list', function (opts) {
            _.extend(tag.filters, opts);
            var promiseArray = tag.filters.results();
            console.log(tag.filters);
            promiseArray.then(function(project_list) {
                $(tag.refs.project_list_table).fadeOut('fast', function(){
                    tag.update({loading: false, projects: project_list})
                $(tag.refs.project_list_table).fadeIn('fast')
                })
            })
        });

        tag.page = {};
        tag.page.up = function () {tag.trigger('refresh_list', {offset: tag.filters.offset + tag.filters.limit})};
        tag.page.down = function () {tag.trigger('refresh_list', {offset: tag.filters.offset - tag.filters.limit})};

        tag.detail = function(e){
              //tag.opts.table.get(_.toInteger(e.item.project.pk)).then(function(detail){
              //tag.parent.update({detail: detail})
              route('project/' + e.item.project.pk)

        }
    </script>
</project-list>

<translated-field>
    <p>{translatedString}<span class="small"> - {translationLanguage} </span></p>

    <script>
        var tag=this;

        tag.languages = _.get(window, 'languages', ['en','tet','ind','pt']);
        tag.set_language = undefined;
        tag.on('mount',function(){tag.trigger('setLanguage')});

        tag.on('setLanguage', function(){
            var translatedString;
            var translationLanguage;
            _.each(tag.languages, function(l) {
                translatedString = _.get(tag.opts.field, l);
                translationLanguage = l;
                if (translatedString) {
                    return false;
                }
            });
            tag.update({translatedString:translatedString,translationLanguage:translationLanguage})
        })


    </script>

</translated-field>

<lookup-value>

    <span if="{!resolved}">...<br></span>
    <span if="{resolved}">{resolved}<br></span>

    <script>
        var tag= this;

        function lookup_value() {
            return new Promise(function (resolve, reject) {
                tag.opts.table.where('pk').equals(tag.opts.lookupvalue).first()
                    .then(function (a) {
                        var r = _.get(a, tag.opts.display_attribute);
                        resolve(r);
                    }).catch(function (a) {
                    reject([]);
                });
            });
        }

        tag.on('mount', function(){
            lookup_value().then(function(r){tag.update({resolved:r})});
        })

    </script>

</lookup-value>

<lookup-array>
    <span if="{!resolved}" each="{pk in opts.array}">{pk}<br></span>
    <span if="{resolved}" each="{tag in resolved}">{tag}<br></span>

    <script>
        var tag= this;

        function lookup_array() {
            return new Promise(function (resolve, reject) {
                tag.opts.table.where('pk').anyOf(_.compact(tag.opts.array)).toArray()
                    .then(function (a) {
                        var r = _.map(a, tag.opts.display_attribute);
                        resolve(r);
                    }).catch(function (a) {
                    reject([]);
                });
            });
        }

        tag.on('mount', function(){
            lookup_array().then(function(r){tag.update({resolved:r})});
        })
    </script>
</lookup-array>

<project-detail>


    <div class="col col-sm-12">
        <h3>{detail.name}<span class="small"> Project Detail</span></h3>
        <h5>{detail.pk}</h5>

        <p ref="json">
        </p>
        <button onclick="{list}">Back to list</button>

    </div>

    <script>
        var tag = this;
        tag.detail = {name: '', pk:''}
        var detail;

        function onResolve(values) {
            _.each(values, function(v){_.set(detail, v[0], v[1])});
            tag.detail = detail;
            $(tag.refs.json).jsonViewer(detail);
        }

        function onReject(values){
            console.warn('Promise Errors');
            onResolve(values);
        }

        function lookup(value, table, lookup_attribute, display_attribute){
            if (_.isArray(value)){return lookup_array(value, table, lookup_attribute, display_attribute)}
            return new Promise(function (resolve) {
                table.where('pk').equals(value).first().then(function (a) {
                        var r = a[display_attribute];
                        resolve([lookup_attribute, r]);
                });
            });
        }

        function lookup_array(array, table, lookup_attribute, display_attribute) {
            return new Promise(function (resolve, reject) {
                table.where('pk').anyOf(_.compact(array)).toArray()
                    .then(function (a) {
                        var r = _.map(a, display_attribute);
                        resolve([lookup_attribute, r]);
                    }).catch(function (a) {
                    reject([lookup_attribute, []]);
                });
            });
        }

        tag.list = function(){
            route('project')
        };

        tag.on('route', function(pk){
              db.Project.get(_.toInteger(pk)).then(function(d) {
                  detail = d;
                  Promise.all([
                          lookup(d.activity_s, db.Activity, 'activity_s', 'name'),
                          lookup(d.sector_s, db.Sector, 'sector_s', 'name'),
                          lookup(d.orgs, db.Organization, 'orgs', 'name'),
                          lookup(d.beneficiary_s, db.Beneficiary, 'beneficiary_s', 'name'),
                          lookup(d.places, db.AdminArea, 'places', 'name'),
                          lookup(d.status, db.ProjectStatus, 'status', 'description')
                      ]
                  ).then(onResolve, onReject)
              });
        });

        tag.on('mount', function(){
            tag.opts.table = db.Project;
            tag.opts.pk = undefined;
            tag.d = {};
            tag.detail = {};
        })
    </script>
</project-detail>


<sector-name>

    <p if="{!s}">Looking up</p>
    <p if="{s}">{s}</p>
    <script>
        var tag =this;
        tag.on('before-mount', function(){
            var table = tag.opts.table || db.PropertyTag;
            var property = tag.opts.property || 'name';
            if (!tag.opts.table){tag.update({s:"Missing Table"}); return}
            tag.opts.table.get(_.toInteger(tag.opts.sector)).then(function(s){
                console.log(s);
                tag.update({s:_.get(s, property)})})
        });
    </script>
</sector-name>