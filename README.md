# TimorData Repository

## Stack

 - postgresql
 - python
 - django
 - riotjs
 - requirejs
 - typescript


## Development

In development,

 - Use 'tsc' to compile typescript when a typescript file is edited

```
# riot watcher
REPO=/home/josh/github/joshbrooks/timordata; APP=web/app; cd ${REPO}/${APP}/nhdb/static; ${REPO}/${APP}/node_modules/riot/node_modules/.bin/riot -m -w . tags/project_tags.js

``` bash
# tsc watcher
REPO=/home/josh/github/joshbrooks/timordata
APP=web/app
cd ${REPO}/${APP}/nhdb/static
${REPO}/${APP}/node_modules/typescript/bin/tsc -w
```

``` bash
# Runserver
virtualenv_name="timordata_env"
workon ${virtualenv_name}
REPO=/home/josh/github/joshbrooks/timordata
APP=web/app
cd ${REPO}/${APP}
./manage.py runserver
```
