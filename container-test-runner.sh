for i in 2.7 3.3 3.4 3.5 3.6
do
    docker run --rm -i -v "$(pwd)":/workdir python:$i bash /workdir/_container_run_tests.sh \
         > /dev/null 2>&1 \
         && echo "python $i: OK" \
         || echo "python $i: NOT OK" \
     &
done

wait $(jobs -p)