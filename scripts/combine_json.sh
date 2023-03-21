#!/usr/bin/env bash
dir_to_clean=${1:-data/generated_data}
# Get absolute path to script dir
script_dir=$(readlink -f $(dirname "$0"))
# Get absolute path to the data dir. Which is relative to the main dir
data_dir=$(readlink -f $script_dir/../$dir_to_clean)

[[ ! -d ${data_dir} ]] && echo "The dir ${data_dir} does not exist" && exit 1 || :

# Create all_data.json for each subdir
for db in ${data_dir}/*; do
    [[ -f ${db} ]] && continue || :
    pushd ${db} > /dev/null
    jq -s 'add' [0-9]*json > all_data.json
    popd > /dev/null
done

# Create all_data.json for every db combined
pushd ${data_dir} > /dev/null

jq -s 'add' */all_data.json > all_data.json
#jq -s 'add' */syntax_correct_data.json > syntax_correct_data.json
#jq -s 'add' */syntax_incorrect_data.json > syntax_incorrect_data.json

echo "First run this script to create all_data.json. Then run validate.py. Then rerun this script."

popd > /dev/null
