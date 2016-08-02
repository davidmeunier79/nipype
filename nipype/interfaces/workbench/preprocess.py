# -*- coding: utf-8 -*-
"""
A->B) First step: DICOM conversion
"""

#from nipype import config
#config.enable_debug_mode()

#import sys,io,os

import sys, os

############################################################## sup function ############################################################

def convert_cifti_to_np(cifti_file):

    import nibabel as nib 
    import os
    import numpy as np
    
    
    img = nib.load(cifti_file)
    
    
    data = img.get_data()
    
    print data
    
    data = data[0,0,0,0,:,:]
    
    print data.shape
    
    ts_npy_file = os.path.abspath("all_ts.npy")
    
    np.save(ts_npy_file,data)
    
    return ts_npy_file
    

def cifti_separate(cifti_file,label):
    
    import os
    
    gifti_file =  os.path.abspath(label + ".func.gii")
    
    command = "wb_command -cifti-separate " + cifti_file + " COLUMN -metric " + label + " " + gifti_file
    
    os.system(command)
    
    return gifti_file

def gifti_resample(gifti_file,orig_sphere,orig_anat,resampled_sphere_file,resampled_anat_file,brain_mask):

    import os
    
    resampled_dtseries = os.path.abspath("resampled_dtseries.func.gii")
    resampled_brain_mask = os.path.abspath("resampled_brain_mask.shape.gii")
                   
    command = "wb_command -metric-resample " + gifti_file + " " + orig_sphere + " " + resampled_sphere_file + " ADAP_BARY_AREA " + resampled_dtseries + " -area-surfs " + orig_anat + " " + resampled_anat_file + " -current-roi " + brain_mask + " -valid-roi-out " + resampled_brain_mask
    
    os.system(command)

    return resampled_dtseries,resampled_brain_mask


def surface_resample(sphere_file,anat_file,target_sphere_file):
    
    import os
    
    resampled_anat_file =  os.path.abspath("resampled_anat.surf.gii")
    
    if not os.path.exists(anat_file):
        
        print "warning anat_file does not exist"
    
    if not os.path.exists(sphere_file):
        
        print "warning sphere_file does not exist"
    
    
    if not os.path.exists(target_sphere_file):
        
        print "warning target_sphere_file does not exist"
        
    command = "wb_command -surface-resample " + anat_file + " " + sphere_file + " " + target_sphere_file + " BARYCENTRIC " + resampled_anat_file
    
    os.system(command)
    
    return resampled_anat_file

def read_hemispheric_gifti_and_convert_to_npy(left_gifti,right_gifti, left_mask_file, right_mask_file):
    
    import os
    import numpy as np
    import nibabel.gifti as gio
    
    from scipy import stats
    
    ### lecture du fichier gifti left + mask left
    gii_left  = gio.read(left_gifti)
    
    gii_left_mask = np.array(gio.read(left_mask_file).darrays[0].data, dtype = bool)
        
    print gii_left_mask
    
    ## list comprehension (liste des data par pas de temps)
    data_left = [gii_left.darrays[i].data for i in range(len(gii_left.darrays))]
    
    ### conversion en numpy array
    np_data_left = np.transpose(np.array(data_left))[gii_left_mask,:]
    
    print np_data_left.shape
    
    
    ### lecture du fichier gifti right + mask right
    gii_right  = gio.read(right_gifti)
    
    
    gii_right_mask = np.array(gio.read(right_mask_file).darrays[0].data, dtype = bool)
        
    print gii_right_mask
    
    
    ## list comprehension (liste des data par pas de temps)
    data_right = [gii_right.darrays[i].data for i in range(len(gii_right.darrays))]
    
    ### conversion en numpy array
    np_data_right = np.transpose(np.array(data_right))[gii_right_mask,:]
    
    print np_data_right.shape
    
    merged_ts = np.concatenate((np_data_left,np_data_right), axis = 0)
    
    
    #merged_ts_npy = os.path.abspath("merged_ts.npy")
    #np.save(merged_ts_npy,merged_ts)
    
    print merged_ts.shape
    
    #nonnan, = np.where(np.sum(np.isnan(merged_ts),axis = 1) == 0)
    
    #print nonnan.shape
    
    #nonnan_vect_file = os.path.abspath('nonnan_corres_vect.npy')
    
    #np.save(nonnan_vect_file,nonnan)
    
    #nonnan_merged_ts = merged_ts[nonnan,:]
    
    #print nonnan_merged_ts.shape
    
    #nonnan_merged_ts_file = os.path.abspath("nonnan_merged_ts.npy")
    
    #np.save(nonnan_merged_ts_file,nonnan_merged_ts)



    norm_merged_ts = stats.zscore(merged_ts,axis = 1)
    #norm_merged_ts = stats.zscore(nonnan_merged_ts,axis = 1)
    
    #print norm_merged_ts[0,:]
    #print norm_merged_ts[:,0]
    
    print norm_merged_ts.shape
    
    
    #print np.where(np.sum(np.isnan(norm_merged_ts),axis = 1) == 0)
    
    
    norm_merged_ts_npy = os.path.abspath("zscore_merged_ts.npy")
    np.save(norm_merged_ts_npy,norm_merged_ts)
    
    return norm_merged_ts_npy
    #,nonnan_vect_file

if __name__ =='__main__':
    
    test()
        
    
    
    
    
