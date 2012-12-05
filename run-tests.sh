#!/bin/bash

./match_paras.py tests/matching/input tests/matching/template tests/matching/output
echo "Matching paras test"
diff -s tests/matching/expected-output tests/matching/output
echo

