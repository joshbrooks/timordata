docker run -d --name some-nginx -P -v `pwd`/sockets:/sockets -v `pwd`/default.conf:/etc/nginx/conf.d/default.conf nginx
