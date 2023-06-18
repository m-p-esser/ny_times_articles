#!make
include .env

##################### Setup Environment

# Initializing Git
initialize_git:
	@echo "Initializing git..."
	git init

# Setting up Poetry
add_dependencies:
	@echo "Adding packages..."
	poetry add black -G dev
	poetry add flake8 -G dev
	poetry add python-dotenv -G dev
	poetry add pre-commit -G dev
	poetry add ipykernel -G dev
	poetry add prefect
# Lock Pandas so its compatible with ydata-profiling
	poetry add "pandas >=1.4.0, <2"
	poetry add ydata-profiling

install: 
	@echo "Installing..."
	poetry install

activate_precommit:
	poetry run pre-commit install

setup_environment: add_dependencies install activate_precommit

##################### Setup/Modify Google Cloud  

create_project:
	@echo "Create new project"
	gcloud projects create $(CLOUDSDK_CORE_PROJECT)
	@echo "Check if project is created"
	gcloud projects describe $(CLOUDSDK_CORE_PROJECT)

set_project:
	@echo "Set the project for the current session"
	gcloud config set project $(CLOUDSDK_CORE_PROJECT)

link_billing:
	@echo "Get list of billing accounts"
	gcloud beta billing accounts list
	@echo "Link billing account to project"
	gcloud beta billing projects link $(CLOUDSDK_CORE_PROJECT) --billing-account=$(CLOUDSKD_BILLING_ACCOUNT)
	@echo "Confirm billing account has been linked"
	gcloud beta billing accounts --project=$(CLOUDSDK_CORE_PROJECT) list

create_service_account:
	@echo "Create new Service account"
	gcloud iam service-accounts create $(CLOUDSDK_SERVICE_ACCOUNT)


member := serviceAccount:$(CLOUDSDK_SERVICE_ACCOUNT)@$(CLOUDSDK_CORE_PROJECT).iam.gserviceaccount.com

bind_iam_policies:
	@echo "Bind IAM Policies to Service account $(CLOUDSDK_SERVICE_ACCOUNT)"
	gcloud projects add-iam-policy-binding $(CLOUDSDK_CORE_PROJECT) --member=$(member) --role="roles/run.admin"
	gcloud projects add-iam-policy-binding $(CLOUDSDK_CORE_PROJECT) --member=$(member) --role="roles/compute.instanceAdmin.v1"
	gcloud projects add-iam-policy-binding $(CLOUDSDK_CORE_PROJECT) --member=$(member) --role="roles/artifactregistry.admin"
	gcloud projects add-iam-policy-binding $(CLOUDSDK_CORE_PROJECT) --member=$(member) --role="roles/iam.serviceAccountUser"
	gcloud projects add-iam-policy-binding $(CLOUDSDK_CORE_PROJECT) --member=$(member) --role="roles/storage.objectAdmin"
	gcloud projects add-iam-policy-binding $(CLOUDSDK_CORE_PROJECT) --member=$(member) --role="roles/bigquery.admin"

create_key_file:
	gcloud iam service-accounts keys create credentials/prefect_service_account.json \
		--iam-account=$(CLOUDSDK_SERVICE_ACCOUNT)@$(CLOUDSDK_CORE_PROJECT).iam.gserviceaccount.com

enable_services:
	@echo "Enabling GCP services..."
	gcloud services enable iamcredentials.googleapis.com
	gcloud services enable artifactregistry.googleapis.com
	gcloud services enable run.googleapis.com
	gcloud services enable compute.googleapis.com

enable_compute:
	@echo "Enable compute service"
	gcloud services enable compute.googleapis.com
	@echo "Add gcloud services compute default region and zone using variables above"
	gcloud compute project-info add-metadata \
	    --metadata google-compute-default-region=$(CLOUDSDK_DEFAULT_REGION),google-compute-default-zone=$(CLOUDSDK_DEFAULT_ZONE)
	@echo "Check that default region and zone is configured"
	gcloud compute project-info describe
	@echo "List compute services and ensure that they're enabled"
	gcloud services list --enabled --filter=compute
	
list_bucket:
	@echo "List current buckets"
	gsutil ls
	
prepare_script:
# chmod Upload worker script file so that it's executable
	chmod +x worker-startup-script.sh
	
deploy_compute:
# Create instance, using the `worker-startup-script.sh` as a startup script
	gcloud compute --project=$(CLOUDSDK_CORE_PROJECT) \
	instances create $(INSTANCE_NAME) --description="GCE Lab Challenge 1" --zone=$(CLOUDSDK_DEFAULT_ZONE) \
	--machine-type=f1-micro --image=debian-9-stretch-v20191121 --image-project=debian-cloud --boot-disk-size=10GB --boot-disk-type=pd-standard \
	--boot-disk-device-name=instance-1 --reservation-affinity=any --metadata-from-file startup-script=./worker-startup-script.sh \
	--metadata lab-logs-bucket=$(BUCKET) --scopes=https://www.googleapis.com/auth/servicecontrol,https://www.googleapis.com/auth/service.management.readonly,https://www.googleapis.com/auth/logging.write,https://www.googleapis.com/auth/monitoring.write,https://www.googleapis.com/auth/trace.append,https://www.googleapis.com/auth/devstorage.write_only
# Check that the instance is up
	gcloud compute instances list
	
validate_compute:
# Wait 300 seconds so that stress test can run and copy the file to the storage bucket
	sleep 300
# Check that stress test results are in bucket
	gsutil cat $(BUCKET)machine-$(INSTANCE_NAME)-finished.txt

unset_project:
	@echo "Unset project for current session"
	gcloud config unset project

delete_project:
	@echo "Delete project and WITHOUT prompting the user to confirm"
	gcloud projects delete $(CLOUDSDK_CORE_PROJECT) --quiet

create_project: create_project set_project link_billing
setup_basic_ressources: set_project enable_services bind_iam_policies create_service_account

##################### Startup | needs run everytime you open the Command line

# Activate Virtual Env
activate:
	@echo "Activating virtual environment"
	poetry shell

##################### Testing functions | needs to run before committing new functions

test:
	pytest

##################### Database Structure changes

sql2dbml:
	sql2dbml --mysql schema/prod/instagram_db.sql -o schema/prod/instagram_db.dbml

dbml2sql:
	dbml2sql --mysql schema/prod/instagram_db.dbml -o schema/prod/instagram_db.sql

##################### Deployment

export_dependencies:
	poetry export -o "requirements.txt" --without-hashes --without-urls

build_docker_image:
# gcloud artifacts repositories create prefect-flows --location=$(CLOUDSDK_COMPUTE_REGION) --repository-format="DOCKER"
	docker build -t $(CLOUDSDK_COMPUTE_REGION)-docker.pkg.dev/$(CLOUDSDK_CORE_PROJECT)/prefect-flows/$(HEALTHCHECK_FLOW_NAME):$(PREFECT_IMAGE_VERSION)-python$(PYTHON_VERSION) .
	gcloud auth configure-docker $(CLOUDSDK_COMPUTE_REGION)-docker.pkg.dev
	docker push $(CLOUDSDK_COMPUTE_REGION)-docker.pkg.dev/$(CLOUDSDK_CORE_PROJECT)/prefect-flows/$(HEALTHCHECK_FLOW_NAME):$(PREFECT_IMAGE_VERSION)-python$(PYTHON_VERSION)

##################### Documentation

docs_view:
	@echo View API documentation... 
	PYTHONPATH=src pdoc src --http localhost:8080

docs_save:
	@echo Save documentation to docs... 
	PYTHONPATH=src pdoc src -o docs


##################### Clean up

# Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache