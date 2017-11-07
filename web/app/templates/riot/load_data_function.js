/* globals db, src, Dexie, $, _ */
var consoleLogError = function (e) { return console.error('Some database PUTs did not succeed.' + e.failures.length + 'failed in ' + tablename); };
var loaddata = function (db, data) {
    var promises = [];
    _.each(data, function (dataset, tablename) {
        var createP;
        var updateP;
        var deleteP; // TODO: Promise removes matching values
        createP = db[tablename].bulkPut(dataset.data.created).catch(Dexie.BulkError, function (e) { consoleLogError(e); });
        updateP = db[tablename].bulkPut(dataset.data.updated).catch(Dexie.BulkError, function (e) { consoleLogError(e); });
        promises.push(createP);
        promises.push(updateP);
    });
    return Promise.all(promises);
};
db.settings.get('lastupdated').then(function (lastupdated) {
    $.getJSON(src, { timestamp: _.get(lastupdated, 'value', 0) }).then(function (objects) {
        var promises = loaddata(db, objects);
        promises.then(function () { });
    });
});
