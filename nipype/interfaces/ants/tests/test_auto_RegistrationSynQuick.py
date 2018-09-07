# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..registration import RegistrationSynQuick


def test_RegistrationSynQuick_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        dimension=dict(
            argstr='-d %d',
            usedefault=True,
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        fixed_image=dict(
            argstr='-f %s...',
            mandatory=True,
        ),
        histogram_bins=dict(
            argstr='-r %d',
            usedefault=True,
        ),
        moving_image=dict(
            argstr='-m %s...',
            mandatory=True,
        ),
        num_threads=dict(
            argstr='-n %d',
            usedefault=True,
        ),
        output_prefix=dict(
            argstr='-o %s',
            usedefault=True,
        ),
        precision_type=dict(
            argstr='-p %s',
            usedefault=True,
        ),
        spline_distance=dict(
            argstr='-s %d',
            usedefault=True,
        ),
        transform_type=dict(
            argstr='-t %s',
            usedefault=True,
        ),
        use_histogram_matching=dict(argstr='-j %d', ),
    )
    inputs = RegistrationSynQuick.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_RegistrationSynQuick_outputs():
    output_map = dict(
        forward_warp_field=dict(),
        inverse_warp_field=dict(),
        inverse_warped_image=dict(),
        out_matrix=dict(),
        warped_image=dict(),
    )
    outputs = RegistrationSynQuick.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
