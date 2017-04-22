#Stole template from here:
#http://www.itnotes.de/docker/development/tools/2014/08/31/speed-up-your-docker-workflow-with-a-makefile/
NS = tanghaibao
#NS = docker-dev.hli.io/servicedock
TAG = latest

BASENAME = tredparse

.PHONY: all
all: build push
test: build testrun

build:
	docker build -f $(BASENAME).dockerfile -t $(NS)/$(BASENAME):$(TAG) ./
build-public:
	docker build -f $(BASENAME)-public.dockerfile -t $(NS)/$(BASENAME)-public:$(TAG) ./
push:
	docker push $(NS)/$(BASENAME):$(TAG)
testrun:
	docker run $(NS)/$(BASENAME):$(TAG) tred.py
