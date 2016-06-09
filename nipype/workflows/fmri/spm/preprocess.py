# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os

import nipype.algorithms.rapidart as ra
import nipype.interfaces.spm as spm
import nipype.interfaces.utility as niu
import nipype.pipeline.engine as pe
logger = pe.logger
from ....interfaces.matlab import no_matlab

from ...smri.freesurfer.utils import create_getmask_flow

def create_spm_preproc(name='preproc'):
    """Create an spm preprocessing workflow with freesurfer registration and
    artifact detection.

    The workflow realigns and smooths and registers the functional images with
    the subject's freesurfer space.

    Example
    -------

    >>> preproc = create_spm_preproc()
    >>> preproc.base_dir = '.'
    >>> preproc.inputs.inputspec.fwhm = 6
    >>> preproc.inputs.inputspec.subject_id = 's1'
    >>> preproc.inputs.inputspec.subjects_dir = '.'
    >>> preproc.inputs.inputspec.functionals = ['f3.nii', 'f5.nii']
    >>> preproc.inputs.inputspec.norm_threshold = 1
    >>> preproc.inputs.inputspec.zintensity_threshold = 3

    Inputs::

         inputspec.functionals : functional runs use 4d nifti
         inputspec.subject_id : freesurfer subject id
         inputspec.subjects_dir : freesurfer subjects dir
         inputspec.fwhm : smoothing fwhm
         inputspec.norm_threshold : norm threshold for outliers
         inputspec.zintensity_threshold : intensity threshold in z-score

    Outputs::

         outputspec.realignment_parameters : realignment parameter files
         outputspec.smoothed_files : smoothed functional files
         outputspec.outlier_files : list of outliers
         outputspec.outlier_stats : statistics of outliers
         outputspec.outlier_plots : images of outliers
         outputspec.mask_file : binary mask file in reference image space
         outputspec.reg_file : registration file that maps reference image to
                                 freesurfer space
         outputspec.reg_cost : cost of registration (useful for detecting misalignment)
    """

    """
    Initialize the workflow
    """

    workflow = pe.Workflow(name=name)

    """
    Define the inputs to this workflow
    """

    inputnode = pe.Node(niu.IdentityInterface(fields=['functionals',
                                                      'subject_id',
                                                      'subjects_dir',
                                                      'fwhm',
                                                      'norm_threshold',
                                                      'zintensity_threshold']),
                        name='inputspec')

    """
    Setup the processing nodes and create the mask generation and coregistration
    workflow
    """

    poplist = lambda x: x.pop()
    realign = pe.Node(spm.Realign(), name='realign')
    workflow.connect(inputnode, 'functionals', realign, 'in_files')
    maskflow = create_getmask_flow()
    workflow.connect([(inputnode, maskflow, [('subject_id','inputspec.subject_id'),
                                             ('subjects_dir', 'inputspec.subjects_dir')])])
    maskflow.inputs.inputspec.contrast_type = 't2'
    workflow.connect(realign, 'mean_image', maskflow, 'inputspec.source_file')
    smooth = pe.Node(spm.Smooth(), name='smooth')
    workflow.connect(inputnode, 'fwhm', smooth, 'fwhm')
    workflow.connect(realign, 'realigned_files', smooth, 'in_files')
    artdetect = pe.Node(ra.ArtifactDetect(mask_type='file',
                                          parameter_source='SPM',
                                          use_differences=[True,False],
                                          use_norm=True,
                                          save_plot=True),
                        name='artdetect')
    workflow.connect([(inputnode, artdetect,[('norm_threshold', 'norm_threshold'),
                                             ('zintensity_threshold',
                                              'zintensity_threshold')])])
    workflow.connect([(realign, artdetect, [('realigned_files', 'realigned_files'),
                                            ('realignment_parameters',
                                             'realignment_parameters')])])
    workflow.connect(maskflow, ('outputspec.mask_file', poplist), artdetect, 'mask_file')

    """
    Define the outputs of the workflow and connect the nodes to the outputnode
    """

    outputnode = pe.Node(niu.IdentityInterface(fields=["realignment_parameters",
                                                       "smoothed_files",
                                                       "mask_file",
                                                       "reg_file",
                                                       "reg_cost",
                                                       'outlier_files',
                                                       'outlier_stats',
                                                       'outlier_plots'
                                                       ]),
                         name="outputspec")
    workflow.connect([
            (maskflow, outputnode, [("outputspec.reg_file", "reg_file")]),
            (maskflow, outputnode, [("outputspec.reg_cost", "reg_cost")]),
            (maskflow, outputnode, [(("outputspec.mask_file", poplist), "mask_file")]),
            (realign, outputnode, [('realignment_parameters', 'realignment_parameters')]),
            (smooth, outputnode, [('smoothed_files', 'smoothed_files')]),
            (artdetect, outputnode,[('outlier_files', 'outlier_files'),
                                    ('statistic_files','outlier_stats'),
                                    ('plot_files','outlier_plots')])
            ])
    return workflow

