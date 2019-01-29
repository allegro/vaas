FROM ubuntu:18.04
RUN \
  apt-get -y update && \
  apt-get install -y curl && \
  curl -s https://packagecloud.io/install/repositories/varnishcache/varnish60lts/script.deb.sh | bash && \
  apt-get install -y monit varnish && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*
ADD ./init.d/varnish /etc/init.d/varnish
ADD ./start /start
ADD ./monitrc /etc/monitrc
ADD ./secret /etc/varnish/secret
ADD ./varnish /etc/default/varnish
RUN chmod +x /start
RUN chmod 600 /etc/monitrc /etc/varnish/secret
CMD ["/start"]
