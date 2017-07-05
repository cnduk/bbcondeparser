for i in 2.7 3.3 3.4 3.5 3.6
do
    echo -n "python $i: "
    docker run --rm -it -v "$(pwd)":/workdir python:$i bash -c '
        {
            pip install nose coverage cov-core &&
            cd /workdir &&
            python ./setup.py install &&
            python ./setup.py nosetests
        } > /dev/null 2>&1 && echo "OK" || echo "NOT OK"
    '
done