from nipype.interfaces.nipy.preprocess import Trim

def create_preprocess_struct_to_mean_funct_4D_spm12(TR, wf_name='preprocess_struct_to_mean_funct_4D_spm12',mult = True, fast_segmenting = True,output_normalized_segmented_maps = True, smoothing = False, fwhm = [],slice_timing = False,  num_slices = 40, slice_code = 5, nb_scans_to_remove = 2, trimming = True):
    
    """ 
    Preprocessing old fashioned normalize struct -> mean funct with SPM12
    """
    preprocess = pe.Workflow(name=wf_name)

    
    
    inputnode = pe.Node(niu.IdentityInterface(fields=['functionals',
                                                      'struct']),
                        name='inputnode')
     
    #### trim
    
    if nb_scans_to_remove == 0:
        trimming = False
        
    if trimming == True:
        
        if mult == True:    
            trim = pe.MapNode(interface=Trim(), iterfield = ['in_file'],name ="trim")
            
        else:
            trim = pe.Node(interface=Trim(), name="trim")
            
        trim.inputs.begin_index = nb_scans_to_remove
        

    if slice_timing == True:
        
        #### sliceTiming
        sliceTiming = pe.Node(interface=spm.SliceTiming(), name="sliceTiming")
        sliceTiming.inputs.num_slices = num_slices
        sliceTiming.inputs.time_repetition = TR
        sliceTiming.inputs.time_acquisition = TR - TR/num_slices
        
        if slice_code == 5:  #for Siemens-even interleaved ascending
                
            sliceTiming.inputs.slice_order = range(2,num_slices+1,2) + range(1,num_slices+1,2)      #for Siemens-even interleaved ascending 
            #sliceTiming.inputs.ref_slice = num_slices-1
            sliceTiming.inputs.ref_slice = num_slices ### a verifier...
                
        elif slice_code == 2:  #for Siemens sequential_decreasing
                
            sliceTiming.inputs.slice_order = range(num_slices,0,-1)
            sliceTiming.inputs.ref_slice = int(num_slices/2.0)
              
        #sliceTiming.inputs.slice_order = range(1,42,2) + range(2,42,2)      #for Siemens-odd interleaved ascending
        #sliceTiming.inputs.slice_order = range(1,28+1)      #for bottom up slicing
        #sliceTiming.inputs.slice_order = range(28,0,-1)    #for top down slicing
        
        
    ##### realign
    realign = pe.Node(interface=spm.Realign(), name="realign")
    realign.inputs.register_to_mean = True
    
    coregister = pe.Node(interface=spm.Coregister(), name="coregister")
    coregister.inputs.jobtype = 'estimate'
   
    
    ############ Old fashionned segment with SPM12
   
    segment= pe.Node(interface=spm.Segment(), name="segment")
    
    if fast_segmenting == True:
        segment.inputs.gaussians_per_class = [1, 1, 1, 4] #(faster execution)
    
    
    if output_normalized_segmented_maps:
        segment.inputs.csf_output_type = [False,True, False]
        segment.inputs.gm_output_type = [False,True, False]
        segment.inputs.wm_output_type = [False,True, False]
        
    normalize_func = pe.Node(interface=spm.Normalize(), name = "normalize_func")
    normalize_func.inputs.jobtype = 'write'
    
    normalize_struct = pe.Node(interface=spm.Normalize(), name = "normalize_struct")
    normalize_struct.inputs.jobtype = 'write'
    
    if smoothing == True:
        smooth = pe.Node(interface=spm.Smooth(), name="smooth")
        smooth.inputs.fwhm = fwhm
    
    ### connect nodes
    
    if trimming == True:
        
        preprocess.connect(inputnode,'functionals',trim,'in_file')
        
        if slice_timing == True: 
            
            preprocess.connect(trim, 'out_file', sliceTiming,'in_files')
            preprocess.connect(sliceTiming, 'timecorrected_files', realign,'in_files')
        else: 
            preprocess.connect(trim, 'out_file', realign,'in_files')
    else:
        if slice_timing == True: 
            preprocess.connect(inputnode,'functionals', sliceTiming,'in_files')
            preprocess.connect(sliceTiming, 'timecorrected_files', realign,'in_files')
        else: 
            preprocess.connect(inputnode,'functionals', realign,'in_files')
    
    
    preprocess.connect(inputnode, 'struct', coregister,'source')
    preprocess.connect(realign,'mean_image',coregister,'target')
    
    preprocess.connect(coregister,'coregistered_source',segment,'data')
                       
                       
    preprocess.connect(realign,'realigned_files',normalize_func,'apply_to_files')
    preprocess.connect(segment,'transformation_mat', normalize_func, 'parameter_file')
    
    preprocess.connect(coregister,'coregistered_source', normalize_struct, 'apply_to_files')
    preprocess.connect(segment,'transformation_mat', normalize_struct, 'parameter_file')
    
    if smoothing == True:
        preprocess.connect(normalize_func, 'normalized_files',smooth,'in_files')
    
    return preprocess
    
        
    
    

