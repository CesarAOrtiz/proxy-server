# Usa Debian como base
FROM debian:latest

# Instalar Squid, Tor, Privoxy, netcat y jq para JSON
RUN apt update && apt install -y \
    squid tor privoxy curl && \
    rm -rf /var/lib/apt/lists/*

# Copiar configuraciones personalizadas
COPY squid.conf /etc/squid/squid.conf
COPY privoxy.config /etc/privoxy/config
COPY torrc /etc/tor/torrc
COPY check_ip.sh /check_ip.sh

# Exponer el puerto del proxy Squid
EXPOSE 3128

# Iniciar Tor, Privoxy y Squid, luego ejecutar el script de validación
CMD service tor restart && service privoxy restart && service squid restart && ./check_ip.sh && tail -f /dev/null
