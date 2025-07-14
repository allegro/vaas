FROM varnish:7.7

USER root

ADD ./entrypoint /entrypoint
ADD ./secret /etc/varnish/secret

RUN chmod +x /entrypoint
RUN chmod 600 /etc/varnish/secret


CMD ["/entrypoint"]
