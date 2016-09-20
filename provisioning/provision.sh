#!/usr/bin/env bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd -P )"
cd $DIR
pwd

apt_quiet_install () {
   echo "** Install package $1 **"
   DEBIAN_FRONTEND=noninteractive apt-get -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" -y -f -q install $1
}


# Upgrade Package Manager
echo "** Add Package Manager Repositories **"

# elasticsearch and kibana repositories repository
wget -qO - https://packages.elastic.co/GPG-KEY-elasticsearch | apt-key add -
echo "deb http://packages.elastic.co/elasticsearch/2.x/debian stable main" | tee -a /etc/apt/sources.list.d/elasticsearch-2.x.list
echo "deb http://packages.elastic.co/kibana/4.4/debian stable main" | tee -a /etc/apt/sources.list.d/kibana-4.4.x.list

# Node repository
wget -qO- https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
echo 'deb https://deb.nodesource.com/node_6.x wily main' > /etc/apt/sources.list.d/nodesource.list
echo 'deb-src https://deb.nodesource.com/node_6.x wily main' >> /etc/apt/sources.list.d/nodesource.list

apt-get update


# Install Development Tools
echo "** Install Development Tools **"
apt_quiet_install git
apt_quiet_install nodejs
apt_quiet_install npm
apt_quiet_install python-dev
apt_quiet_install libffi-dev
apt_quiet_install libssl-dev
apt_quiet_install libxml2-dev
apt_quiet_install libxslt-dev
apt_quiet_install libyaml-dev
apt_quiet_install python-pip


echo "** Install virtualenv **"
pip install virtualenv


echo "** Install elasticdump **"
npm install elasticdump -g


# Install Oracle Java
echo "** Install OracleJDK **"
cd /tmp
wget -nv --header "Cookie: oraclelicense=accept-securebackup-cookie" http://download.oracle.com/otn-pub/java/jdk/8u92-b14/jdk-8u92-linux-x64.tar.gz
mkdir /opt/jdk
tar -zxf jdk-8u92-linux-x64.tar.gz -C /opt/jdk
rm jdk-8u92-linux-x64.tar.gz
update-alternatives --install /usr/bin/java java /opt/jdk/jdk1.8.0_92/bin/java 100
update-alternatives --install /usr/bin/javac javac /opt/jdk/jdk1.8.0_92/bin/javac 100
cd $DIR


# Install ElasticSearch
echo "** Install ElasticSearch **"
apt_quiet_install elasticsearch
cp $DIR/etc/elasticsearch/elasticsearch.yml /etc/elasticsearch/elasticsearch.yml
update-rc.d elasticsearch defaults 95 10
service elasticsearch start


# Install Kibana
echo "** Install Kibana **"
apt_quiet_install kibana
mkdir /etc/kibana
cp $DIR/etc/kibana/kibana.yml /etc/kibana/kibana.yml
update-rc.d kibana defaults 96 9


echo "** Start Kibana **"
service kibana start


echo "** make screeps-marketd project **"
cd $DIR/../
make


echo "** install screeps-marketd project **"
make install

