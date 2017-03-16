#!/bin/bash 

is_root() {  
  if [ $(id -u) != "0" ]; then
    echo "Error: You must be root to run this script"
    exit 1  
  fi
}

is_root

if [ ! -d "/opt/app/python35" ]; then
	apt-get install gcc
	apt-get install make
	apt-get install libssl-dev
	apt-get install curl
	apt-get install libcurl4-openssl-dev

	mkdir -p /opt/down
	cd /opt/down
	wget https://www.python.org/ftp/python/3.5.2/Python-3.5.2.tgz
	tar xzvf Python-3.5.2.tgz 
	cd Python-3.5.2
	./configure --prefix=/opt/app/python35
	make && make install
	cd /opt/down
	rm -rf Python-3.5.2
	
	ln -s /opt/app/python35/bin/python3.5 /usr/local/bin/python35
	ln -s /opt/app/python35/bin/pip3.5 /usr/local/bin/pip35
fi

python35 -m pip install --upgrade pip
pip35 install configparser
pip35 install pymysql
pip35 install redis
pip35 install pycurl
pip35 install pillow
pip35 install certifi
