#!/bin/sh
# Expand the template into multiple yaml files, one for each item to be processed.
mkdir ./eoprocessing/jobs
for i in $(seq 1 $1)
do
  cat ./eoprocessing/job-tmpl.yaml | sed "s/\$WORKERS_COUNT/$1/;s/\$WORK_SIZE/$2/;s/\$JOB_NUMBER/$i/" > ./eoprocessing/jobs/job-$i.yaml
done