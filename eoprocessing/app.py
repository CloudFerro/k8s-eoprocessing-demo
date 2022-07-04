import sys
import boto3
import time
import psycopg2
from psycopg2 import Error
from datetime import datetime
import os

workers_count = int(sys.argv[1])
work_size = int(sys.argv[2]) # total number of files to process
job_number = int(sys.argv[3])
job_size = int(work_size/workers_count) # no validation, work_size/workers_count

collection = 'Sentinel-2/MSI/L1C/2020/01/08/'

eodata_access_key="anykey"
eodata_secret_key="anykey"
eodata_host="http://data.cloudferro.com"

private_access_key = os.getenv("PRIVATE_ACCESS_KEY")
private_secret_key = os.getenv("PRIVATE_SECRET_KEY")
private_host = "https://s3.waw3-1.cloudferro.com"

eodata_s3_resource = boto3.resource('s3', aws_access_key_id=eodata_access_key, aws_secret_access_key=eodata_secret_key, endpoint_url=eodata_host)
eodata_s3_client = eodata_s3_resource.meta.client

collection_list = eodata_s3_client.list_objects(Delimiter='/', Bucket="DIAS", Prefix=collection, MaxKeys=work_size)['CommonPrefixes']

private_s3_resource = boto3.resource("s3", aws_access_key_id=private_access_key, aws_secret_access_key=private_secret_key, endpoint_url=private_host)
private_s3_client = private_s3_resource.meta.client


job_ranges = {} # ranges of files per job for entire batch e.g. {'job1': [0, 10], 'job2': [10, 20]}
for i in range(0, workers_count):
    job_ranges["job" + str(i+1)] = [i*job_size, job_size * (i+1)]
job_range = job_ranges["job" + str(job_number)]


job_start = str(datetime.now())

for i in collection_list[job_range[0]:job_range[1]]:
    prefix = i["Prefix"]
    jpeg_path = prefix[30:-6] + "-ql.jpg"
    bucket=eodata_s3_resource.Bucket('DIAS')
    bucket.download_file(prefix + jpeg_path, "./images/" + jpeg_path)
    time.sleep(1) # simplified, for production await the file from s3


    private_s3_client.upload_file("./images/" + jpeg_path, "eoprocessing_webinar", str(datetime.now()) + "_" + jpeg_path)

job_end = str(datetime.now())

try:
    connection = psycopg2.connect(user=os.getenv("POSTGRES_USER"),
                                password=os.getenv("POSTGRES_PASSWORD"),
                                host = "postgres", # K8S postgres service name discoverable on the cluster
                                port='5432',
                                dbname='postgresdb')
    cursor = connection.cursor()
    

    query =  "INSERT INTO job_history (job_start, job_end, collection, workers_count, job_number, job_size, work_size) VALUES (%s, %s, %s, %s, %s, %s, %s);"
    data = (job_start, job_end, collection, workers_count, job_number, job_size, work_size)

    cursor.execute(query, data)
    connection.commit()

except (Exception, Error) as error:
    print("Error while connecting to PostgreSQL", error)
finally:
    if (connection):
        cursor.close()
        connection.close()
