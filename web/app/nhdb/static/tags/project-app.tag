<project-app>
    <router>
        <route path="list"><project-list ref="project_list"/></route>
        <route path="project/*"><project-detail/></route>
        <route path="edit/*"><project-edit/></route>
    </router>
    <script>
        var tag = this;

        tag.on('mount', function(){
            window['project_app'] = tag;

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

<project-list>
    <project-filter/>
    <div class="col col-sm-8">
    <h3>List of Projects </h3>
        <ul>
            <li>This needs to keep its order and filtering when I go to a detail and back</li>
        </ul>
    {object_name || 'Projects'} {filters.offset + 1} to {filters.offset + filters.limit + 1} of { filters.count }

    <div class="btn-group" role="group" aria-label="...">
      <button each="{index, label in order_by_options}" type="button" class="btn btn-default {active: filters.order_by==index}" onclick="{order_by_index}">{label}</button>
    </div>

        <div each="{project in projects}">
            <hr/>
            <a href="#project/{project.pk}"><h4 data-is="translated-field" field="{project.name}"></h4></a>
            <hr/>
            <table class="table table-bordered table-compact">
                <tbody>

                <tr>
                    <td>Organizations</td>
                    <td><span data-is="lookup-array" array="{project.orgs}" table="{db.Organization}" display_attribute="name"></span></td>
                </tr>

                <tr>
                    <td>Sectors</td>
                    <td><span data-is="lookup-array" array="{project.sector_s}" table="{db.Sector}" display_attribute="name.en"></span></td>
                </tr>

                <tr>
                    <td>Beneficiary</td>
                    <td><span data-is="lookup-array" array="{project.beneficiary_s}" table="{db.Beneficiary}" display_attribute="name.en"></span></td>
                </tr>

                <tr>
                    <td>Activity</td>
                    <td><span data-is="lookup-array" array="{project.activity_s}" table="{db.Activity}" display_attribute="name.en"></span></td>
                </tr>

                <tr>
                    <td>Timespan</td>
                    <td><span>{project.startdate || ""} - {project.enddate || ""}</span></td>
                </tr>

                <tr>
                    <td>Status</td>
                    <td><span data-is="lookup-value" lookupvalue="{project.status}" table="{db.ProjectStatus}" display_attribute="description"></span></td>
                </tr>

                </tbody>
            </table>
        </div>

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
        tag.mixin('tagExtensions');
        tag.order_by='date';

        tag.order_by_options = {'Name': 'name.en', 'Start Date': 'startdate', 'End Date': 'enddate'};

        tag.order_by_index = function(e){tag.filters.set_order_by(e.item.index); tag.trigger('refresh_list')};
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
            promiseArray.then(function(project_list) {
                tag.update({loading: false, projects: project_list});
            })
        });

        tag.page = {};
        tag.page.up = function () {tag.trigger('refresh_list', {offset: tag.filters.offset + tag.filters.limit})};
        tag.page.down = function () {tag.trigger('refresh_list', {offset: tag.filters.offset - tag.filters.limit})};

    </script>
</project-list>

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
        <span data-is="search-input" label="Name" placeholder="By Name" func="startsWithIgnoreCase" index="searchIndex"></span>
    </div>
</project-filter>

<project-detail>
    <div class="col col-sm-12">
        <h3>{detail.name.en}<span class="small"> Project Detail</span></h3>
        <h5>{detail.pk}</h5>
        <a href="#edit/{detail.pk}">Edit</a>

        <h4>Name</h4>
        <p each="{description, language in detail.name}">
            {description} <span class="small">({language})</span>
        </p>

        <h4>Description</h4>
        <p each="{description, language in detail.description}">
            {description} <span class="small">({language})</span>
        </p>

        <h4>Beneficiaries</h4>
        <p each="{tag in detail.beneficiary_s}">
            <span each="{description, language in tag}" if="{language == (window.CURRENT_LANGUAGE || 'en')}">
                {description}
            </span>
        </p>

        <h4>Activities</h4>
        <p each="{tag in detail.activity_s}">
            <span each="{description, language in tag}" if="{language == (window.CURRENT_LANGUAGE || 'en')}">
                {description}
            </span>
        </p>

        <h4>Sectors</h4>
        <p each="{tag in detail.sector_s}">
            <span each="{description, language in tag}" if="{language == (window.CURRENT_LANGUAGE || 'en')}">
                {description}
            </span>
        </p>

        <!--This is developer info -->
        <hr/>
        <ul>
            <li>Add places (map)</li>
            <li>Add "Who is involved" - (organisations)</li>
            <li>Add ProjectImages</li>
        </ul>
        <p ref="json">
        <hr/>
        <!-- End of developer info -->
        </p>
        <button onclick="{list}">Back to list</button>

    </div>

    <script>
        var tag = this;
        tag.detail = {name: '', pk:''}
        var detail;

        tag.list = function(){
            route('project')
        };

        tag.on('route', function(pk){

            function lookup(value, table, lookup_attribute, display_attribute) {

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

                if (_.isArray(value)) {
                    return lookup_array(value, table, lookup_attribute, display_attribute)
                }
                return new Promise(function (resolve) {
                    table.where('pk').equals(value).first().then(function (a) {
                        var r = a[display_attribute];
                        resolve([lookup_attribute, r]);
                    });
                });
            }

            function onResolve(values) {
                _.each(values, function(v){_.set(detail, v[0], v[1])});
                tag.update({detail:detail});
                $(tag.refs.json).jsonViewer(detail);
            }

            function onReject(values){
                console.warn('Promise Errors');
                onResolve(values);
            }

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

<project-edit>
    <p>Hello World</p>

    <span>pk</span>
    <a href="#project/{pk}">Back to Profile</a>

    <textarea-translatedtext if={pk} table="{db.Project}" field="name" pk="{pk}"></textarea-translatedtext>
    <textarea-translatedtext if={pk} table="{db.Project}" field="description" pk="{pk}"></textarea-translatedtext>
    <ul>
        <li>Create a widget to edit JSON text of title, description, notes</li>
        <li>Create a widget to edit array like beneficiary, sector, activity</li>
        <li>Create a widget to edit timeframe</li>
    </ul>

    <script type="text/javascript">

        var tag = this;
        var detail;

        tag.on('route', function(pk){

            tag.pk = pk;

            function lookup(value, table, lookup_attribute, display_attribute) {

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

                if (_.isArray(value)) {
                    return lookup_array(value, table, lookup_attribute, display_attribute)
                }
                return new Promise(function (resolve) {
                    table.where('pk').equals(value).first().then(function (a) {
                        var r = a[display_attribute];
                        resolve([lookup_attribute, r]);
                    });
                });
            }

            function onResolve(values) {
                _.each(values, function(v){_.set(detail, v[0], v[1])});
                tag.update({detail:detail});
                $(tag.refs.json).jsonViewer(detail);
            }

            function onReject(values){
                console.warn('Promise Errors');
                onResolve(values);
            }

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

    </script>

</project-edit>