SHELL := /bin/sh

# config
SPEC_ROOT            ?= gh
BUNDLE_OUT           ?= gh.yaml

REDOCLY_IMAGE        ?= redocly/cli:latest
OPENAPI_GEN_IMAGE    ?= openapitools/openapi-generator-cli:latest

CLIENT_OUT_DIR       ?= ./
PY_PACKAGE_NAME      ?= github_openapi_client
PY_PROJECT_NAME      ?= github-openapi-client
PY_LIBRARY           ?= httpx

SPEC_MOUNT           ?= /spec
LOCAL_MOUNT          ?= /local

# msys (git bash on windows)
UNAME_S := $(shell uname -s 2>/dev/null || echo unknown)
USE_MSYS ?= $(if $(filter MSYS% MINGW% CYGWIN%,$(UNAME_S)),1,0)

ifeq ($(USE_MSYS),1)
DOCKER_ENV_PREFIX := MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL="*"
else
DOCKER_ENV_PREFIX :=
endif

PWD := $(CURDIR)

.DEFAULT_GOAL := all

.PHONY: all bundle gen-client clean

all: bundle gen-client

$(BUNDLE_OUT):
	@echo "[redocly] bundle $(BUNDLE_OUT)"
	$(DOCKER_ENV_PREFIX) docker run --rm \
	  -v "$(PWD):$(SPEC_MOUNT)" \
	  $(REDOCLY_IMAGE) bundle "$(SPEC_ROOT)" --output "$(BUNDLE_OUT)"
	@git add .
bundle: $(BUNDLE_OUT)

gen-client: $(BUNDLE_OUT)
	@echo "[openapi-generator] generate python client $(CLIENT_OUT_DIR)/$(PY_PACKAGE_NAME)"
	@mkdir -p "$(CLIENT_OUT_DIR)"
	@rm -rf "$(CLIENT_OUT_DIR)/$(PY_PACKAGE_NAME)"
	$(DOCKER_ENV_PREFIX) docker run --rm \
	  -v "$(PWD):$(LOCAL_MOUNT)" \
	  $(OPENAPI_GEN_IMAGE) generate \
	  -i "$(LOCAL_MOUNT)/$(BUNDLE_OUT)" \
	  -g python \
	  -o "$(LOCAL_MOUNT)/$(CLIENT_OUT_DIR)" \
	  --additional-properties=packageName=$(PY_PACKAGE_NAME),projectName=$(PY_PROJECT_NAME),library=$(PY_LIBRARY) \
	  --global-property=apiTests=false,modelTests=false,apiDocs=false,modelDocs=false
	@git add .

clean:
	@rm -f "$(BUNDLE_OUT)"
	@rm -rf "$(CLIENT_OUT_DIR)/$(PY_PACKAGE_NAME)"
