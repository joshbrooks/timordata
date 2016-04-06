#!/usr/bin/env bash

APPDIR='/home/django/app'
HOME='/home/django/'
ENV='/home/django/env/bin/activate'

source $ENV
cd $APPDIR

NAME="timordata.info"
USER=belun
PASSWORD=L1terary20@
set PGPASSWORD="L1terary20@"
HOST=db
TODAY=$(date +%Y%m%d_%H%M%S)

echo "$HOST:5432:$NAME:$USER:$PASSWORD" > $HOME/'.pgpass'
echo "$HOST:5432:postgres:$USER:$PASSWORD" >> $HOME/'.pgpass'
chmod 600 ~/.pgpass
#DIRBACKUPS="/home/josh/backups/${TODAY}"
#mkdir -p ${DIRBACKUPS}
#
#
#
#function backup {
#
#    local NAME=timordata.info
#    local USER=django
#    local PASSWORD=L1terary20@
#    local HOST=localhost
#    local initialdatanhdb=$APPDIR"/nhdb/fixtures/initial_data.json"
#    local initialdatageo=$APPDIR"/geo/fixtures/initial_data.json"
#    mkdir -p ${DIRBACKUPS}/fixtures/nhdb
#    mkdir -p ${DIRBACKUPS}/fixtures/geo
#
#    pg_dump -F c -h $HOST -U $USER $NAME -f ${DIRBACKUPS}/timordata.pgdump
#
#    cd /webapps/project/belun/
#    ./manage.py dumpdata nhdb.propertytag nhdb.projectstatus nhdb.organizationclass nhdb.projectstatus nhdb.projectorganizationclass nhdb.projecttype nhdb.recordowner nhdb.organizationclass > ${DIRBACKUPS}/fixtures/nhdb/initial_data.json
#    ./manage.py dumpdata geo > ${DIRBACKUPS}/fixtures/geo/initial_data.json
#
#}

function reset {

    cd $APPDIR
    # Resets the database to initial state
    psql -h $HOST -d postgres --user $USER -c "DROP DATABASE \"${NAME}\";"
    psql -h $HOST -d postgres --user $USER -c "CREATE DATABASE \"${NAME}\";"
    psql -h $HOST -d $NAME --user $USER -c "CREATE EXTENSION postgis;"
    ./manage.py migrate
    ./manage.py makemigrations
    ./manage.py migrate --run-syncdb
    # ./manage.py loaddata /webapps/project/belun/nhdb/fixtures/_initial_data.json
    # ./manage.py loaddata /webapps/project/belun/geo/fixtures/_initial_data.json.gz
    psql -h $HOST -d $NAME --user $USER -f $APPDIR"/nhdb/fixtures/sql/geo_adminarea.copy"
    psql -h $HOST -d $NAME --user $USER -f $APPDIR"/nhdb/fixtures/sql/geo_suco.copy"
    psql -h $HOST -d $NAME --user $USER -f $APPDIR"/nhdb/fixtures/sql/geo_subdistrict.copy"
    psql -h $HOST -d $NAME --user $USER -f $APPDIR"/nhdb/fixtures/sql/geo_district.copy"
    psql -h $HOST -d $NAME --user $USER -f $APPDIR"/nhdb/fixtures/sql/nhdb_propertytag.copy"
}

function flush {
    cd $APPDIR
    ./manage.py flush
}
function getnhdbdata {
    # Python script to load data from Belun's mysql database
    echo "Loading Python data from USER-HP"
    cd $APPDIR
    ./manage.py loaddata ./nhdb/fixtures/initial_data.json
    ./manage.py loaddata ./geo/fixtures/initial_data.json
    cd nhdb
    python mysqldb.py
    cd $APPDIR
}

