/* global db */
/* Functions to create indexes */
function words(object, field_name) {
    /* Return an object field into separate words */
    return _.split(_.get(object, field_name));
}

function objectwords(object, field_name) {
    /* Return values from an object split into individual words */
    /* Use where a 'name' object has translated strings as values */
    var strings = _.values(_.get(object, field_name));
    var w = _.map(strings, function (thestring) { return _.split(thestring); });
    return _.flatten(w);
}


db.Activity.hook('creating', function (primKey, obj) { obj.searchIndex = objectwords(obj, 'name'); });
db.Beneficiary.hook('creating', function (primKey, obj) { obj.searchIndex = objectwords(obj, 'name'); });
db.Sector.hook('creating', function (primKey, obj) { obj.searchIndex = objectwords(obj, 'name'); });
db.Project.hook('creating', function (primKey, obj) { obj.searchIndex = objectwords(obj, 'name'); });
