docker run -d \
	--name some-nginx -P \
	-v /tmp/static:/usr/share/nginx/html/static \
	-v /tmp/media:/usr/share/nginx/html/media \
	-v `pwd`/sockets:/sockets \
	-v `pwd`/default.conf:/etc/nginx/conf.d/default.conf \
	nginx
