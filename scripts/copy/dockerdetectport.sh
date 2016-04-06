port=$(docker inspect --format='{{range $p, $conf := .NetworkSettings.Ports}}{{if eq $p "5432/tcp"}}{{(index $conf 0).HostPort}}{{end}} {{end}}' timordata_db_1)
psql 
