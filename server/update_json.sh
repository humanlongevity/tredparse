#!/bin/bash

cd ..
python -c "from tredparse.meta import TREDsRepo; print TREDsRepo().to_json()" \
    > server/imports/api/documents/treds.json
cd -
