install:
	-groupadd taurusxr
	-useradd taurusxr -g taurusxr -M -d /var/taurusxr -s /bin/false
	-mkdir -p /var/taurusxr/lib
	-mkdir -p /var/taurusxr/data
	install /opt/taurusxr/lib/libssl.so.1.0.0 /var/taurusxr/lib/libssl.so.1.0.0
	install /opt/taurusxr/lib/libcrypto.so.1.0.0 /var/taurusxr/lib/libcrypto.so.1.0.0
	install /opt/taurusxr/lib/libssl.so.1.0.0 /var/taurusxr/lib/libssl.so.10
	install /opt/taurusxr/lib/libcrypto.so.1.0.0 /var/taurusxr/lib/libcrypto.so.10
	install /opt/taurusxr/lib/libmysqlclient.so.18 /var/taurusxr/lib/libmysqlclient.so.18
	install /opt/taurusxr/lib/libpgm-5.2.so.0 /var/taurusxr/lib/libpgm-5.2.so.0
	install /opt/taurusxr/lib/libzmq.so.3 /var/taurusxr/lib/libzmq.so.3
	echo "/var/taurusxr/lib" >> /etc/ld.so.conf && ldconfig
	install etc/taurusxee.service /usr/lib/systemd/system/taurusxr.service
	install -m 0755 /opt/taurusxr/bin/taurusxkey  /usr/local/bin/taurusxkey
	install -m 0755 /opt/taurusxr/radiusctl  /usr/local/bin/radiusctl
	chown -R taurusxr /opt/taurusxr
	chown -R taurusxr /var/taurusxr
	chmod +x /opt/taurusxr/radiusctl
	chmod +x /opt/taurusxr/bin/*
	systemctl enable taurusxr && systemctl daemon-reload

uninstall:
	-systemctl disable taurusxr && systemctl daemon-reload
	-rm -rf /usr/lib/systemd/system/taurusxr.service
	-rm -rf /usr/local/bin/taurusxkey
	-rm -rf /usr/local/bin/radiusctl
	-sed -i '/taurusxr/d' /etc/ld.so.conf && ldconfig
	-userdel -r taurusxr

upgrade-libs:
	bin/pip install -r requirements.txt

initdb:
	bin/python radiusctl initdb -f -c etc/taurusxee.json
	chown -R taurusxr /var/taurusxr

updb:
	bin/python radiusctl updb -c etc/taurusxee.json
	chown -R taurusxr /var/taurusxr

backup:
	bin/python radiusctl backup -c etc/taurusxee.json
	chown -R taurusxr /var/taurusxr

clean-build:
	sh release.sh clean

buildver:
	sh release.sh buildver

package:
	sh release.sh package

patch:
	sh release.sh patch

run:
	python radiusctl standalone -c testdata/master.json

freerun:
	python freectl standalone -c testdata/master.json

freesspd:
	python freectl ssportal -c testdata/master.json

sspd:
	python radiusctl ssportal -c testdata/master.json

wland:
	python radiusctl wlanportal -lp 50100 -c testdata/master.json

acsim:
	python radiusctl acsim -c testdata/master.json

mpd:
	export DEV_OPEN_ID=oFXX6s_ftj6LOYDodkcxoHNjlXj0;\
	python radiusctl mpd -c testdata/master.json

runs:
	python radiusctl standalone -c testdata/slave.json

suprun:
	python radiusctl daemon -s startup -n -c testdata/taurusxee.conf

shell:
	python radiusctl shell -c testdata/master.json

test:
	python radiusctl initdb -f -c taurusxradius/tests/test.json;\
	trial taurusxradius.tests

inittest:
	python radiusctl initdb -c testdata/master.json
	python radiusctl initdb -c testdata/slave.json

uptest:
	python radiusctl updb -c testdata/master.json
	python radiusctl updb -c testdata/slave.json

baktest:
	python radiusctl backup -c testdata/master.json

dbdoc:
	python radiusctl dbdoc > docs/manual/database.rst


clean:
	rm -fr _trial_temp

all:install

.PHONY: all clean initdb install