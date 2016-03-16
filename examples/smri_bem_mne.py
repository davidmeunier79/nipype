# -*- coding: utf-8 -*-
"""
Created on Mon Jan 18 14:51:07 2016

@author: pasca

Call MNE Watershed BEM algorithm by using the make_watershed_bem function 
of MNE Python package and copy the generated surfaces in the bem folder

"""


# Import modules
import nipype.pipeline.engine as pe
from nipype.interfaces.utility import IdentityInterface, Function

from nipype.interfaces.mne import WatershedBEM

from smri_params import sbj_dir, subjects_list, BEM_WF_name


### datasource
infosource = pe.Node(interface=IdentityInterface(fields=['subject_id']), name="infosource")
infosource.iterables = ('subject_id', subjects_list)


### create BEM workflow
bem_workflow = pe.Workflow(BEM_WF_name)

bem_workflow.base_dir = sbj_dir

def mne_watershed_bem(sbj_dir, sbj_id):

    from mne.bem import make_watershed_bem                
    
    print 'call make_watershed_bem'
    make_watershed_bem(sbj_id, sbj_dir, overwrite=True)
    
    return sbj_id

call_mne_watershed_bem = pe.Node(interface=Function(input_names=['sbj_dir', 'sbj_id'], 
                                           output_names=['sbj_id'],
                                           function = mne_watershed_bem), name = 'call_mne_watershed_bem')

call_mne_watershed_bem.inputs.sbj_dir = sbj_dir

def copy_surfaces(sbj_id):
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
    
copy_bem_surf = pe.Node(interface=Function(input_names=['sbj_id'], 
                                           output_names=['sbj_id'],
                        function = copy_surfaces), name = 'copy_bem_surf')
                            

bem_workflow.connect(infosource, 'subject_id',   call_mne_watershed_bem, 'sbj_id')
bem_workflow.connect(call_mne_watershed_bem, 'sbj_id',  copy_bem_surf, 'sbj_id')

bem_workflow.run() 