def create_preprocess_funct_to_struct_4D_spm12(wf_name='preprocess_funct_to_struct_4D_spm12', mult = True, trimming = False, slice_timing = False, fast_segmenting = True, smoothing = False, output_normalized_segmented_maps = False, nb_scans_to_remove = 2, TR = 2.2, num_slices = 40, slice_code = 4,fwhm = [7.5,7.5,8]):
    """ 
    Preprocessing old fashioned normalize funct -> struct with SPM12
    """
    preprocess = pe.Workflow(name=wf_name)

    
    inputnode = pe.Node(niu.IdentityInterface(fields=['functionals',
                                                      'struct']),
                        name='inputnode')
     
    if nb_scans_to_remove != 0:
        trimming = False
        
    if trimming:
            
        print "Running trimming with {} volums removed".format(nb_scans_to_remove)
        #### trim
        if mult == True:
            trim = pe.MapNode(interface=Trim(), iterfield = ['in_file'],name ="trim")
        else:
            trim = pe.Node(interface=Trim(), name="trim")
            
        trim.inputs.begin_index = nb_scans_to_remove
    
        
    if slice_timing:
        
        #### sliceTiming
        sliceTiming = pe.Node(interface=spm.SliceTiming(), name="sliceTiming")
        sliceTiming.inputs.num_slices = num_slices
        sliceTiming.inputs.time_repetition = TR
        sliceTiming.inputs.time_acquisition = TR - TR/num_slices
        
        if slice_code == 5:  #for Siemens-even interleaved ascending
                
            sliceTiming.inputs.slice_order = range(2,num_slices+1,2) + range(1,num_slices+1,2)      #for Siemens-even interleaved ascending 
            #sliceTiming.inputs.ref_slice = num_slices-1
            sliceTiming.inputs.ref_slice = num_slices ### a verifier...
                
        elif slice_code == 2:  #for Siemens sequential_decreasing
                
            sliceTiming.inputs.slice_order = range(num_slices,0,-1)
            sliceTiming.inputs.ref_slice = int(num_slices/2.0)
              
        #sliceTiming.inputs.slice_order = range(1,42,2) + range(2,42,2)      #for Siemens-odd interleaved ascending
        #sliceTiming.inputs.slice_order = range(1,28+1)      #for bottom up slicing
        #sliceTiming.inputs.slice_order = range(28,0,-1)    #for top down slicing
        
    ##### realign
    realign = pe.Node(interface=spm.Realign(), name="realign")
    realign.inputs.register_to_mean = True
    
    if trimming:
        
        preprocess.connect(inputnode,'functionals',trim,'in_file')
        
        if slice_timing: 
            preprocess.connect(trim, 'out_file', sliceTiming,'in_files')
            preprocess.connect(sliceTiming, 'timecorrected_files', realign,'in_files')
        else: 
            preprocess.connect(trim, 'out_file', realign,'in_files')
    else:
        if slice_timing: 
            preprocess.connect(inputnode,'functionals', sliceTiming,'in_files')
            preprocess.connect(sliceTiming, 'timecorrected_files', realign,'in_files')
        else: 
            preprocess.connect(inputnode,'functionals', realign,'in_files')

    coregister = pe.Node(interface=spm.Coregister(), name="coregister")
    coregister.inputs.jobtype = 'estimate'
   
    preprocess.connect(inputnode, 'struct', coregister,'target')
    preprocess.connect(realign,'mean_image',coregister,'source')
    preprocess.connect(realign,'realigned_files',coregister,'apply_to_files')
    
    ############ SPM12 (Normalize12)
    #normalize = pe.Node(interface=spm.Normalize12(), name = "normalize")
    #normalize.inputs.jobtype = 'write'
    
    #preprocess.connect(coregister,'coregistered_files',normalize,'apply_to_files') ##SPM12 Normalize12
    
    ############ Old fashionned segment with SPM12
   
    segment= pe.Node(interface=spm.Segment(), name="segment")
    
    if fast_segmenting:
        segment.inputs.gaussians_per_class = [1, 1, 1, 4] #(faster execution)
    
    if output_normalized_segmented_maps:
        segment.inputs.csf_output_type = [False,True, False]
        segment.inputs.gm_output_type = [False,True, False]
        segment.inputs.wm_output_type = [False,True, False]
        
    preprocess.connect(inputnode, 'struct', segment,'data')
    
    ### normalise struct to MNI using segement transformation_matrix
    normalize_struct = pe.Node(interface=spm.Normalize(), name = "normalize_struct")
    normalize_struct.inputs.jobtype = 'write'
    
    preprocess.connect(inputnode, 'struct', normalize_struct,'apply_to_files')    
    preprocess.connect(segment,'transformation_mat', normalize_struct, 'parameter_file')
    
    ### normalise functionals to MNI using segement transformation_matrix
    normalize_func = pe.Node(interface=spm.Normalize(), name = "normalize_func")
    normalize_func.inputs.jobtype = 'write'
    
    preprocess.connect(coregister,'coregistered_files',normalize_func,'apply_to_files')    
    preprocess.connect(segment,'transformation_mat', normalize_func, 'parameter_file')
    
    if smoothing:
        
        ### smoothing
        smooth = pe.Node(interface=spm.Smooth(), name="smooth")
        smooth.inputs.fwhm = fwhm
        
    
        ### connect nodes
        preprocess.connect(normalize_func, 'normalized_files',smooth,'in_files')
    
    return preprocess
    
    

