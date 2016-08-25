# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os

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





def create_level1_4D_spm12(contrasts,wf_name = 'level1_4D_spm12', deriv1 = False, concat_runs = True, high_pass_filter_cutoff = 128 ):

    l1analysis = pe.Workflow(name=wf_name)
    
    #################### inputs ###################
    inputnode = pe.Node(niu.IdentityInterface(fields=['subject_info',
                                                      'functional_runs',
                                                      'realignment_parameters',
                                                      'time_repetition',
                                                      'mask',
                                                      'outlier_files'
                                                      ]),
                        name='inputnode')

    
    ##### define nodes         
    modelspec = pe.Node(interface=model.SpecifySPMModel(), name= "modelspec")
    modelspec.inputs.high_pass_filter_cutoff = high_pass_filter_cutoff
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
    
    level1design.inputs.timing_units = 'secs'
    
    
    
    level1estimate = pe.Node(interface=spm.EstimateModel(), name="level1estimate")
    level1estimate.inputs.estimation_method = {'Classical' : 1}
    
    contrastestimate = pe.Node(interface = spm.EstimateContrast(), name="contrastestimate")
    contrastestimate.inputs.contrasts = contrasts 
    
    if deriv1 == True:
        contrastestimate.inputs.use_derivs = True
        
    #### connect nodes
    ### from inputnode
    l1analysis.connect(inputnode, 'subject_info', modelspec, 'subject_info')
    l1analysis.connect(inputnode, 'functional_runs', modelspec, 'functional_runs')
    l1analysis.connect(inputnode, 'realignment_parameters',modelspec,'realignment_parameters')
    
    l1analysis.connect(inputnode, 'time_repetition',modelspec,'time_repetition')
    
    ### si art dans le preprocessing
    l1analysis.connect(inputnode, 'outlier_files',modelspec,'outlier_files')
    
    l1analysis.connect(inputnode, 'time_repetition',level1design,'interscan_interval')
    
    ### si skullstrip dans le preprocessing
    l1analysis.connect(inputnode, 'mask',level1design,'mask_image')
    
    ### other nodes
    l1analysis.connect(modelspec,'session_info', level1design,'session_info')
    
    l1analysis.connect(level1design,'spm_mat_file', level1estimate,'spm_mat_file')
    
    l1analysis.connect(level1estimate,'spm_mat_file', contrastestimate,'spm_mat_file')
    l1analysis.connect(level1estimate,'beta_images', contrastestimate,'beta_images')
    l1analysis.connect(level1estimate,'residual_image', contrastestimate,'residual_image')

    return l1analysis
    
def create_level2_one_sample_ttest_spm12(wf_name = "level2_one_sample_test"):

    
    l2Analysis = pe.Workflow(name=wf_name)
    
    #################### inputs ###################
    inputnode = pe.Node(niu.IdentityInterface(fields=['group_con_files']),
                        name='inputnode')

    #### One-sample T test (difference to zeros)
    l2Ttester = pe.Node(interface = spm.OneSampleTTestDesign(), name = 'l2Ttester')
    
    l2Analysis.connect(inputnode ,'group_con_files',l2Ttester,'in_files')
    #l2Analysis.connect(l2DataSource ,'con',l2Ttester,'group1_files')
    
    #### estimate model

    l2Estimttest = pe.Node(interface = spm.EstimateModel(), name = 'l2Estimttest')
    l2Estimttest.inputs.estimation_method = {'Classical':1}
    
    l2Analysis.connect(l2Ttester,'spm_mat_file',l2Estimttest,'spm_mat_file')
    
    
    
    #### contrast estimate
    l2Conest = pe.Node(interface = spm.EstimateContrast(), name = 'l2Conest')
    cont1 = ('Group','T', ['mean'],[1])
    l2Conest.inputs.contrasts = [cont1]        
    l2Conest.inputs.group_contrast = True

    l2Analysis.connect(l2Estimttest,'spm_mat_file',l2Conest,'spm_mat_file')
    l2Analysis.connect(l2Estimttest,'residual_image',l2Conest,'residual_image')
    l2Analysis.connect(l2Estimttest,'beta_images',l2Conest,'beta_images')
    
    #### datasink SPM.matlab_spm_path
    
    return l2Analysis

def create_level2_two_sample_ttest_spm12(wf_name = "level2_two_sample_test"):

    
    l2Analysis = pe.Workflow(name=wf_name)
    
    #################### inputs ###################
    inputnode = pe.Node(niu.IdentityInterface(fields=['group1_con_files','group2_con_files']),
                        name='inputnode')


    ##### Two-sample T test (difference between groups)
    l2Ttester = pe.Node(interface = spm.TwoSampleTTestDesign(), name = 'l2Ttester')
    
    l2Analysis.connect(inputnode ,'group1_con_files',l2Ttester,'group1_files')
    l2Analysis.connect(inputnode ,'group2_con_files',l2Ttester,'group2_files')
    
    ##### estimate model

    l2Estimttest = pe.Node(interface = spm.EstimateModel(), name = 'l2Estimttest')
    l2Estimttest.inputs.estimation_method = {'Classical':1}
    
    l2Analysis.connect(l2Ttester,'spm_mat_file',l2Estimttest,'spm_mat_file')
    
    
    
    #### contrast estimate
    l2Conest = pe.Node(interface = spm.EstimateContrast(), name = 'l2Conest')
    

    ### Group level
    cont_group1 = ('Group_1','T', ['Group_{1}'],[1])
    cont_group2 = ('Group_2','T', ['Group_{2}'],[1])

    ### Group comparison
    cont_group3 = ('Group_1>Group_2','T',['Group_{1}','Group_{2}'],[1,-1])
    cont_group4 = ('Group_2>Group_1','T',['Group_{1}','Group_{2}'],[-1,1])

    l2Conest.inputs.contrasts = [cont_group1,cont_group2,cont_group3,cont_group4]
    l2Conest.inputs.group_contrast = True

    l2Analysis.connect(l2Estimttest,'spm_mat_file',l2Conest,'spm_mat_file')
    l2Analysis.connect(l2Estimttest,'residual_image',l2Conest,'residual_image')
    l2Analysis.connect(l2Estimttest,'beta_images',l2Conest,'beta_images')
    
    return l2Analysis