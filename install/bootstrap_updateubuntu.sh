apt-get update
apt-get autoremove -y
apt-get -f install -y
apt-get upgrade -y
apt-get install mc curl git ssh python2.7 python-requests  -y
curl https://raw.githubusercontent.com/Jumpscale/jumpscale_core7/master/install/bootstrap.py | python 