def create_preprocess_funct_4D_spm8(norm_template_file,wf_name='preprocess_funct_4D_spm8', TR = 2.0, num_slices = 40, slice_code = 5,fwhm = [7.5,7.5,8]):
    
    """
    Preprocessing with SPM8 from 4D file only based on functional scans
    Normlization is based on Normalize on EPI.nii 
    """
    
    preprocess = pe.Workflow(name=wf_name)
    
    
    #### sliceTiming
    sliceTiming = pe.Node(interface=spm.SliceTiming(), name="sliceTiming")
    sliceTiming.inputs.num_slices = num_slices
    sliceTiming.inputs.time_repetition = TR
    sliceTiming.inputs.time_acquisition = TR - TR/num_slices
    
    if slice_code == 5:  #for Siemens-even interleaved ascending
            
        sliceTiming.inputs.slice_order = range(2,num_slices+1,2) + range(1,num_slices+1,2)      #for Siemens-even interleaved ascending
        sliceTiming.inputs.ref_slice = num_slices-1
        
    #sliceTiming.inputs.slice_order = range(1,42,2) + range(2,42,2)      #for Siemens-odd interleaved ascending
    #sliceTiming.inputs.slice_order = range(1,28+1)      #for bottom up slicing
    #sliceTiming.inputs.slice_order = range(28,0,-1)    #for top down slicing
    
    
    #### realign
    realign = pe.Node(interface=spm.Realign(), name="realign")
    realign.inputs.register_to_mean = True
    
    #### normalize_func
    normalize_func = pe.Node(interface=spm.Normalize(), name = "normalize_func")
    normalize_func.inputs.jobtype = 'estwrite'
    normalize_func.inputs.template = norm_template_file
    
    
    #### smooth
    smooth = pe.Node(interface=spm.Smooth(), name="smooth")
    smooth.inputs.fwhm = fwhm
    
    ### connecting nodes
    preprocess.connect(sliceTiming,'timecorrected_files',realign,'in_files')
    preprocess.connect(realign,'mean_image',normalize_func,'source')
    preprocess.connect(realign, 'realigned_files', normalize_func, 'apply_to_files')
    preprocess.connect(normalize_func, 'normalized_files',smooth,'in_files')
    
    return preprocess

    ########################################### Nipype original pipelines
    
