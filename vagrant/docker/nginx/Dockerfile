FROM ubuntu:12.04
RUN \
  apt-get update && \
  apt-get install -y python-software-properties && \
  add-apt-repository -y ppa:nginx/stable && \
  apt-get update && \
  apt-get install -y nginx && \
  echo "\ndaemon off;" >> /etc/nginx/nginx.conf && \
  sed -ri 's/(worker_processes )4;/\11;/' /etc/nginx/nginx.conf && \
  chown -R www-data:www-data /var/lib/nginx && \
  touch /usr/share/nginx/html/ts.1 && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*
WORKDIR /etc/nginx
CMD ["nginx"]
