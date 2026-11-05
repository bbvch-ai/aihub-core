FROM alpine:3.23
RUN apk add --no-cache squid=7.6-r0 \
 && for template in /usr/share/squid/errors/templates/ERR_*; do : > "$template"; done
COPY squid.conf /etc/squid/squid.conf
# Started as root, Squid drops to its own user before opening its logs and then cannot open /dev/stdout.
USER squid
EXPOSE 3128
CMD ["squid", "-N", "-d", "1", "-f", "/etc/squid/squid.conf"]
