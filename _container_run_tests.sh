set -e
pip install nose coverage cov-core
cp -r /workdir /workdir-copy
cd /workdir-copy
python ./setup.py install
python ./setup.py nosetests
