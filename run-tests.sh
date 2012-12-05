#!/bin/bash

echo "Matching paras test"
./match_paras.py tests/matching/input tests/matching/template tests/matching/output
diff -s tests/matching/expected-output tests/matching/output
echo

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