def create_vbm_preproc(name='vbmpreproc'):
    """Create a vbm workflow that generates DARTEL-based warps to MNI space

    Based on: http://www.fil.ion.ucl.ac.uk/~john/misc/VBMclass10.pdf

    Example
    -------

    >>> preproc = create_vbm_preproc()
    >>> preproc.inputs.inputspec.fwhm = 8
    >>> preproc.inputs.inputspec.structural_files = [os.path.abspath('s1.nii'), os.path.abspath('s3.nii')]
    >>> preproc.inputs.inputspec.template_prefix = 'Template'
    >>> preproc.run() # doctest: +SKIP

    Inputs::

         inputspec.structural_files : structural data to be used to create templates
         inputspec.fwhm: single of triplet for smoothing when normalizing to MNI space
         inputspec.template_prefix : prefix for dartel template

    Outputs::

         outputspec.normalized_files : normalized gray matter files
         outputspec.template_file : DARTEL template
         outputspec.icv : intracranial volume (cc - assuming dimensions in mm)

    """

    workflow = pe.Workflow(name=name)

    """
    Define the inputs to this workflow
    """

    inputnode = pe.Node(niu.IdentityInterface(fields=['structural_files',
                                                      'fwhm',
                                                      'template_prefix']),
                        name='inputspec')

    dartel_template = create_DARTEL_template()

    workflow.connect(inputnode, 'template_prefix', dartel_template, 'inputspec.template_prefix')
    workflow.connect(inputnode, 'structural_files', dartel_template, 'inputspec.structural_files')

    norm2mni = pe.Node(spm.DARTELNorm2MNI(modulate=True), name='norm2mni')
    workflow.connect(dartel_template, 'outputspec.template_file', norm2mni, 'template_file')
    workflow.connect(dartel_template, 'outputspec.flow_fields', norm2mni, 'flowfield_files')

    def getclass1images(class_images):
        class1images = []
        for session in class_images:
            class1images.extend(session[0])
        return class1images

    workflow.connect(dartel_template, ('segment.native_class_images', getclass1images), norm2mni, 'apply_to_files')
    workflow.connect(inputnode, 'fwhm', norm2mni, 'fwhm')

    def compute_icv(class_images):
        from nibabel import load
        from numpy import prod
        icv = []
        for session in class_images:
            voxel_volume = prod(load(session[0][0]).get_header().get_zooms())
            img = load(session[0][0]).get_data() + \
                load(session[1][0]).get_data() + \
                load(session[2][0]).get_data()
            img_icv = (img>0.5).astype(int).sum()*voxel_volume*1e-3
            icv.append(img_icv)
        return icv

    calc_icv = pe.Node(niu.Function(function=compute_icv,
                                    input_names=['class_images'],
                                    output_names=['icv']),
                       name='calc_icv')

    workflow.connect(dartel_template, 'segment.native_class_images', calc_icv, 'class_images')

    """
    Define the outputs of the workflow and connect the nodes to the outputnode
    """

    outputnode = pe.Node(niu.IdentityInterface(fields=["normalized_files",
                                                       "template_file",
                                                       "icv"
                                                       ]),
                         name="outputspec")
    workflow.connect([(dartel_template, outputnode, [('outputspec.template_file','template_file')]),
                      (norm2mni, outputnode, [("normalized_files", "normalized_files")]),
                      (calc_icv, outputnode, [("icv", "icv")]),
                      ])

    return workflow

