# -*- coding: utf-8 -*-
"""
Created on Wed Oct  7 14:43:35 2015

@author: pasca
"""


def get_first_file(dcm_files):
    return dcm_files[0]


def get_MRI_sbj_dir(dcm_file):
    from nipype.utils.filemanip import split_filename as split_f
    import os.path as op
    
    MRI_sbj_dir, basename, ext = split_f(dcm_file)
    struct_filename = op.join(MRI_sbj_dir, 'struct.nii.gz')
    return struct_filename
    
def copy_surfaces(sbj_dir, sbj_id, brain_surface, inner_skull_surface, outer_skin_surface,
                                                            outer_skull_surface):
    import os
    import os.path as op
    from FS_params import surf_names, new_surf_names
    
    bem_dir     = op.join(sbj_dir, sbj_id, 'bem')    
    surface_dir = op.join(sbj_dir, sbj_id, 'bem/watershed')

    for i in range(len(surf_names)):
        os.system('cp %s %s' %(op.join(surface_dir,sbj_id + '_' + surf_names[i]), 
                               op.join(bem_dir,sbj_id + '-' + new_surf_names[i])))
   
    return sbj_id
                               

def create_bem_sol(sbj_id):
    import os 
    
    os.system("$MNE_ROOT/bin/mne_setup_forward_model --subject "+sbj_id + " --homog --surf --ico 4")
    return sbj_id
    
    
def create_source_space(sbj_dir, sbj_id):
    import os.path as op
    import mne
    
    bem_dir     = op.join(sbj_dir, sbj_id, 'bem') 
    
    src_fname = op.join(bem_dir, '%s-ico-5-src.fif' %sbj_id)
    if not op.isfile(src_fname):
        mne.setup_source_space(sbj_id, fname=True, spacing='ico5', subjects_dir=sbj_dir, 
                               overwrite=True, n_jobs=2)
  