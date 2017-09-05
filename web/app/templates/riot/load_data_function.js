function loaddata(db, data) {
    _.each(data, function (dataset, tablename) {
        db[tablename].bulkPut(dataset.data.created).catch(Dexie.BulkError, function (e) {
            // Explicitly catching the bulkAdd() operation makes those successful
            // additions commit despite that there were errors.
            console.error ("Some database PUTs did not succeed." + e.failures.length + 'failed in ' + tablename);
        }).catch(Dexie.DataError, function(e){
            tablename;
            dataset;

            debugger});

        db[tablename].bulkPut(dataset.data.updated).catch(Dexie.BulkError, function (e) {
            // Explicitly catching the bulkAdd() operation makes those successful
            // additions commit despite that there were errors.
            console.error ("Some database PUTs did not succeed." + e.failures.length + 'failed in ' + tablename);
        }).catch(Dexie.DataError, function(e){debugger});

    });
}