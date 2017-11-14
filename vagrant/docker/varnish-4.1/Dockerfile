FROM ubuntu:12.04
RUN \
  apt-get -y update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y apt-transport-https curl && \
  curl -L https://packagecloud.io/varnishcache/varnish41/gpgkey | apt-key add - && \
  apt-key adv --keyserver keyserver.ubuntu.com --recv-keys FDBCAE9C0FC6FD2E && \
  echo "deb https://packagecloud.io/varnishcache/varnish41/ubuntu/ precise main" >> /etc/apt/sources.list.d/varnishcache_varnish41.list && \
  apt-get -y update && \
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
