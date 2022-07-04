from flask import Flask, Response, render_template, request, url_for, flash, redirect
import traceback
import os
from datetime import date, datetime
import psycopg2
from psycopg2 import Error

from kubernetes import client, config, utils
from kubernetes.client import V1JobList, V1Job, BatchV1Api

import subprocess
import shutil


app = Flask(__name__, template_folder='templates')

app.config['PROPAGATE_EXCEPTIONS'] = True
@app.errorhandler(Exception)
def handle_exception(e):
    return traceback.format_exc(), 500


@app.route("/")
def home():
    return render_template('home.html')

# -----------------------------------------------------------

@app.route("/job-history/")
def job_history():

    result = None

    try:
        connection = psycopg2.connect(user=os.getenv("POSTGRES_USER"), # read username/password from env. variable set by the deployed K8S secret
                                    password=os.getenv("POSTGRES_PASSWORD"),
                                    database="postgresdb",
                                    host = "postgres", # K8S service name discoverable on the cluster
                                    port="5432"
                                    )
        
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM job_history;")
        result = cursor.fetchall()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

    return render_template("job-history.html", result=result)

# ----------------------------------------------------------------

@app.route('/deploy-jobs/', methods=('GET', 'POST'))
def deploy_jobs():

    yaml_dir = "./eoprocessing/jobs"

    if request.method == 'POST':
        workers_count = request.form['workers-count']
        work_size = request.form['work-size']

        if os.path.isdir(yaml_dir):
            try:
                shutil.rmtree(yaml_dir)
            except OSError as e:
                print("Error: %s : %s" % (yaml_dir, e.strerror))
        subprocess.run(["./extract_job_manifests.sh", workers_count, work_size])

        config.load_config()
        k8s_client = client.ApiClient()
        utils.create_from_directory(k8s_client, yaml_dir,verbose=True)

        return redirect('/read-jobs')
    return render_template('deploy-jobs.html')


# ----------------------------------------------------------------

@app.route('/read-jobs/', methods=('GET', 'POST'))
def read_jobs():

    job_statuses = []

    config.load_config()
    batch = BatchV1Api()
    job_list = batch.list_namespaced_job(namespace='default')

    for job in job_list.items:
        name = job.metadata.name
        start_time = job.status.start_time.strftime("%m/%d/%Y, %H:%M:%S")
        active = 'No' if job.status.active is None else 'Yes'
        succeeded = 'Yes' if job.status.succeeded == 1 else 'No'
        job_status = (name, start_time, active, succeeded)
        job_statuses.append(job_status)
    
    if request.method == 'POST': 
        for job in job_list.items:
            batch.delete_namespaced_job(namespace='default', name=job.metadata.name, propagation_policy='Background')
        return redirect(url_for("home"))

    return render_template('read-jobs.html', job_statuses=job_statuses)