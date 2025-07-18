FROM varnish:6.0.14

USER root

ADD ./entrypoint /entrypoint
ADD ./secret /etc/varnish/secret

RUN chmod +x /entrypoint
RUN chmod 600 /etc/varnish/secret

CMD ["/entrypoint"]
