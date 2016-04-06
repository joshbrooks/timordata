USERIP=$(nmblookup USER-HP|awk '{print substr($1,1)}')
DOCKERPORT=$(docker inspect --format='{{range $p, $conf := .NetworkSettings.Ports}}{{if eq $p "3306/tcp"}}{{(index $conf 0).HostPort}}{{end}} {{end}}' timordata_source_1)
mysqldump -h $USERIP -ujosh -pd1atheke --opt -d -B development > /tmp/dbserver_schema.sql
mysqldump -h $USERIP -ujosh -pd1atheke --quick --single-transaction -t -n -B development > /tmp/dbserver_data.sql
mysql -P$DOCKERPORT -h127.0.0.1 -uroot -pduck < /tmp/dbserver_schema.sql
mysql -P$DOCKERPORT -h127.0.0.1 -uroot -pduck < /tmp/dbserver_data.sql
