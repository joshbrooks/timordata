import Dexie from "dexie";
import _ = require('lodash');
import $ = require('jquery');

const src='/nhdb/project/database.js';
const languages = ['en', 'pt', 'tet', 'ind'];
const translated_idx = _.join(_.map(languages, function(i){return 'name.'+i}), ', ')

const stores = {'0.1': {
 "Activity": "pk, *searchIndex, " + translated_idx,
 "AdminArea": "pk, path, name",
 "OrganizationClass": "pk, code, orgtype",
 "Beneficiary": "pk, name, *searchIndex",
 "settings": "key, value",
 "ProjectStatus": "pk, code, description",
 "ProjectOrganization": "pk, project__pk, organization, organizationclass",
 "Person": "pk, name, title, organization",
 "Project": "pk, description, startdate, enddate, *orgs, status, places, *sector_s, *activity_s, *beneficiary_s, *searchIndex, " + translated_idx,
 "Organization": "pk, name",
 "Sector": "pk, name, *searchIndex",
 "ProjectPerson": "pk, project, person, is_primary"
}};

interface IActivity {pk: number, name?: string, searchIndex?: string[]}
interface IAdminArea {pk: number, path?: string, name?: string}
interface IOrganizationClass {pk: number}
interface IBeneficiary {pk: number, searchIndex?: string[]}
interface ISettings {pk: number,}
interface IProjectStatus {pk: number}
interface IProjectOrganization {pk: number}
interface IPerson {pk: number}
interface IProject {pk: number, searchIndex?: string[]}
interface IOrganization {pk: number}
interface ISector {pk: number, searchIndex?: string[]}
interface IProjectPerson {pk: number, project:number, person:number, is_primary:boolean}

class ApplicationDatabase extends Dexie {
    Activity: Dexie.Table<IActivity, number>;
    AdminArea: Dexie.Table<IAdminArea, number>;
    OrganizationClass: Dexie.Table<IOrganizationClass, number>;
    Beneficiary: Dexie.Table<IBeneficiary, number>;
    settings: Dexie.Table<ISettings, string>;
    ProjectStatus: Dexie.Table<IProjectStatus, number>;
    ProjectOrganization: Dexie.Table<IProjectOrganization, number>;
    Person: Dexie.Table<IPerson, number>;
    Project: Dexie.Table<IPerson, number>;
    Organization: Dexie.Table<IOrganization, number>;
    Sector: Dexie.Table<ISector, number>;
    ProjectPerson: Dexie.Table<IProjectPerson, number>;

    constructor() {
        super('ApplicationDatabase');
        this.version(0.1).stores(stores['0.1'])
    }
}

const db = new ApplicationDatabase();

/* Return an object field into separate words */
// const words = (object: object, field_name: string) => _.split(_.get(object, field_name));

const objectwords = (object: object, field_name: string) => {
    /* Return values from an object split into individual words */
    /* Use where a 'name' object has translated strings as values */
        let words : string[] = _.values (_.get(object, field_name)).join(' ').split(' ');
        words = _.map(words, function(word){return _.replace(word, /[\W\(\)]/g, '')});
        words = _.filter(words, function(word){return _.size(word) > 3});
        return words;
};

db.Activity.hook('creating', (primKey?: number, obj?: IActivity) => { obj.searchIndex = objectwords(obj, 'name');});
db.Beneficiary.hook('creating', (primKey?, obj?:IBeneficiary) => { obj.searchIndex = objectwords(obj, 'name'); });
db.Sector.hook('creating', (primKey?, obj?:ISector) => { obj.searchIndex = objectwords(obj, 'name'); });
db.Project.hook('creating', (primKey?, obj?:IProject) => { obj.searchIndex = objectwords(obj, 'name'); });

db.Activity.hook('updating', (modifications: object, primKey?: number, obj?: IActivity) => {if (!_.isUndefined(modifications.name)) {return {searchIndex: objectwords(modifications, 'name')}}});
db.Beneficiary.hook('updating', (modifications: object, primKey?, obj?:IBeneficiary) => {if (!_.isUndefined(modifications.name)) {return {searchIndex: objectwords(modifications, 'name')}}});
db.Sector.hook('updating', (modifications: object, primKey?, obj?:ISector) => {if (!_.isUndefined(modifications.name)) {return {searchIndex: objectwords(modifications, 'name')}}});
db.Project.hook('updating', (modifications: object, primKey?, obj?:IProject) => {if (!_.isUndefined(modifications.name)) {return {searchIndex: objectwords(modifications, 'name')}}});



let consoleLogError = (e, tablename : string) => console.error('Some database PUTs did not succeed.' + e.failures.length + 'failed on '+tablename);

let loaddata = (db : ApplicationDatabase, data: object) => {
    let promises = [];
    _.each(data, (dataset : object, tablename : string) => {
        let createP : Promise<any>;
        let updateP : Dexie.Promise<any>;
        let deleteP : Dexie.Promise<any>; // TODO: Promise removes matching values
        createP = db[tablename].bulkPut(dataset['data']['created']).catch(Dexie.BulkError, (e) => { consoleLogError(e, tablename); });
        updateP = db[tablename].bulkPut(dataset['data']['updated']).catch(Dexie.BulkError, (e) => { consoleLogError(e, tablename); });
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

window['db'] = db;
console.log(db);