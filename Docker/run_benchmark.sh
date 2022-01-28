#!/bin/bash

BASEDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo $1
DIRNAME=$1
python3 $BASEDIR/client.py --log --dir $DIRNAME
node $BASEDIR/chrome/chrome.js --log --dir $DIRNAME
# node $BASEDIR/chrome/chrome.js --log --multi --dir $DIRNAME
