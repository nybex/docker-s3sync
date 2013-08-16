# -*- coding: utf-8 -*-
import tempfile

import boto
import envoy
from moto import mock_s3
from nose.tools import with_setup

from ..api import upload, download
from ..api.helpers.exceptions import *

TEST_BUCKET = 'test-bucket'

# Create our fake volumes
v1 = tempfile.mkdtemp()
v2 = tempfile.mkdtemp()

TEST_ARGS = {
    '--bucket': TEST_BUCKET,
    '--help': False,
    '--redundancy': '1',
    '--version': False,
    '--volume': [v1, v2],
    '<id>': '1234',
    'download': False,
    'upload': True
}

def setup_volumes():
    for i,v in enumerate(TEST_ARGS['--volume']):
        # Put some fake files in the directories
        with open('%s/test%s' % (v1,str(i),),'w') as f:
            f.write('This is a test')

@mock_s3
def test_no_volumes():
    a = TEST_ARGS.copy()
    a['--volume'] = []
    try:
        upload(a)
    except NoVolumesError:
        assert True
        return

    assert False

@mock_s3
def test_incorrect_bucket():
    try:
        upload(TEST_ARGS)
    except NoBucketError:
        assert True
        return
    except: pass

    assert False

@mock_s3
@with_setup(setup_volumes)
def test_simple_upload():
    conn = boto.connect_s3()
    conn.create_bucket(TEST_BUCKET)

    upload(TEST_ARGS)

    # The key should exist
    assert conn.get_bucket('test-bucket').get_key(1234) is not None

    k_len = 0
    for k in conn.get_bucket('test-bucket').list():
        k_len += 1

    assert k_len is 1
