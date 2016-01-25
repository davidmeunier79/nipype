# -*- coding: utf-8 -*-
"""
Created on Mon Jan 18 14:51:07 2016

@author: pasca
"""
# Import modules
import nipype.pipeline.engine as pe
from nipype.interfaces.utility import IdentityInterface, Function

from nipype.workflows.smri.freesurfer import create_BEM_workflow

from smri_params import sbj_dir, subjects_list, BEM_WF_name, MAIN_WF_name


### datasource
infosource = pe.Node(interface=IdentityInterface(fields=['subject_id']), name="infosource")
infosource.iterables = ('subject_id', subjects_list)


### create BEM workflow
bem_workflow = create_BEM_workflow(BEM_WF_name)

bem_workflow.base_dir = sbj_dir
bem_workflow.inputs.inputspec.subjects_dir = sbj_dir


### create main workflow
main_workflow = pe.Workflow(name = MAIN_WF_name)
main_workflow.base_dir = sbj_dir
main_workflow.connect(infosource, 'subject_id', bem_workflow, 'inputspec.subject_id')

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
                            
main_workflow.connect(infosource,   'subject_id',           copy_bem_surf, 'sbj_id')
main_workflow.connect(bem_workflow, 'outputspec.meshes',    copy_bem_surf, 'mesh_files')


main_workflow.run() 