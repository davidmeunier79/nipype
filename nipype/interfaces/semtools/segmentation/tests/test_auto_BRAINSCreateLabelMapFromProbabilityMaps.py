# AUTO-GENERATED by tools/checkspecs.py - DO NOT EDIT
from __future__ import unicode_literals
from ..specialized import BRAINSCreateLabelMapFromProbabilityMaps


def test_BRAINSCreateLabelMapFromProbabilityMaps_inputs():
    input_map = dict(
        args=dict(argstr='%s', ),
        cleanLabelVolume=dict(
            argstr='--cleanLabelVolume %s',
            hash_files=False,
        ),
        dirtyLabelVolume=dict(
            argstr='--dirtyLabelVolume %s',
            hash_files=False,
        ),
        environ=dict(
            nohash=True,
            usedefault=True,
        ),
        foregroundPriors=dict(
            argstr='--foregroundPriors %s',
            sep=',',
        ),
        ignore_exception=dict(
            deprecated='1.0.0',
            nohash=True,
            usedefault=True,
        ),
        inclusionThreshold=dict(argstr='--inclusionThreshold %f', ),
        inputProbabilityVolume=dict(argstr='--inputProbabilityVolume %s...', ),
        nonAirRegionMask=dict(argstr='--nonAirRegionMask %s', ),
        priorLabelCodes=dict(
            argstr='--priorLabelCodes %s',
            sep=',',
        ),
        terminal_output=dict(
            deprecated='1.0.0',
            nohash=True,
        ),
    )
    inputs = BRAINSCreateLabelMapFromProbabilityMaps.input_spec()

    for key, metadata in list(input_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(inputs.traits()[key], metakey) == value
def test_BRAINSCreateLabelMapFromProbabilityMaps_outputs():
    output_map = dict(
        cleanLabelVolume=dict(),
        dirtyLabelVolume=dict(),
    )
    outputs = BRAINSCreateLabelMapFromProbabilityMaps.output_spec()

    for key, metadata in list(output_map.items()):
        for metakey, value in list(metadata.items()):
            assert getattr(outputs.traits()[key], metakey) == value
