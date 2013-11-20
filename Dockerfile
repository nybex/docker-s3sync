# docker-bitcoin
#
# VERSION               0.0.1

FROM stackbrew/ubuntu:12.04
MAINTAINER Jud Stephenson "<jud@nybex.com>"

# Inflate the apt cache
RUN apt-get update

# Install pip
RUN apt-get install -y python-pip

# Add the s3sync command
ADD s3sync/ /nybex/

# add the python libraries
RUN pip install -r /nybex/requirements.txt

# Run the s3sync command
ENTRYPOINT ["/usr/bin/env", "python", "/nybex/s3sync"]
