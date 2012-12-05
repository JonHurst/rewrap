#!/bin/bash

echo "Matching paras test"
./match_paras.py tests/matching/input tests/matching/template tests/matching/output
diff -s tests/matching/expected-output tests/matching/output
echo


echo "Missing para test"
./match_paras.py tests/missing/input tests/missing/template tests/missing/output
diff -s tests/missing/expected-output tests/missing/output
echo
