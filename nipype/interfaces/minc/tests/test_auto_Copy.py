# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from ..minc import Copy


def test_Copy_inputs():
    input_map = dict(
        args=dict(argstr="%s",),
        environ=dict(nohash=True, usedefault=True,),
        input_file=dict(argstr="%s", extensions=None, mandatory=True, position=-2,),
        output_file=dict(
            argstr="%s",
            extensions=None,
            genfile=True,
            hash_files=False,
            name_source=["input_file"],
            name_template="%s_copy.mnc",
            position=-1,
        ),
        pixel_values=dict(argstr="-pixel_values", xor=("pixel_values", "real_values"),),
        real_values=dict(argstr="-real_values", xor=("pixel_values", "real_values"),),
    )
    inputs = Copy.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value


def test_Copy_outputs():
    output_map = dict(output_file=dict(extensions=None,),)
    outputs = Copy.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
