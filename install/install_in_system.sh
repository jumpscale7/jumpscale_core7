if [ -f "/etc/slitaz-release" ]
then
  echo "found slitaz"
  tazpkg get-install curl 
  tazpkg get-install git
  tazpkg get-install python 
fi

#known env variables

#JSBASE : is root where jumpscale will be installed
#SANDBOX : if system will be installed as sanbox or not (1 or 0)
#GITHUBUSER : user used to connect to github
#GITHUBPASSWD : passwd used to connect to github
#JSGIT : root for jumpcale git

#how to set the env vars: below you can find the defaults
# export GITHUBUSER=''
# export GITHUBPASSWD=''
export SANDBOX=0
# export JSBASE='/opt/jumpscale7'
# export JSGIT='https://github.com/jumpscale7/jumpscale_core7.git'
# export JSBRANCH='master'
# export AYSGIT='https://github.com/jumpscale7/ays_jumpscale7.git'
# export AYSBRANCH='master'

set -ex
if [ "$(uname)" == "Darwin" ]; then
    # Do something under Mac OS X platform   
    echo 'install brew'     
    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"
    brew install curl
    brew install python
    brew install git
    TMPDIR = $(~/tmp)
    export JSBASE = '/Users/Shared/jumpscale'
elif [ "$(expr substr $(uname -s) 1 5)" == "Linux" ]; then
    dist=''
    dist=`grep DISTRIB_ID /etc/*-release | awk -F '=' '{print $2}'`
    if [ "$dist" == "Ubuntu" ]; then
        echo "found ubuntu"
        apt-get install curl git ssh python2.7 python -y
    fi
    export TMPDIR='/tmp'
    export JSBASE='/opt/jumpscale7'
elif [ "$(expr substr $(uname -s) 1 10)" == "MINGW32_NT" ]; then
    # Do something under Windows NT platform
    echo 'windows'
    echo "CODE NOT COMPLETE FOR WINDOWS IN install.sh"
    exit
fi

set -ex
curl -k https://raw.githubusercontent.com/jumpscale7/jumpscale_core7/master/install/web/bootstrap.py > $TMPDIR/bootstrap.py
cd $TMPDIR
python bootstrap.py
