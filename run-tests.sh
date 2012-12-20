#!/bin/bash

for X in matching missing multi-missing extra multi-extra moved changed join multi-join
do
    echo "------------------------------"
    echo "${X} test"
    echo "=============================="
    ./match_paras.py tests/${X}/template tests/${X}/input
    diff -s tests/${X}/input.paramatch tests/${X}/expected.paramatch
    ./wrap.py tests/${X}/template tests/${X}/input.paramatch
    diff -s tests/${X}/input.paramatch.wrap tests/${X}/expected.paramatch.wrap
    echo "------------------------------"
    echo
done
exit

#not yet working: multi-moved

echo "Join multiple paras test"
./match_paras.py tests/multi-join/input tests/multi-join/template tests/multi-join/output
diff -s tests/multi-join/expected-output tests/multi-join/output
echo

echo "Split paras test"
./match_paras.py tests/split/input tests/split/template tests/split/output
diff -s tests/split/expected-output tests/split/output
echo

echo "Splits and joins test"
./match_paras.py tests/split-and-join/input tests/split-and-join/template tests/split-and-join/output
diff -s tests/split-and-join/expected-output tests/split-and-join/output
echo
