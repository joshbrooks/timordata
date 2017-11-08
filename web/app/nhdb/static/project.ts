import * as riot from 'riot';
import 'project-tags';
import 'riot-filters';
import 'database';
import route = require('route');
import jsonviewer = require('json-viewer');
window['jsonviewer'] = jsonviewer;
window['route'] = route;
riot.mount('project-app');
