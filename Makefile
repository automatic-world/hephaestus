OLD_IMAGE=us-west1-docker.pkg.dev/lines-infra/lines-store/erp-backend:0.0.1
NEW_IMAGE=471112615042.dkr.ecr.ap-northeast-2.amazonaws.com/erp_backend:latest
FILE=deployments/deployments.yaml

fastapi_run:
	uvicorn app.interfaces.rest.main:app --reload --port 8080

docker_build:
	docker build --platform=linux/amd64 -f ./deployments/prod/Dockerfile  -t $(NEW_IMAGE) .

ecr_push:
	docker push $(NEW_IMAGE)

k8s_apply_deployments_with_replace: build gcs_push
	sed -i '' 's|$(OLD_IMAGE)|$(NEW_IMAGE)|g' $(FILE)
	kubectl apply -f $(FILE)

k8s_apply_deployments:
	kubectl apply -f $(FILE)

k8s_delete_deployments:
	kubectl delete deploy/lines-rag-retriever-python

k8s_apply_config:
	kubectl apply -f deployments/configmap.yaml

k8s_apply_service:
	kubectl apply -f deployments/service.yaml

retriever_port_forward:
	kubectl port-forward svc/lines-chatbot-service 9090:9090 -n airflow

docker_manager_run:
	docker run -d -p  8080:8080 us-west1-docker.pkg.dev/lines-infra/lines-store/lines-g2b-manager-python:0.0.9

# Makefile
# Variables
ZIP_FILE = chat_websocket_lambda_python.zip
SOURCE_DIRS = lambda_chat.py

# Default target
all: zip

# Target for creating the zip file
zip: clean
	@echo "Zipping source directories and files..."
	zip -r $(ZIP_FILE) $(SOURCE_DIRS)

# Target for cleaning up zip file
clean:
	@echo "Cleaning up..."
	rm -f $(ZIP_FILE)

poetry_export:
	poetry export -f requirements.txt --without-hashes > requirements_deploy.txt

python_install:
	pip install --no-cache-dir --target ./python/ --python-version 3.12 --only-binary=:all: -r requirements_deploy.txt

zip_deployment:
	zip -r hp-deployment-package.zip python/
