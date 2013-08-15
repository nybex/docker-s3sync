# -*- coding: utf-8 -*-
import os
import multiprocessing

import envoy
import boto

from boto.s3.key import Key
from boto.s3.bucket import Bucket

if not os.environ.get('AWS_ACCESS_KEY_ID') or (
        not os.environ.get('AWS_SECRET_ACCESS_KEY')):
    raise Exception("Please set %s and %s in your environment" %(
        'AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY',))

# Create a connection to s3
conn = boto.connect_s3()

def upload(args):
    # Get the bucket, validate tries to list the bucket,
    # to minimize permissions, we're turning that off
    aws_bucket = args.get('--bucket')
    bucket = conn.lookup(aws_bucket, validate=False)
    key_basename = args.get('<id>')

    # Create the first key
    keys = []
    keys.append(key_basename)

    # Yes, I know s3 has a 99.999999999% reliability rate
    redundancy = None
    try:
        redundancy = int(args.get('--redundancy'))
    except: pass
    if redundancy:
        if isinstance(redundancy, (int, long)) and redundancy > 0:
            for x in range(redundancy-1):
                keys.append('%s-r%s' % (key_basename, str(x),))

    if len(args.get('--volume')):
        upload_volumes = args.get('--volume')
    else:
        upload_volumes = []
        # Get a list of docker mounted volumes
        # TODO: make sure this works across volume types
        r = envoy.run('mount | grep by-uuid | grep rw')
        raw_mounts = r.std_out.split("\n")
        for raw_mount in raw_mounts:
            if raw_mount:
                upload_volumes.append(raw_mount.split(' ')[2])

    if not len(upload_volumes):
        raise Exception(
            'No volumes specified and unable to infer from mounts')


    if False in [os.path.isdir(x) for x in upload_volumes]:
        raise Exception(
            'Unable to find all specified volumes')

    # Tar up the volumes, gzip for size reduction
    tmp_name = os.tmpnam()
    envoy.run('tar czf %s %s' % (tmp_name, ' '.join(upload_volumes),))

    for k in keys:
        key = Key(bucket)
        key.name = k
        try:
            key.set_contents_from_filename(tmp_name, encrypt_key=True)
        except Exception as e:
            raise Exception('There was a problem storing the data: %s' %
                    e.message)
