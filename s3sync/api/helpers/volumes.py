# -*- coding: utf-8 -*-
import envoy

def get_volumes(args):
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

    return upload_volumes
