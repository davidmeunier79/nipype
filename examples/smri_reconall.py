# -*- coding: utf-8 -*-
"""
Created on Tue Jan 19 11:11:02 2016

@author: pasca

Call recon-all on set of subjects and then run the MNE watershed bem algorithm
    python run_FS_segmentation.py

"""

# Import modules
import os
import os.path as op
import nipype.interfaces.io as nio
import nipype.pipeline.engine as pe

from nipype.interfaces.freesurfer import MRIConvert, ReconAll
from nipype.interfaces.utility import IdentityInterface, Function

from smri_params import is_nii, sbj_dir, subjects_list, MRI_path, FS_WF_name, MAIN_WF_name

from nipype.interfaces.mne import WatershedBEM

def create_main_workflow_FS_segmentation():
    
    ### check envoiroment variables
    if not os.environ.get('FREESURFER_HOME'):
        raise RuntimeError('FREESURFER_HOME environment variable not set')
    
    if not os.environ.get('MNE_ROOT'):
        raise RuntimeError('MNE_ROOT environment variable not set')
            
    if not op.exists(sbj_dir):
        os.mkdir(sbj_dir)
        
    ### (1) iterate over subjects to define paths with templates -> Infosource and DataGrabber
    #       Node: SubjectData - we use IdentityInterface to create our own node, to specify
    #       the list of subjects the pipeline should be executed on
    infosource = pe.Node(interface=IdentityInterface(fields=['subject_id']), name="infosource")
    infosource.iterables = ('subject_id', subjects_list)

    ### Grab data
    #   the template can be filled by other inputs
    #   Here we define an input field for datagrabber called subject_id. 
    #   This is then used to set the template (see %s in the template).

    if is_nii:  
        datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'], 
                                                       outfields=['struct']),
                             name='datasource')
        datasource.inputs.template = '%s*.nii.gz'
        datasource.inputs.template_args = dict(struct=[['subject_id']])
    else:
        datasource = pe.Node(interface=nio.DataGrabber(infields=['subject_id'],
                                                       outfields=['dcm_file']),
                             name = 'datasource')
        datasource.inputs.template = '%s*/*.dcm' # '%s*/*/*T1*1mm/*.dcm'
        datasource.inputs.template_args = dict(dcm_file = [['subject_id']] )
        
    datasource.inputs.base_directory = MRI_path # dir where the MRI files are
    datasource.inputs.sort_filelist = True
    
    # get the path of the first dicom file
    def get_first_file(dcm_files):
        return dcm_files[0]

    # return the path of the struct filename in the MRI sbj dir that will be the 
    # input of MRI convert routine
    def get_MRI_sbj_dir(dcm_file):
        from nipype.utils.filemanip import split_filename as split_f
        import os.path as op
        
        MRI_sbj_dir, basename, ext = split_f(dcm_file)
        struct_filename = op.join(MRI_sbj_dir, 'struct.nii.gz')
        return struct_filename

    get_firstfile  = pe.Node(interface=Function(input_names  = ['dcm_files'], 
                                               output_names  = ['dcm_file'],
                            function = get_first_file), name = 'get_firstfile')
    
    
    get_MRI_sbjdir = pe.Node(interface=Function(input_names  = ['dcm_file'], 
                                                output_names = ['struct_filename'],
                             function = get_MRI_sbj_dir), name = 'get_MRI_sbjdir')
                 
    ### MRI_convert Node
    #   We use it if we don't have a .nii.gz file
    #   The output of mriconvert is the input of recon-all
    mri_convert = pe.Node(interface=MRIConvert(), infields=['in_file'] , 
                                                  outfields=['out_file'], 
                          name='mri_convert')


    ### (2) ReconAll Node to generate surfaces and parcellations of structural
    #       data from anatomical images of a subject.
    recon_all = pe.Node(interface=ReconAll(), infields=['T1_files'], name='recon_all')
    recon_all.inputs.subjects_dir = sbj_dir
    recon_all.inputs.directive    = 'all'

    # reconall_workflow will be a node of the main workflow    
    reconall_workflow = pe.Workflow(name = FS_WF_name)

    reconall_workflow.base_dir = MRI_path
     
    reconall_workflow.connect(infosource, 'subject_id', recon_all, 'subject_id')
    
    reconall_workflow.connect(infosource, 'subject_id', datasource,  'subject_id') 
    if is_nii:
        reconall_workflow.connect(datasource, 'struct', recon_all, 'T1_files')
    else:
        reconall_workflow.connect(datasource,   'dcm_file',   get_firstfile,  'dcm_files')  
        reconall_workflow.connect(get_firstfile,'dcm_file',   get_MRI_sbjdir, 'dcm_file')
    
        reconall_workflow.connect(get_firstfile,   'dcm_file',        mri_convert, 'in_file')
        reconall_workflow.connect(get_MRI_sbjdir,  'struct_filename', mri_convert, 'out_file')
        
        reconall_workflow.connect(mri_convert, 'out_file',  recon_all, 'T1_files')
            
