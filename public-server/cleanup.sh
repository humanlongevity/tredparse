#!/bin/bash

set -x
rm -rf node_modules/ .meteor/ .editorconfig .gitignore package.json \
        update_json.sh client/ imports/ public/ server/
