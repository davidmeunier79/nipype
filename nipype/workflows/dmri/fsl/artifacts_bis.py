# -*- coding: utf-8 -*-
# coding: utf-8
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
from __future__ import division

from ....interfaces.io import JSONFileGrabber
from ....interfaces import utility as niu
from ....interfaces import ants
from ....interfaces import fsl
from ....pipeline import engine as pe
from .utils import (b0_indices, time_avg, apply_all_corrections, b0_average,
                    hmc_split, dwi_flirt, eddy_rotate_bvecs, rotate_bvecs,
                    insert_mat, extract_bval, recompose_dwi, recompose_xfm,
                    siemens2rads, rads2radsec, demean_image,
                    cleanup_edge_pipeline, add_empty_vol, vsm2warp,
                    compute_readout,average4d)


def all_fsl_pipeline(name='fsl_all_correct',
                     epi_params=dict(echospacing=0.77e-3,
                                     acc_factor=3,
                                     enc_dir='y-'),
                     altepi_params=dict(echospacing=0.77e-3,
                                        acc_factor=3,
                                        enc_dir='y')):
    """
    Workflow that integrates FSL ``topup`` and ``eddy``.


    .. warning:: this workflow rotates the gradients table (*b*-vectors)
      [Leemans09]_.


    .. warning:: this workflow does not perform jacobian modulation of each
      *DWI* [Jones10]_.


    Examples
    --------

    >>> from nipype.workflows.dmri.fsl.artifacts import all_fsl_pipeline
    >>> allcorr = all_fsl_pipeline()
    >>> allcorr.inputs.inputnode.in_file = 'epi.nii'
    >>> allcorr.inputs.inputnode.alt_file = 'epi_rev.nii'
    >>> allcorr.inputs.inputnode.in_bval = 'diffusion.bval'
    >>> allcorr.inputs.inputnode.in_bvec = 'diffusion.bvec'
    >>> allcorr.run() # doctest: +SKIP

    """

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['in_file', 'in_bvec', 'in_bval', 'alt_file']),
        name='inputnode')

    outputnode = pe.Node(niu.IdentityInterface(
        fields=['out_file', 'out_mask', 'out_bvec']), name='outputnode')

    def _gen_index(in_file):
        import numpy as np
        import nibabel as nb
        import os
        out_file = os.path.abspath('index.txt')
        vols = nb.load(in_file).get_data().shape[-1]
        np.savetxt(out_file, np.ones((vols,)).T)
        return out_file

    avg_b0_0 = pe.Node(niu.Function(
        input_names=['in_dwi', 'in_bval'], output_names=['out_file'],
        function=b0_average), name='b0_avg_pre')
    
    bet_dwi0 = pe.Node(fsl.BET(frac=0.3, mask=True, robust=True),
                       name='bet_dwi_pre')

    sdc = sdc_peb(epi_params=epi_params, altepi_params=altepi_params)
    
    wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode, avg_b0_0, [('in_file', 'in_dwi'),
                               ('in_bval', 'in_bval')]),
        (avg_b0_0, bet_dwi0, [('out_file', 'in_file')]),
        (bet_dwi0, sdc, [('mask_file', 'inputnode.in_mask')]),
        (inputnode, sdc, [('in_file', 'inputnode.in_file'),
                          ('alt_file', 'inputnode.alt_file'),
                          ('in_bval', 'inputnode.in_bval'),
                          ('in_bvec', 'inputnode.in_bvec')])
    ])
    
    #return wf

    ### eddy
    ecc = pe.Node(fsl.Eddy(method='jac'), name='ecc')
    wf.connect([
        (sdc, ecc, [('topup.out_enc_file', 'in_acqp'),
                    ('topup.out_fieldcoef', 'in_topup_fieldcoef'),
                    ('topup.out_movpar', 'in_topup_movpar')]),
        (bet_dwi0, ecc, [('mask_file', 'in_mask')]),
        (inputnode, ecc, [('in_file', 'in_file'),
                          (('in_file', _gen_index), 'in_index'),
                          ('in_bval', 'in_bval'),
                          ('in_bvec', 'in_bvec')])
    ])
        
    ### rotate bvecs
    rot_bvec = pe.Node(niu.Function(
        input_names=['in_bvec', 'eddy_params'], output_names=['out_file'],
        function=eddy_rotate_bvecs), name='Rotate_Bvec')
    avg_b0_1 = pe.Node(niu.Function(
        input_names=['in_dwi', 'in_bval'], output_names=['out_file'],
        function=b0_average), name='b0_avg_post')
    bet_dwi1 = pe.Node(fsl.BET(frac=0.3, mask=True, robust=True),
                       name='bet_dwi_post')

    #wf = pe.Workflow(name=name)
    wf.connect([
        (inputnode, rot_bvec, [('in_bvec', 'in_bvec')]),
        (ecc, rot_bvec, [('out_parameter', 'eddy_params')]),
        (ecc, avg_b0_1, [('out_corrected', 'in_dwi')]),
        (inputnode, avg_b0_1, [('in_bval', 'in_bval')]),
        (avg_b0_1, bet_dwi1, [('out_file', 'in_file')]),
        (ecc, outputnode, [('out_corrected', 'out_file')]),
        (rot_bvec, outputnode, [('out_file', 'out_bvec')]),
        (bet_dwi1, outputnode, [('mask_file', 'out_mask')])
    ])
    
    return wf


