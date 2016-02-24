# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
import nipype


import nipype.interfaces.io as nio
import nipype.interfaces.utility as niu

import nipype.interfaces.spm as spm

#import nipype.interfaces.freesurfer as fs    # freesurfer

#from nipype.interfaces import fsl

#import nipype.algorithms.rapidart as ra
import nipype.algorithms.modelgen as model
import nipype.pipeline.engine as pe
from nipype.pipeline.engine import Workflow





def create_level1_4D_spm12(contrasts, TR = 2.0, deriv1 = False, concat_runs = True):

    l1analysis = pe.Workflow(name='level1_4D_spm12')
    
    #################### inputs ###################
    inputnode = pe.Node(niu.IdentityInterface(fields=['subject_info',
                                                      'functional_runs',
                                                      'realignment_parameters',
                                                      'time_repetition',]),
                        name='inputnode')

    
    ##### define nodes         
    modelspec = pe.Node(interface=model.SpecifySPMModel(), name= "modelspec")
    modelspec.inputs.high_pass_filter_cutoff = 128
    modelspec.inputs.time_repetition = TR  
    modelspec.inputs.input_units = 'secs'
    modelspec.inputs.output_units = 'secs'
    
    if concat_runs == True:
        modelspec.inputs.concatenate_runs = True
    else:
        modelspec.inputs.concatenate_runs = False
        
    level1design = pe.Node(interface=spm.Level1Design(), name= "level1design")
    
    if deriv1 == True:
        level1design.inputs.bases  = {'hrf':{'derivs': [1,0]}}
    else:
        level1design.inputs.bases  = {'hrf':{'derivs': [0,0]}}  
    
    level1design.inputs.interscan_interval = TR
    level1design.inputs.timing_units = 'secs'
    
    level1estimate = pe.Node(interface=spm.EstimateModel(), name="level1estimate")
    level1estimate.inputs.estimation_method = {'Classical' : 1}
    
    contrastestimate = pe.Node(interface = spm.EstimateContrast(), name="contrastestimate")
    contrastestimate.inputs.contrasts = contrasts 
    
    #### connect nodes
    ### from inputnode
    l1analysis.connect(inputnode, 'subject_info', modelspec, 'subject_info')
    l1analysis.connect(inputnode, 'functional_runs', modelspec, 'functional_runs')
    l1analysis.connect(inputnode, 'realignment_parameters',modelspec,'realignment_parameters')
    
    l1analysis.connect(inputnode, 'time_repetition',modelspec,'time_repetition')
    l1analysis.connect(inputnode, 'time_repetition',level1design,'interscan_interval')
    
    ### other nodes
    l1analysis.connect(modelspec,'session_info', level1design,'session_info')
    
    l1analysis.connect(level1design,'spm_mat_file', level1estimate,'spm_mat_file')
    
    l1analysis.connect(level1estimate,'spm_mat_file', contrastestimate,'spm_mat_file')
    l1analysis.connect(level1estimate,'beta_images', contrastestimate,'beta_images')
    l1analysis.connect(level1estimate,'residual_image', contrastestimate,'residual_image')

    return l1analysis
    
