#!/usr/bin/env bash
dir_to_clean=${1:-data/generated_data}
# Get absolute path to script dir
script_dir=$(readlink -f $(dirname "$0"))
# Get absolute path to the data dir. Which is relative to the main dir
data_dir=$(readlink -f $script_dir/../$dir_to_clean)

[[ ! -d ${data_dir} ]] && echo "The dir ${data_dir} does not exist" && exit 1 || :

for db in ${data_dir}/*; do
    pushd ${db} > /dev/null
    jq -s 'add' [0-9]*json > all_data.json
    popd > /dev/null
done
