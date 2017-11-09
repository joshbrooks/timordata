require.config({
    baseUrl: "/static/",
    paths: {
        "dexie": "dexie/dist/dexie",
        jquery: "jquery/dist/jquery.min",
        "lodash": "lodash/lodash.min",
        "riot": "riot/riot.min",
        "riot-route": "riot-route/dist/amd.route+tag",
        "project-tags": "tags/project-tags",
    }
});

requirejs(['/static/project.js']);
