# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..preprocess import EditWMwithAseg


def test_EditWMwithAseg_inputs():
    input_map = dict(args=dict(argstr='%s',
    ),
    brain_file=dict(argstr='%s',
    mandatory=True,
    position=-3,
    ),
    environ=dict(nohash=True,
    usedefault=True,
    ),
    ignore_exception=dict(nohash=True,
    usedefault=True,
    ),
    in_file=dict(argstr='%s',
    mandatory=True,
    position=-4,
    ),
    keep_in=dict(argstr='-keep-in',
    ),
    out_file=dict(argstr='%s',
    mandatory=True,
    position=-1,
    ),
    seg_file=dict(argstr='%s',
    mandatory=True,
    position=-2,
    ),
    subjects_dir=dict(),
    terminal_output=dict(nohash=True,
    ),
    )
    inputs = EditWMwithAseg.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_EditWMwithAseg_outputs():
    output_map = dict(out_file=dict(),
    )
    outputs = EditWMwithAseg.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
