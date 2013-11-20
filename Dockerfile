# docker-bitcoin
#
# VERSION               0.0.1

FROM stackbrew/ubuntu:12.04
MAINTAINER Jud Stephenson "<jud@nybex.com>"

# Add the s3sync command
ADD s3sync/ /nybex/

# Run the s3sync command
ENTRYPOINT ["/usr/bin/env", "python", "/nybex/s3sync"]