def sdc_peb(name='peb_correction',
            epi_params=dict(echospacing=0.77e-3,
                            acc_factor=3,
                            enc_dir='y-',
                            epi_factor=1),
            altepi_params=dict(echospacing=0.77e-3,
                               acc_factor=3,
                               enc_dir='y',
                               epi_factor=1)):
    """
    SDC stands for susceptibility distortion correction. PEB stands for
    phase-encoding-based.

    The phase-encoding-based (PEB) method implements SDC by acquiring
    diffusion images with two different enconding directions [Andersson2003]_.
    The most typical case is acquiring with opposed phase-gradient blips
    (e.g. *A>>>P* and *P>>>A*, or equivalently, *-y* and *y*)
    as in [Chiou2000]_, but it is also possible to use orthogonal
    configurations [Cordes2000]_ (e.g. *A>>>P* and *L>>>R*,
    or equivalently *-y* and *x*).
    This workflow uses the implementation of FSL
    (`TOPUP <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/TOPUP>`_).

    Example
    -------

    >>> from nipype.workflows.dmri.fsl.artifacts import sdc_peb
    >>> peb = sdc_peb()
    >>> peb.inputs.inputnode.in_file = 'epi.nii'
    >>> peb.inputs.inputnode.alt_file = 'epi_rev.nii'
    >>> peb.inputs.inputnode.in_bval = 'diffusion.bval'
    >>> peb.inputs.inputnode.in_mask = 'mask.nii'
    >>> peb.run() # doctest: +SKIP

    .. admonition:: References

      .. [Andersson2003] Andersson JL et al., `How to correct susceptibility
        distortions in spin-echo echo-planar images: application to diffusion
        tensor imaging <http://dx.doi.org/10.1016/S1053-8119(03)00336-7>`_.
        Neuroimage. 2003 Oct;20(2):870-88. doi: 10.1016/S1053-8119(03)00336-7

      .. [Cordes2000] Cordes D et al., Geometric distortion correction in EPI
        using two images with orthogonal phase-encoding directions, in Proc.
        ISMRM (8), p.1712, Denver, US, 2000.

      .. [Chiou2000] Chiou JY, and Nalcioglu O, A simple method to correct
        off-resonance related distortion in echo planar imaging, in Proc.
        ISMRM (8), p.1712, Denver, US, 2000.

    """

    inputnode = pe.Node(niu.IdentityInterface(
        fields=['in_file', 'in_bval', 'in_bvec','in_mask', 'alt_file', 'ref_num']),
        name='inputnode')
    
    outputnode = pe.Node(niu.IdentityInterface(
        fields=['out_file', 'out_vsm', 'out_warp']), name='outputnode')

    ### Averaging b0 from file with mixed b0 and b1000
    b0_ref = pe.Node(niu.Function(input_names=['in_dwi', 'in_bval'], output_names=['out_file'],function=b0_average), name='b0_ref')
    
    ### Averaging b0 from file with only b0 (easier)
    b0_alt = pe.Node(niu.Function(input_names=['in_dwi'], output_names=['out_file'],function=average4d), name='b0_alt')
    
    ### merging the 2 average in opposite directions
    b0_comb = pe.Node(niu.Merge(2), name='b0_list')
    b0_merge = pe.Node(fsl.Merge(dimension='t'), name='b0_merged')
          
    wf = pe.Workflow(name=name)
    wf.connect([
            (inputnode, b0_ref, [('in_file', 'in_dwi'),
                                ('in_bval', 'in_bval')]),
            (inputnode, b0_alt, [('alt_file', 'in_dwi')]),
            (b0_ref, b0_comb, [('out_file', 'in1')]),
            (b0_alt, b0_comb, [('out_file', 'in2')]),
            (b0_comb, b0_merge, [('out', 'in_files')])
            ])
  
    ### Topup
    topup = pe.Node(fsl.TOPUP(), name='topup')
    topup.inputs.encoding_direction = [epi_params['enc_dir'],
                                       altepi_params['enc_dir']]

    readout = compute_readout(epi_params)
    topup.inputs.readout_times = [readout,
                                  compute_readout(altepi_params)]
     
            
    wf.connect(b0_merge, 'merged_file', topup,'in_file')
    
    ### ApplyTopup and Converts a voxel shift map (vsm) to a displacements field (warp).
    unwarp = pe.Node(fsl.ApplyTOPUP(in_index=[1], method='jac'), name='unwarp')

    # scaling = pe.Node(niu.Function(input_names=['in_file', 'enc_dir'],
    #                   output_names=['factor'], function=_get_zoom),
    #                   name='GetZoom')
    # scaling.inputs.enc_dir = epi_params['enc_dir']
    
    vsm2dfm = vsm2warp()
    vsm2dfm.inputs.inputnode.enc_dir = epi_params['enc_dir']
    vsm2dfm.inputs.inputnode.scaling = readout


    wf.connect([(topup, unwarp, [('out_fieldcoef', 'in_topup_fieldcoef'),
                         ('out_movpar', 'in_topup_movpar'),
                         ('out_enc_file', 'encoding_file')]),
        (inputnode, unwarp, [('in_file', 'in_files')]),
        (unwarp, outputnode, [('out_corrected', 'out_file')]),
        # (b0_ref,      scaling,    [('roi_file', 'in_file')]),
        # (scaling,     vsm2dfm,    [('factor', 'inputnode.scaling')]),
        (b0_ref, vsm2dfm, [('out_file', 'inputnode.in_ref')]),
        (topup, vsm2dfm, [('out_field', 'inputnode.in_vsm')]),
        (topup, outputnode, [('out_field', 'out_vsm')]),
        (vsm2dfm, outputnode, [('outputnode.out_warp', 'out_warp')])
    ])
    return wf


