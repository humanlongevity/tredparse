#!/bin/bash

# Save the current directory
SAVED_DIR=`pwd`
VER=1.3.1

# Grab the top level cerebro directory
cd /tmp

wget https://github.com/samtools/samtools/releases/download/$VER/samtools-$VER.tar.bz2
tar -xjf samtools-$VER.tar.bz2 && rm samtools-$VER.tar.bz2

cd samtools-$VER
./configure --enable-libcurl
make clean
make -j 8 LIBS="-lcurl -lcrypto" all
make install

# Go back to where we came from
cd $SAVED_DIR