function getlibrarydata {
    # This connects to the timordata.info site and gets a copy of the organization ID's and names as used by the library
    # In some cases these will be different to the local site - this allows to make sure the names are consistent
    # Note you may need to edit the hba.conf file to allow connection and restart the server!

    psql -h timordata.info -d 'timordata.info' --user belun -c "
    DROP TABLE IF EXISTS library_publication_organization_temp;
    CREATE TABLE library_publication_organization_temp
            (publication_id int, name varchar(256), organization_name varchar(256));
        INSERT INTO library_publication_organization_temp ( publication_id, name, organization_name)
            SELECT p.id, p.name, o.name
                FROM library_publication p, nhdb_organization o, library_publication_organization po
                WHERE po.organization_id = o.id AND po.publication_id = p.id;"

        #copy library_publication_organization_temp to '/tmp/library_publication_organization_temp.tab';"


    ssh -p 81 timordata.info "pg_dump --host localhost --user belun --data-only -t 'public.library*' -T 'public.library_publication_organization' timordata.info > ~/library.data"
    scp -P 81 josh@timordata.info:/home/josh/library.data /tmp/
    scp -P 81 josh@timordata.info:/tmp/library_publication_organization_temp.tab /tmp/
    psql -U belun -h localhost -d timordata.info < /tmp/library.data

    # Run manage.py to reset serial numbers
    cd $APPDIR
   ./manage.py sqlsequencereset nhdb library | psql -h $HOST -d $NAME --user $USER
    psql -h $HOST -d $NAME --user $USER -c "
    CREATE TABLE library_publication_organization_temp
        (publication_id int, name varchar(256), organization_name varchar(256));
    INSERT INTO library_publication_organization_temp ( publication_id, name, organization_name)
        SELECT p.id, p.name, o.name
            FROM library_publication p, nhdb_organization o, library_publication_organization po
            WHERE po.organization_id = o.id AND po.publication_id = p.id;
    copy library_publication_organization_temp from '/tmp/library_publication_organization_temp.tab';

    -- Populate the Organization table with any missing values

    INSERT INTO nhdb_organization(name, active, orgtype_id)
        SELECT DISTINCT organization_name, True, 'None'
            FROM library_publication_organization_temp
            WHERE library_publication_organization_temp.organization_name NOT IN (SELECT name FROM nhdb_organization);

    -- Create links in the library_publication_organization table
    INSERT INTO library_publication_organization (publication_id, organization_id)
        SELECT DISTINCT library_publication.id, nhdb_organization.id
            FROM nhdb_organization, library_publication, library_publication_organization_temp
            WHERE nhdb_organization.name = library_publication_organization_temp.organization_name
            AND library_publication.name = library_publication_organization_temp.name;
    "
}

#function getauth {
#    # Connect to timordata.info and get user names and passwords
#    echo "Getting AUTH data from timordata site"
#    ssh -p 81 timordata.info "pg_dump --host localhost --user belun --data-only -t 'public.auth*' django > ~/auth.data"
#    scp -P 81 josh@timordata.info:/home/josh/auth.data /tmp/
#    psql -U belun -h localhost -d timordata.info -c "TRUNCATE TABLE auth_group CASCADE; TRUNCATE TABLE auth_group_permissions CASCADE; TRUNCATE TABLE auth_permission CASCADE; TRUNCATE TABLE auth_user CASCADE; TRUNCATE TABLE auth_user_groups CASCADE;  TRUNCATE TABLE auth_user_user_permissions CASCADE;"
#    psql -U belun -h localhost -d timordata.info < /tmp/auth.data
#}

function getdonormapping {
    # Connect to timordata.info and get donor mapping data
    echo "Getting Donor Mapping data from timordata site"
    ssh -p 81 timordata.info "pg_dump --host localhost --user belun --data-only -t 'public.donormapping*' django > ~/donormapping.data"
    scp -P 81 josh@timordata.info:/home/josh/donormapping.data /tmp/
    psql -U belun -h localhost -d timordata.info < /tmp/donormapping.data
}



function makeexport {
    echo "Creating export of ALL data except geo.* tables to load to timordata.info site"
#    pg_dump --host localhost --user belun -T 'public.geo*' -T 'auth.*' timordata.info > ${DIRBACKUPS}/export.data
    pg_dump --host $HOST --user $USER -T 'public.geo*' -T 'auth.*' --data-only $NAME > ${DIRBACKUPS}/data-only-export.data
}

#sudo service nginx stop && sudo service supervisor stop && sudo service postgresql stop

function flushserver {
    # Runs the SQL "flush" command
    ssh -p 81 timordata.info "
    cd /webapps/project/belun/
    ./manage.py sqlflush > /tmp/flush.sql
    psql -h $HOST -d $NAME --user $USER -f /tmp/flush.sql
    "
#    ./manage.py loaddata /webapps/project/belun/nhdb/fixtures/_initial_data.json
#    ./manage.py loaddata /webapps/project/belun/geo/fixtures/_initial_data.json.gz

}

function loadexport {
    # Transmit data to the server and load it up
#    ssh -p 81 timordata.info "
#    cd /webapps/project/belun/
#    ./manage.py loaddata /webapps/project/belun/geo/fixtures/_initial_data.json.gz
#    "
    rsync -avz -e 'ssh -p 81' --progress ${DIRBACKUPS}/export.data timordata.info:/tmp/export.data
#    ssh -p 81 timordata.info "psql -U belun -h localhost -d timordata.info < /tmp/export.data"
}
# backup
# reset
flush
getnhdbdata
# getlibrarydata
# getdonormapping
# makeexport

#flushserver
#loadexport

#sudo service nginx restart && sudo service supervisor restart && sudo service postgresql restart
