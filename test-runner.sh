#!/usr/bin/env bash
cd $(dirname $0)

# get the default python version.
PYVER=$(python -c 'import sys; print(sys.version_info.major)')

if [ $PYVER -eq 2 ]; then other_py=python3
elif [ $PYVER -eq 3 ]; then other_py=python2
fi

# Run default python version.
python ./setup.py nosetests

if [ $? -ne 0 ]
then
    echo "failed to run under python${PYVER}, not checking $other_py"

    exit 1
fi


if [ -z "other_py" ];
then
    echo "what python version are you running '$PYVER'?!";
    echo "Couldn't test another version.";
else
    # check if the thing actually exists
    command -v $other_py > /dev/null 2>&1
    if [ $? -eq 0 ]
    then
        tmpfile=$(tempfile);

        echo "testing under $other_py"
        $other_py ./setup.py nosetests > $tmpfile 2>&1

        if [ $? -eq 0 ]
        then
            rm -f $tmpfile
            echo "ok under $other_py as well (omitting test output for brevity)"
        else
            cat $tmpfile
            rm -f $tmpfile
            exit 1
        fi
    else
        echo "Couldn't find suitable $other_py candidate, not tested under $other_py"
    fi
fi

