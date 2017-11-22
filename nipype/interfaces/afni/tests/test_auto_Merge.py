# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..utils import Merge


def test_Merge_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    blurfwhm=dict(argstr='-1blur_fwhm %d',
    units='mm',
    ),
    doall=dict(argstr='-doall',
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_files=dict(argstr='%s',
    copyfile=False,
    mandatory=True,
    position=-1,
    ),
    num_threads=dict(nohash=True,
    usedefault=True,
    ),
    out_file=dict(argstr='-prefix %s',
    name_source='in_file',
    name_template='%s_merge',
    ),
    outputtype=dict(),
    terminal_output=dict(deprecated='1.0.0',
    nohash=True,
    ),
    )
    inputs = Merge.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_Merge_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = Merge.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
