# -*- coding: utf-8 -*-
"""
Created on Mon Sep 21 22:44:00 2015

@author: pasca
"""
import os
import getpass

test = True
is_nii = True # True if you have MRI files in nii format

if getpass.getuser() == 'pasca':
    main_path = '/home/pasca/Dropbox/work/karim/data/'
    sbj_dir   = '/home/pasca/Science/research/MEG/work/subjects/'    
    MRI_path  = os.path.join(sbj_dir,"MRI")
    subjects_list = ['monk0002', 'prova']  # ['dmn_mri','Monk1'] #['monk0002']  'dmn_mri'
else:    
    main_path = '/media/karim/DATAS/MEDITATION'         # data dir
    sbj_dir   =  os.path.join(main_path,"FSF")          # where FS creates sbj dir           
    MRI_path  =  main_path                              # MRI dir
    
    if test:
        subjects_list = ['monk0002'] # ['MORYV','SANGA','VANSO','VIRJE'] 
    else:
#        subjects_list = ["balai",'benba','casla','doble','droco','duple','frapa',
#                         'haimo','laupa','levma','mahan','marle','merly','mesma','moryv','ricro',
#                         'rimso','rougw','sanga','torgu','vanso','virje'] 
#    
        subjects_list = ['monk0003','monk0004','monk0004','monk0005','monk0006','monk0007','monk0008','monk0009','monk0010',
                         'monk0011','monk0012']
        
# dir names in main_path=sbj_dir
FS_WF_name    = "_segmentation" 
BEM_WF_name   = "_watershed_bem" 
MAIN_WF_name  = "_main_worfflow" 
    
    
if test == True:
    FS_WF_name   = FS_WF_name   + '_test'
    BEM_WF_name  = BEM_WF_name  + '_test'
    MAIN_WF_name = MAIN_WF_name + '_test'

