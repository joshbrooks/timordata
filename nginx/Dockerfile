FROM ubuntu:latest

MAINTAINER Joshua Brooks "josh.vdbroek@gmail.com"
ENV DEBIAN_FRONTEND=noninteractive

# explicitly set user/group IDs
RUN groupadd -r postgres --gid=999 && useradd -r -g postgres --uid=999 postgres

# Use docker host's apt-cache-ng server (if built on a host with apt-cache)
RUN route -n | awk '/^0.0.0.0/ {print $2}' > /tmp/host_ip.txt; nc -zv `cat /tmp/host_ip.txt` 3142 &> /dev/null && if [ $? -eq 0 ]; then echo "Acquire::http::Proxy \"http://$(cat /tmp/host_ip.txt):3142\";" > /etc/apt/apt.conf.d/30proxy; echo "Proxy detected on docker host - using for this build"; fi
RUN apt-get update && apt-get install -y nginx && apt-get clean && rm -rf /var/lib/apt/lists/*
RUN if [ -f "/etc/apt/apt.conf.d/30proxy" ]; then rm /etc/apt/apt.conf.d/30proxy; fi

RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN rm /etc/nginx/sites-enabled/default
ADD sites-enabled/ /etc/nginx/sites-enabled
RUN mkdir -p /etc/letsencrypt/live/timordata.info/
ADD certs/ /etc/letsencrypt/live/timordata.info/

EXPOSE 80 443

CMD ["/usr/sbin/nginx"]

