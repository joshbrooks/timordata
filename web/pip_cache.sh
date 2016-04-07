mkdir -p pip
pip2tgz pip -r requirements.txt
dir2pi --normalize-package-names pip
