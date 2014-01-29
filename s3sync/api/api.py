# -*- coding: utf-8 -*-
import os
import multiprocessing
import tempfile

import envoy
import boto

from boto.s3.key import Key
from boto.s3.bucket import Bucket

from helpers import get_volumes
from helpers.exceptions import *

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
                keys.append('%sr-%s' % (str(x), key_basename,))

    upload_volumes = get_volumes(args)
    if not len(upload_volumes):
        raise NoVolumesError(
            'No volumes specified and unable to infer from mounts')


    if False in [os.path.isdir(x) for x in upload_volumes]:
        raise VolumeNotDirectoryError(
            'Unable to find all specified volumes')

    # Tar up the volumes, gzip for size reduction
    tmp_name = tempfile.NamedTemporaryFile().name
    try:
        envoy.run('tar cf %s %s' % (tmp_name, ' '.join(upload_volumes),))

        for k in keys:
            key = Key(bucket)
            key.name = k
            try:
                key.set_contents_from_filename(tmp_name, encrypt_key=True)
            except KeyError:
                raise NoBucketError('The specified bucket does not exist')

    finally:
        envoy.run('rm -rf %s' % tmp_name)


def download(args):
    # Get the bucket, validate tries to list the bucket,
    # to minimize permissions, we're turning that off
    aws_bucket = args.get('--bucket')
    bucket = conn.lookup(aws_bucket, validate=False)
    key_basename = args.get('<id>')

    # Where are we going to download this
    tmp_name = tempfile.NamedTemporaryFile(delete=False).name
    extracted_tmp_name = tempfile.mkdtemp()

    volumes = get_volumes(args)
    if not len(volumes):
        raise Exception(
            'No volumes specified and unable to infer from mounts')

    try:
        # Create the key
        k = Key(bucket)
        k.name = key_basename
        k.get_contents_to_filename(tmp_name)

        # Now extract to location
        r = envoy.run(
            'tar -C %s -xf %s' %
                (extracted_tmp_name, tmp_name,))

        for f in volumes:
            r = envoy.run('cp -r %s%s %s' % (
                extracted_tmp_name, f.rstrip('/'),
                        os.path.dirname(f.rstrip('/'))))

            if r.status_code:
                raise Exception(
                    "There was an issue extracting volume:\n %s\n %s" %
                        (r.std_err, r.std_out,))

    finally:
        envoy.run('rm -rf %s %s' % (tmp_name, extracted_tmp_name,))
