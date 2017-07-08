FROM ubuntu:latest
MAINTAINER htang@humanlongevity.com

RUN apt-get update
RUN apt-get install -y gcc git build-essential
RUN apt-get install -y python-dev libxml2-dev libxslt-dev
RUN apt-get install -y libncurses-dev libcurl4-openssl-dev zlib1g-dev
RUN apt-get install -y vcftools python-pip
RUN apt-get install -y libblas-dev liblapack-dev libatlas-base-dev gfortran
RUN apt-get install -y wget autoconf libssl-dev

RUN pip install --upgrade pip
RUN pip install boto3 awscli
RUN pip install pyfaidx pyliftover pyvcf
RUN pip install cython
RUN pip install pandas
RUN pip install scipy

# Install HTSLIB
ADD install.sh /
RUN bash /install.sh

# Must install pysam after HTSLIB
RUN pip install pysam==0.9.1

# Install tredparse
ADD t001_HD.bam t001_HD.bam.bai /
ADD t002_DM1.bam t002_DM1.bam.bai /
ADD t003_SCA17.bam t003_SCA17.bam.bai /
ADD t004_AR.bam t004_AR.bam.bai /
RUN pip install git+git://github.com/humanlongevity/tredparse.git
WORKDIR /
