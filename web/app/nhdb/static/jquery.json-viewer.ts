/**
* jQuery json-viewer
* @author: Alexandre Bodelot <alexandre.bodelot@gmail.com>
* @author: Joshua Brooks <josh.vdbroek@gmail.com>
*/
import _ = require('lodash');
import $ = require('jquery');

const url_regexp = /^(ftp|http|https):\/\/(\w+:?\w*@)?(\S+)(:[0-9]+)?(\/|\/([\w#!:.?+=&%@\-\/]))?/;

/**
* Check if arg is either an array with at least 1 element, or a dict with at least 1 key
*/
const isCollapsible = (arg: any ) : boolean => (_.isObject(arg) && _(arg).keys().size() > 0) || (_.isArray(arg) && _(arg).size() > 0);

/**
* Check if a string represents a valid url
*/
const isUrl = (s: string) : boolean => url_regexp.test(s);

/**
* Transform a json object into html representation
*/
const json2html = (json:any) : string =>  {
    let html : string = '';
    if (_.isString(json)) {
        json = json.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        if (isUrl(json)) { html += '<a href="' + json + '" class="json-string">' + json + '</a>'; } else { html += '<span class="json-string">"' + json + '"</span>'; }
    } else if (_.isNumber(json)) {
        html += '<span class="json-literal">' + json + '</span>';
    } else if (_.isBoolean(json)) {
        html += '<span class="json-literal">' + json + '</span>';
    } else if (_.isNull(json)) {
        html += '<span class="json-literal">null</span>';
    } else if (_.isArray(json)) {
        if (json.length > 0) {
            html += '[<ol class="json-array">';
            for (let i = 0; i < json.length; ++i) {
                html += '<li>';
                // Add toggle button if item is collapsable
                if (isCollapsible(json[i])) { html += '<a href class="json-toggle"></a>'; }

                html += json2html(json[i]);
                // Add comma if item is not last
                if (i < json.length - 1) { html += ','; }
                html += '</li>';
            }
            html += '</ol>]';
        } else {
            html += '[]';
        }
    } else if (typeof json === 'object') {
        let key_count = Object.keys(json).length;
        if (key_count > 0) {
            html += '{<ul class="json-dict">';
            for (let i in json) {
                if (json.hasOwnProperty(i)) {
                    html += '<li>';
                    // Add toggle button if item is collapsable
                    if (isCollapsible(json[i])) { html += '<a href class="json-toggle">' + i + '</a>'; } else { html += i; }

                    html += ': ' + json2html(json[i]);
                    // Add comma if item is not last
                    if (--key_count > 0) { html += ','; }
                    html += '</li>';
                }
            }
            html += '</ul>}';
        } else {
            html += '{}';
        }
    }
    return html;
};

/**
* jQuery plugin method
*/


$.fn.jsonViewer = function(json :string, options: object) {
    // jQuery chaining
    return this.each(function () {
        // Transform to HTML
        let html = json2html(json);
        if (isCollapsible(json)) { html = '<a href class="json-toggle"></a>' + html; }

        // Insert HTML in target DOM element
        $(this).html(html);

        // Bind click on toggle buttons
        $(this).off('click');
        $(this).on('click', 'a.json-toggle', function () {
            const target = $(this).toggleClass('collapsed').siblings('ul.json-dict, ol.json-array');
            target.toggle();
            if (target.is(':visible')) {
                target.siblings('.json-placeholder').remove();
            } else {
                const count = target.children('li').length;
                const placeholder = count + (count > 1 ? ' items' : ' item');
                target.after('<a href class="json-placeholder">' + placeholder + '</a>');
            }
            return false;
        });

        // Simulate click on toggle button when placeholder is clicked
        $(this).on('click', 'a.json-placeholder', function () {
            $(this).siblings('a.json-toggle').click();
            return false;
        });

        if (_.isObject(options) && _.get(options, 'collapsed', false)) {
            // Trigger click to collapse all nodes
            $(this).find('a.json-toggle').click();
        }
    });
};