#    reconall_workflow.run()
    

    ### (3) BEM generation by the watershed algo of MNE C
    main_workflow = pe.Workflow(name = MAIN_WF_name)
    main_workflow.base_dir = sbj_dir
    
    bem = pe.Node(interface=WatershedBEM(), infields=['subject_id', 'subjects_dir', 'atlas_mode'],
                                            outfields=['mesh_files'],
                                            name='bem')
    bem.inputs.subjects_dir = sbj_dir 
    bem.inputs.atlas_mode = True
    
    main_workflow.connect(reconall_workflow, 'recon_all.subject_id', bem, 'subject_id')
    
    def mne_watershed_bem(sbj_dir, sbj_id):

        from mne.bem import make_watershed_bem                
        
        print 'call make_watershed_bem'
        make_watershed_bem(sbj_id, sbj_dir, overwrite=True)

    call_mne_watershed_bem = pe.Node(interface=Function(input_names=['sbj_dir', 'sbj_id'], 
                                               output_names=['sbj_id'],
                                               function = mne_watershed_bem), name = 'call_mne_watershed_bem')
                                             

    def copy_surfaces(sbj_id, mesh_files):
        import os
        import os.path as op
        from smri_params import sbj_dir
        
        surf_names     = ['brain_surface',  'inner_skull_surface',  'outer_skull_surface',  'outer_skin_surface']
        new_surf_names = ['brain.surf',     'inner_skull.surf',     'outer_skull.surf',     'outer_skin.surf']
        
        bem_dir     = op.join(sbj_dir, sbj_id, 'bem')    
        surface_dir = op.join(sbj_dir, sbj_id, 'bem/watershed')
    
        for i in range(len(surf_names)):
            os.system('cp %s %s' %(op.join(surface_dir,sbj_id + '_' + surf_names[i]), 
                                   op.join(bem_dir,sbj_id + '-' + new_surf_names[i])))
       
        return sbj_id    
    
    copy_bem_surf = pe.Node(interface=Function(input_names=['sbj_id', 'mesh_files'], 
                                               output_names=['sbj_id'],
                            function = copy_surfaces), name = 'copy_bem_surf')
                            
    main_workflow.connect(infosource,   'subject_id',    copy_bem_surf, 'sbj_id')
    main_workflow.connect(bem,           'mesh_files',    copy_bem_surf, 'mesh_files')


    return main_workflow



### Execute the pipeline
# The code above sets up all the necessary data structures and the connectivity 
# between the processes, but does not generate any output. To actually run the
# analysis on the data the ``nipype.pipeline.engine.Pipeline.Run``
# function needs to be called.


if __name__ == '__main__':
    
    ### run pipeline:
    main_workflow = create_main_workflow_FS_segmentation()
    
    # main_workflow.write_graph()
    main_workflow.config['execution'] = {'remove_unnecessary_outputs':'false'}
    main_workflow.run(plugin='MultiProc', plugin_args={'n_procs' : 8})    