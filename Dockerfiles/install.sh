#!/bin/bash

# Save the current directory
SAVED_DIR=`pwd`

# Grab the top level cerebro directory
cd /tmp

mkdir htslib-s3
cd htslib-s3
wget https://github.com/samtools/samtools/releases/download/1.3.1/samtools-1.3.1.tar.bz2
wget https://github.com/samtools/htslib/releases/download/1.3.1/htslib-1.3.1.tar.bz2
tar -xjf samtools-1.3.1.tar.bz2 && rm samtools-1.3.1.tar.bz2
tar -xjf htslib-1.3.1.tar.bz2 && rm htslib-1.3.1.tar.bz2

cd htslib-1.3.1
autoconf
./configure --enable-libcurl
make -j 8 all
make install

cd ../samtools-1.3.1
make -j 8 HTSDIR=../htslib-1.3.1/ LIBS="-lcurl -lcrypto" all
make install

# Go back to where we came from
cd $SAVED_DIR
