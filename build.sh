#!/bin/bash

set -e

# 설정
PYTHON_VERSION="3.12"
LAMBDA_FILE="execute.py"
OUTPUT_ZIP="lambda.zip"
PYTHON_DIR="python"

# 1. 이전 빌드 제거
rm -rf $PYTHON_DIR $OUTPUT_ZIP

# 2. Docker + gcc 포함 설치환경에서 의존성 빌드 및 압축
docker run --rm -v "$(pwd)":/var/task amazonlinux:2023 bash -c "
  dnf install -y python$PYTHON_VERSION python$PYTHON_VERSION-pip python$PYTHON_VERSION-devel gcc gcc-c++ make zip && \

  echo '
annotated-types==0.7.0
anyio==4.9.0
certifi==2025.7.14
charset-normalizer==3.4.2
distro==1.9.0
fastapi==0.116.1
greenlet==3.2.3
h11==0.16.0
httpcore==1.0.9
httpx==0.28.1
idna==3.10
importlib-metadata==8.7.0
jiter==0.10.0
jsonpatch==1.33
jsonpointer==3.0.0
langchain-core==0.3.72
langchain-openai==0.3.28
langchain-text-splitters==0.3.8
langchain==0.3.26
langsmith==0.4.8
mangum==0.19.0
openai==1.97.1
orjson==3.11.0
packaging==25.0
pydantic-core==2.33.2
pydantic==2.11.7
pyjwt==2.10.1
python-arango==8.2.1
pyyaml==6.0.2
regex==2024.11.6
requests-toolbelt==1.0.0
requests==2.32.4
setuptools==80.9.0
sniffio==1.3.1
sqlalchemy==2.0.41
starlette==0.47.2
tenacity==9.1.2
tiktoken==0.9.0
tqdm==4.67.1
typing-extensions==4.14.1
typing-inspection==0.4.1
urllib3==2.5.0
zipp==3.23.0
zstandard==0.23.0
' > /var/task/requirements.txt && \

  python$PYTHON_VERSION -m pip install --upgrade pip && \
  python$PYTHON_VERSION -m pip install --no-binary :all: -r /var/task/requirements.txt -t /var/task/$PYTHON_DIR
"

# 3. 의존성 압축
cd $PYTHON_DIR
zip -r9 ../$OUTPUT_ZIP .
cd ..

# 4. Lambda 핸들러 파일 추가
zip -g $OUTPUT_ZIP $LAMBDA_FILE

echo ""
echo "✅ Lambda 배포용 zip 완성: $OUTPUT_ZIP"
echo "📁 포함된 파일 수: $(unzip -l $OUTPUT_ZIP | wc -l)"
