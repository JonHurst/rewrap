#!/bin/bash

TESTS="matching missing multi-missing extra multi-extra \
moved changed join multi-join split split-and-join pg84-1 pg84-2 \
pg84-3"

if [ $# -ge 1 ]
then
    TESTS=$*
fi

for X in $TESTS
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
