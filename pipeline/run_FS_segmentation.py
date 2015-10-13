# -*- coding: utf-8 -*-
"""
Created on Wed Sep  9 16:49:35 2015

@author: pasca

================
sMRI: FreeSurfer
================

Call reconall on set of subjects and then make an average subject::
    python run_FS_segmentation.py

"""

# Import modules
import os
import os.path as op
import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe

from nipype.interfaces.freesurfer import MRIConvert, ReconAll
from nipype.interfaces.utility import IdentityInterface, Function

from nipype.interfaces.mne import WatershedBEM

from FS_params import home, is_nii
from FS_params import sbj_dir, MRI_path, FS_WF_name, subjects_list, BEM_WF_name

from FS_utils import get_first_file, get_MRI_sbj_dir
from FS_utils import copy_surfaces, create_bem_sol, create_source_space


def create_main_workflow_FS_segmentation():
    ### check envoiroment variables
    if not os.environ.get('FREESURFER_HOME'):
        raise RuntimeError('FREESURFER_HOME environment variable not set')
    
    if not os.environ.get('MNE_ROOT'):
        raise RuntimeError('MNE_ROOT environment variable not set')
            
        
    ### (1) iterate over subjects to define paths with templates -> Infosource and DataGrabber
    #       Node: SubjectData - we use IdentityInterface to create our own node, to specify
    #      the list of subjects the pipeline should be executed on
    infosource = pe.Node(interface=IdentityInterface(fields=['subject_id']), name="infosource")
    infosource.iterables = ('subject_id', subjects_list)

    ### grab data
    if is_nii:  
        datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'], outfields=['struct']),
                             name='datasource')
        datasource.inputs.base_directory = MRI_path
        datasource.inputs.template = '%s_swap.nii.gz'
        datasource.inputs.template_args = dict(struct=[['subject_id']])
        datasource.inputs.sort_filelist = True
    else:
        datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],outfields=['dcm_file']),
                             name = 'datasource')
        datasource.inputs.base_directory = MRI_path # dir in cui cercare i file
        # the template can be filled by other inputs
        # Here we define an input field for datagrabber called subject_id. 
        # This is then used to set the template (see %s in the template).
        if home:
            datasource.inputs.template = '%s*/*.dcm'
        else:
            datasource.inputs.template = '%s*/*/*T1*1mm/*.dcm'
        datasource.inputs.template_args = dict(dcm_file = [['subject_id']] )
        datasource.inputs.sort_filelist = True


    get_firstfile = pe.Node(interface=Function(input_names=['dcm_files'], output_names=['dcm_file'],
                             function = get_first_file), name = 'get_firstfile')
    
    
    get_MRI_sbjdir = pe.Node(interface=Function(input_names=['dcm_file'], output_names=['struct_filename'],
                             function = get_MRI_sbj_dir), name = 'get_MRI_sbjdir')
                         
    ### MRI_convert Node
    mri_convert = pe.Node(interface=MRIConvert(), infields=['in_file'] , outfields=['out_file'], 
                          name='mri_convert')

    ### ReconAll Node to generate surfaces and parcellations of structural
    # data from anatomical images of a subject.
    # the output of mriconvert is the input of recon-all

    recon_all = pe.Node(interface=ReconAll(), infields=['T1_files'], name='recon_all')
    #recon_all.inputs.subject_id = subject_list
    if not op.exists(sbj_dir):
        os.mkdir(sbj_dir)
        
    recon_all.inputs.subjects_dir = sbj_dir
    recon_all.inputs.directive    = 'all'

    # reconall_workflow will be a node of the main workflow    
    reconall_workflow = pe.Workflow(name = FS_WF_name)
    reconall_workflow.base_dir = MRI_path
    
    reconall_workflow.connect(infosource, 'subject_id', datasource,  'subject_id')  
    
    if not is_nii:
        reconall_workflow.connect(datasource, 'dcm_file',   get_firstfile,  'dcm_files')  
        reconall_workflow.connect(get_firstfile,  'dcm_file', get_MRI_sbjdir,  'dcm_file')
    
        reconall_workflow.connect(get_MRI_sbjdir,  'struct_filename', mri_convert, 'out_file')
        reconall_workflow.connect(get_firstfile,   'dcm_file',        mri_convert, 'in_file')
    
        
        reconall_workflow.connect(mri_convert, 'out_file',  recon_all, 'T1_files')
    else:
        reconall_workflow.connect(datasource, 'struct', recon_all, 'T1_files')

    reconall_workflow.connect(infosource, 'subject_id', recon_all, 'subject_id')
    
    ### BEM generation
    main_workflow = pe.Workflow(name = BEM_WF_name)
    main_workflow.base_dir = sbj_dir
    
    
    #
    bem = pe.Node(interface=WatershedBEM(), infields=['subject_id', 'subjects_dir', 'atlas_mode'],
                  outfields=['brain_surface', 'inner_skull_surface', 'outer_skin_surface', 'outer_skull_surface'],
                  name='bem')
    bem.inputs.subjects_dir = sbj_dir 
    bem.inputs.atlas_mode = True
    
    main_workflow.connect(reconall_workflow, 'recon_all.subject_id', bem, 'subject_id')
    
    copy_bem_surf = pe.Node(interface=Function(input_names=['sbj_dir', 'sbj_id','brain_surface', 
                                                            'inner_skull_surface', 'outer_skin_surface',
                                                            'outer_skull_surface'], output_names=['sbj_id'],
                            function = copy_surfaces), name = 'copy_bem_surf')
    copy_bem_surf.inputs.sbj_dir = sbj_dir
    
    main_workflow.connect(infosource, 'subject_id',   copy_bem_surf, 'sbj_id')
    main_workflow.connect(bem, 'brain_surface',       copy_bem_surf, 'brain_surface')
    main_workflow.connect(bem, 'inner_skull_surface', copy_bem_surf, 'inner_skull_surface')
    main_workflow.connect(bem, 'outer_skin_surface',  copy_bem_surf, 'outer_skin_surface')
    main_workflow.connect(bem, 'outer_skull_surface', copy_bem_surf, 'outer_skull_surface')
    
    bem_sol = pe.Node(interface=Function(input_names=['sbj_dir','sbj_id'], output_names=['sbj_id'],
                             function = create_bem_sol), name = 'bem_sol')
    bem_sol.inputs.sbj_dir = sbj_dir

    main_workflow.connect(copy_bem_surf, 'sbj_id', bem_sol, 'sbj_id')
    
    source_space = pe.Node(interface=Function(input_names=['sbj_dir','sbj_id'], output_names=[''],
                             function = create_source_space), name = 'source_space')
    source_space.inputs.sbj_dir = sbj_dir
    
    main_workflow.connect(bem_sol, 'sbj_id', source_space, 'sbj_id')

    return main_workflow

if __name__ == '__main__':
    
    ### run pipeline:
    main_workflow = create_main_workflow_FS_segmentation()
    
    # main_workflow.write_graph()
    main_workflow.config['execution'] = {'remove_unnecessary_outputs':'false'}
    main_workflow.run(plugin='MultiProc', plugin_args={'n_procs' : 8})    
