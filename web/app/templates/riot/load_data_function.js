function loaddata(db, data) {
    _.each(data, function (dataset, tablename) {
        console.log(tablename, dataset);
        db[tablename].bulkPut(dataset.data).catch(Dexie.BulkError, function (e) {
            // Explicitly catching the bulkAdd() operation makes those successful
            // additions commit despite that there were errors.
            console.error ("Some database PUTs did not succeed." + e.failures.length + 'failed in ' + tablename);
        });
    });
}