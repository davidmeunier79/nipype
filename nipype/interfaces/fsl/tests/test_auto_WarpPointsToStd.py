# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..utils import WarpPointsToStd


def test_WarpPointsToStd_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    coord_mm=dict(argstr='-mm',
    xor=['coord_vox'],
    ),
    coord_vox=dict(argstr='-vox',
    xor=['coord_mm'],
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    img_file=dict(argstr='-img %s',
    mandatory=True,
    ),
    in_coords=dict(argstr='%s',
    mandatory=True,
    position=-1,
    ),
    out_file=dict(name_source='in_coords',
    name_template='%s_warped',
    output_name='out_file',
    ),
    premat_file=dict(argstr='-premat %s',
    ),
    std_file=dict(argstr='-std %s',
    mandatory=True,
    ),
    terminal_output=dict(deprecated='1.0.0',
    nohash=True,
    ),
    warp_file=dict(argstr='-warp %s',
    xor=['xfm_file'],
    ),
    xfm_file=dict(argstr='-xfm %s',
    xor=['warp_file'],
    ),
    )
    inputs = WarpPointsToStd.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_WarpPointsToStd_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = WarpPointsToStd.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
