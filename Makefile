# Makefile
# Variables
ZIP_FILE = hephaestus.zip
SOURCE_DIRS = *.py app db utils

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
	poetry export -f requirements.txt --without-hashes > requirements.txt

python_install_with_requirements:
	pip install -r requirements.txt --platform manylinux2014_x86_64 --target ./python --only-binary=:all:

zip_deployment:
	zip -r hp-deployment-package.zip python/

