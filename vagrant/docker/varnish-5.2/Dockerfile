FROM ubuntu:16.04
RUN \
  apt-get -y update && \
  apt-get install -y apt-transport-https curl gnupg && \
  curl -L https://packagecloud.io/varnishcache/varnish52/gpgkey | apt-key add - && \
  echo "deb https://packagecloud.io/varnishcache/varnish52/ubuntu/ xenial main" >> /etc/apt/sources.list.d/varnishcache_varnish52.list && \
  apt-get -y update &&\
  apt-get install -y monit varnish && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*
ADD ./start /start
ADD ./monitrc /etc/monitrc
ADD ./secret /etc/varnish/secret
ADD ./varnish /etc/default/varnish
RUN chmod +x /start
RUN chmod 600 /etc/monitrc /etc/varnish/secret
CMD ["/start"]
