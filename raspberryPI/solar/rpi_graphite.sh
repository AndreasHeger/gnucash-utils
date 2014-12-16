#!/bin/bash -ex
#####################
# https://github.com/ghoulmann/rpi-graphite/blob/master/rpi-graphite.sh
# Installs Graphite
#####################
# Graphite served from :8080
# Default is disabled
# Requires interaction: yes, admin name, password
# check for root
if [[ $EUID -ne 0 ]]; then
    echo "$0 must be run as root." 1>&2
    exit 1
fi

# Install Function - Installs packages from repositories
install ()
{
    apt-get update #always do "sudo apt-get update" before installing from the (always free) software repositories.
    DEBIAN_FRONTEND=noninteractive apt-get -y \
    -o DPkg::Options::=--force-confdef \
    -o DPkg::Options::=--force-confold \
    install $@
}

# pip install function
pips ()
{
    pip install $@
}

install apache2 \
python-pip \
python-cairo \
python-django \
python-django-tagging \
libapache2-mod-wsgi \
libapache2-mod-python \
python-twisted \
python-memcache \
python-pysqlite2 \
python-simplejson \
memcached \
python-cairo-dev \
python-ldap \
erlang-os-mon \
erlang-snmp \
rabbitmq-server \
netcat


# apache2 site conf from web
rm -f /etc/apache2/sites-available/graphite
wget https://raw.github.com/tmm1/graphite/master/examples/example-graphite-vhost.conf -O /etc/apache2/sites-available/graphite

# port 8080 instead of 80
sed -i 's|80|8080|' /etc/apache2/sites-available/graphite
echo "Listen 8080" >> /etc/apache2/sites-available/graphite

# copy configuration files
cp graphite/*.conf /opt/graphite/conf

# because docs say so
mkdir -p /etc/httpd/wsgi/

#Local settings from example
cp graphite/local_settings.py /opt/graphite/webapp/graphite/local_settings.py
# SyncDB - requires interaction
cd /opt/graphite/webapp/graphite && python manage.py syncdb #prompts for input
#OR cd /opt/graphite/webapp/graphite && python manage.py syncdb --noinput
# set permissions
chown -R www-data:www-data /opt/graphite/storage

# enable mod_wsgi
a2enmod wsgi

# enable site
a2ensite graphite

# restart apache2
service apache2 reload