def create_DARTEL_template(name='dartel_template'):
    """Create a vbm workflow that generates DARTEL-based template


    Example
    -------

    >>> preproc = create_DARTEL_template()
    >>> preproc.inputs.inputspec.structural_files = [os.path.abspath('s1.nii'), os.path.abspath('s3.nii')]
    >>> preproc.inputs.inputspec.template_prefix = 'Template'
    >>> preproc.run() # doctest: +SKIP

    Inputs::

         inputspec.structural_files : structural data to be used to create templates
         inputspec.template_prefix : prefix for dartel template

    Outputs::

         outputspec.template_file : DARTEL template
         outputspec.flow_fields : warps from input struct files to the template

    """

    workflow = pe.Workflow(name=name)

    inputnode = pe.Node(niu.IdentityInterface(fields=['structural_files', 'template_prefix']),
                        name='inputspec')

    segment = pe.MapNode(spm.NewSegment(),
                             iterfield=['channel_files'],
                             name='segment')
    workflow.connect(inputnode, 'structural_files', segment, 'channel_files')

    version = spm.Info.version()
    if version:
        spm_path = version['path']
        if version['name'] == 'SPM8':
            tissue1 = ((os.path.join(spm_path,'toolbox/Seg/TPM.nii'), 1), 2, (True,True), (False, False))
            tissue2 = ((os.path.join(spm_path,'toolbox/Seg/TPM.nii'), 2), 2, (True,True), (False, False))
            tissue3 = ((os.path.join(spm_path,'toolbox/Seg/TPM.nii'), 3), 2, (True,False), (False, False))
            tissue4 = ((os.path.join(spm_path,'toolbox/Seg/TPM.nii'), 4), 3, (False,False), (False, False))
            tissue5 = ((os.path.join(spm_path,'toolbox/Seg/TPM.nii'), 5), 4, (False,False), (False, False))
            tissue6 = ((os.path.join(spm_path,'toolbox/Seg/TPM.nii'), 6), 2, (False,False), (False, False))
        elif version['name'] == 'SPM12':
            spm_path = version['path']
            tissue1 = ((os.path.join(spm_path,'tpm/TPM.nii'), 1), 1, (True,True), (False, False))
            tissue2 = ((os.path.join(spm_path,'tpm/TPM.nii'), 2), 1, (True,True), (False, False))
            tissue3 = ((os.path.join(spm_path,'tpm/TPM.nii'), 3), 2, (True,False), (False, False))
            tissue4 = ((os.path.join(spm_path,'tpm/TPM.nii'), 4), 3, (False,False), (False, False))
            tissue5 = ((os.path.join(spm_path,'tpm/TPM.nii'), 5), 4, (False,False), (False, False))
            tissue6 = ((os.path.join(spm_path,'tpm/TPM.nii'), 6), 2, (False,False), (False, False))
        else:
            logger.critical('Unsupported version of SPM')

        segment.inputs.tissues = [tissue1, tissue2, tissue3, tissue4, tissue5, tissue6]
    else:
        logger.critical('SPM not found')

    dartel = pe.Node(spm.DARTEL(), name='dartel')

    """Get the gray and white segmentation classes generated by NewSegment
    """

    def get2classes(dartel_files):
        class1images = []
        class2images = []
        for session in dartel_files:
            class1images.extend(session[0])
            class2images.extend(session[1])
        return [class1images, class2images]

    workflow.connect(segment, ('dartel_input_images', get2classes), dartel, 'image_files')
    workflow.connect(inputnode, 'template_prefix', dartel, 'template_prefix')

    outputnode = pe.Node(niu.IdentityInterface(fields=["template_file",
                                                       "flow_fields"
                                                       ]),
                         name="outputspec")
    workflow.connect([
            (dartel, outputnode, [('final_template_file','template_file'),
                                  ('dartel_flow_fields', 'flow_fields')]),
            ])

    return workflow
