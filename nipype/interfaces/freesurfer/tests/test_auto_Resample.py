# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..preprocess import Resample


def test_Resample_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        in_file=dict(
            argstr='-i %s',
            mandatory=True,
            position=-2,
        ),
        resampled_file=dict(
            argstr='-o %s',
            genfile=True,
            position=-1,
        ),
        subjects_dir=dict(),
        voxel_size=dict(
            argstr='-vs %.2f %.2f %.2f',
            mandatory=True,
        ),
    )
    inputs = Resample.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_Resample_outputs():
    output_map = dict(resampled_file=dict(), )
    outputs = Resample.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
