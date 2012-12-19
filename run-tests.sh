#!/bin/bash

for X in matching missing multi-missing
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
echo "Missing para test"
./match_paras.py tests/missing/input tests/missing/template tests/missing/output
diff -s tests/missing/expected-output tests/missing/output
echo

echo "Multiple missing para test"
./match_paras.py tests/multi-missing/input tests/multi-missing/template tests/multi-missing/output
diff -s tests/multi-missing/expected-output tests/multi-missing/output
echo

echo "Extra para test"
./match_paras.py tests/extra/input tests/extra/template tests/extra/output
diff -s tests/extra/expected-output tests/extra/output
echo

echo "Multiple extra para test"
./match_paras.py tests/multi-extra/input tests/multi-extra/template tests/multi-extra/output
diff -s tests/multi-extra/expected-output tests/multi-extra/output
echo

echo "Moved para test"
./match_paras.py tests/moved/input tests/moved/template tests/moved/output
diff -s tests/moved/expected-output tests/moved/output
echo

echo "Multiple moved paras test"
./match_paras.py tests/multi-moved/input tests/multi-moved/template tests/multi-moved/output
diff -s tests/multi-moved/expected-output tests/multi-moved/output
echo

echo "Large Change para test"
./match_paras.py tests/changed/input tests/changed/template tests/changed/output
diff -s tests/changed/expected-output tests/changed/output
echo

echo "Join two paras test"
./match_paras.py tests/join/input tests/join/template tests/join/output
diff -s tests/join/expected-output tests/join/output
echo

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
