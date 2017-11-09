import * as riot from 'riot';
import 'project-tags';
import 'riot-filters';
import 'database';
import route = require('riot-route');
import './jquery.json-viewer.js';
import './tag-extensions.js';
window['route'] = route;
riot.mount('project-app');
