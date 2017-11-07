/* globals db, src, Dexie, $, _ */

let consoleLogError = (e) => console.error('Some database PUTs did not succeed.' + e.failures.length + 'failed in ' + tablename);

let loaddata = (db : Table, data: object) => {
    let promises = [];
    _.each(data, (dataset : object, tablename : string) => {
        let createP : Promise;
        let updateP : Promise;
        let deleteP : Promise; // TODO: Promise removes matching values
        createP = db[tablename].bulkPut(dataset.data.created).catch(Dexie.BulkError, (e) => { consoleLogError(e); });
        updateP = db[tablename].bulkPut(dataset.data.updated).catch(Dexie.BulkError, (e) => { consoleLogError(e); });
        promises.push(createP);
        promises.push(updateP);
    });
    return Promise.all(promises);
};

db.settings.get('lastupdated').then((lastupdated) => {
    $.getJSON(src, { timestamp: _.get(lastupdated, 'value', 0) }).then((objects) => {
        let promises = loaddata(db, objects);
        promises.then(() => {});
    });
});