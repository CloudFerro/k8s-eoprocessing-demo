# Sample EO Processing workflow using Kubernetes jobs
This is a demo application for CloudFerro Kubernetes as a Service webinar held on 30.06.2022.
App mocks a sample EO processing workflow. The code pulls EO images from EO data, Kubernetes jobs store the output back to S3 private bucket (no actual processing in this sample workflow). Job history is saved in to a containerized Postgres deployment backed with a persistent Cinder volume.

## Prerequisites
- Kubernetes Magnum cluster (with EODATA access enabled) on WAW3-1 cloud with Kubectl configured (refer to demo ppt deck). Best a fresh cluster to avoid any configuration conflicts.
- Download the YAML files in this repo folder and subfolders. Downloading `/eoprocessing/jobs-tmpl.yaml` is optional, as it will be deployed by actions from webapp UI.

## Steps to deploy
- Run `kubectl apply -f pods_jobs_rbac.yaml` to generate ClusterRole and ClusterRoleBinding to authorize web app to access Kubernetes API via Python client
- Create a private S3 bucket called `eoprocessing_webinar` in your WAW3-1 Openstack project.
- Input in `secrets.yaml` file the access/secret keys to the project containing this bucket.
- If you wish to update sample Postgres username/password, please change them to same values in both `secrets.yaml` and `/postgres/postgres-configmap.yaml`
- Run `kubectl apply -f secrets.yaml` to deploy secrets on your cluster.
- Deploy **Postgres** container: deploy 3 yaml files from the `/postgres` directory in order: configmap -> storage -> deployment (e.g. for first file run from postgres dir `kubectl apply -f postgres-configmap.yaml`)
- Deploy **Webapp** container: run `kubectl apply -f eoprocessing-webapp.yaml`
- After couple of minutes by running `kubectl get services` you will see Postgres and Webapp services running. Type into your browser the external IP of the Webapp service.

## Docker images
- Deployment and service yaml file for both `eoprocessing` and `eoprocessing-webapp` containers are available as (public) Docker images in CFRO [Docker Hub](docker.io).
- You can build your own images based on included Dockerfiles and point to your own repository instead, you would need to reconfigure accordingly.

## Precautions
- This is not production ready code. Do not apply directly into production environment before undergoing proper security and reliability precautions.
- Hitting `Delete Jobs` in the web app will currently delete all jobs in default namespace (so also your own jobs if you are currently running some!). Use with caution or amend Python script to specify only the demo jobs e.g. filter by labels.