# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 22:44:00 2015

@author: pasca
"""
import os

home = False
test = True

is_nii = False

if home:
    main_path = '/home/pasca/Dropbox/work/karim/data/'
    sbj_dir   = '/home/pasca/Science/research/MEG/work/subjects/'    
    MRI_path  = os.path.join(sbj_dir,"MRI")
    sbj       = 'megsim'
    subjects_list = ['megsim', 'dmn_mri']
else:    
    main_path = '/home/karim/Documents/pasca/data/MEG-ODYSSEE' # data dir
    sbj_dir   =  os.path.join(main_path,"FSF")                 
    MRI_path  =  os.path.join(main_path,"MRI2_odysse")
    
    if test:
        subjects_list = ['MORYV','SANGA','VANSO','VIRJE']  # 
    else:
        subjects_list = ["balai",'benba','casla','doble','droco','duple','frapa',
                         'haimo','laupa','levma','mahan','marle','merly','mesma','moryv','ricro',
                         'rimso','rougw','sanga','torgu','vanso','virje'] 
    

# nome della cartella dentro main_path=sbj_dir
FS_WF_name = "_segmentation" 
BEM_WF_name = "_watershed_bem" 

surf_names     = ['brain_surface',  'inner_skull_surface',  'outer_skull_surface',  'outer_skin_surface']
new_surf_names = ['brain.surf',     'inner_skull.surf',     'outer_skull.surf',     'outer_skin.surf']
    
    
if test == True:
    FS_WF_name = FS_WF_name + '_test'
    BEM_WF_name = BEM_WF_name + '_test'

