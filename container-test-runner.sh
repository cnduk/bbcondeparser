#!/bin/bash
set -ex
for i in 3.3 3.4 3.5 3.6 3.7 3.8
do
    docker run --rm -i -v "$(pwd)":/workdir python:$i bash /workdir/_container_run_tests.sh \
         > /dev/null 2>&1 \
         && echo "python $i: Matthew McConaughey says ALRIGHT ALRIGHT ALRIGHT" \
         || echo "python $i: Shia Labeouf says NO NO NO NOOOOO" \
     &
done

wait $(jobs -p)