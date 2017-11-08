require.config({
    baseUrl: "/static/",
    paths: {
        "dexie": "dexie/dist/dexie",
        jquery: "jquery/dist/jquery.min",
        "lodash": "lodash/lodash.min",
        "riot": "riot/riot.min",
        "route": "riot-route/dist/amd.route+tag",
        "project-tags": "tags/project-tags",
        "riot-filters": "nhdb/riot-filters",
        "database": "database",
        'jsonviewer': 'json-viewer'
    }
});

requirejs(['/static/project.js']);
