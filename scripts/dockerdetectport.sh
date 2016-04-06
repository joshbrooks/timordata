#!/bin/bash
set -o nounset
set -o errexit
function resolvePort() {
  local container=$1
  local exposedPort=$2
  local port=$(docker inspect --format='{{range $p, $conf := .NetworkSettings.Ports}}{{if eq $p "'$exposedPort'/tcp"}}{{(index $conf 0).HostPort}}{{end}} {{end}}' $container)
  echo $port
}