def _eff_t_echo(echospacing, acc_factor):
    eff_echo = echospacing / (1.0 * acc_factor)
    return eff_echo


def _fix_enc_dir(enc_dir):
    enc_dir = enc_dir.lower()
    if enc_dir == 'lr':
        return 'x-'
    if enc_dir == 'rl':
        return 'x'
    if enc_dir == 'ap':
        return 'y-'
    if enc_dir == 'pa':
        return 'y'
    return enc_dir


def _checkrnum(ref_num):
    from nipype.interfaces.base import isdefined
    if (ref_num is None) or not isdefined(ref_num):
        return 0
    return ref_num


def _nonb0(in_bval):
    import numpy as np
    bvals = np.loadtxt(in_bval)
    return np.where(bvals != 0)[0].tolist()


def _xfm_jacobian(in_xfm):
    import numpy as np
    from math import fabs
    return [fabs(np.linalg.det(np.loadtxt(xfm))) for xfm in in_xfm]


def _get_zoom(in_file, enc_dir):
    import nibabel as nb

    zooms = nb.load(in_file).header.get_zooms()

    if 'y' in enc_dir:
        return zooms[1]
    elif 'x' in enc_dir:
        return zooms[0]
    elif 'z' in enc_dir:
        return zooms[2]
    else:
        raise ValueError('Wrong encoding direction string')
