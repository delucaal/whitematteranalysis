#!/Library/Frameworks/EPD64.framework/Versions/Current/bin/ipython

import os
import glob
import matplotlib.pyplot as plt
import numpy

import vtk

import whitematteranalysis as wma

import multiprocessing
parallel_jobs = multiprocessing.cpu_count()
print 'CPUs detected:', parallel_jobs
parallel_jobs *= 2
print 'Using two threads per CPU:', parallel_jobs

indir = '/Users/odonnell/Dropbox/Coding/OUTPUTS/test_scale_tracts/GAUSSIAN/sigma20_weight_greater_2'
#outdir = '/Users/odonnell/Dropbox/Coding/OUTPUTS/test_scale_tracts/GAUSSIAN/test_reg_tues_jan31'
outdir = '/Users/odonnell/Dropbox/Coding/OUTPUTS/MICCAI2012/test_reg_feb_2'
outdir = '.'

input_mask = "{0}/*.vtp".format(indir)
input_poly_datas = glob.glob(input_mask)
#input_poly_datas = input_poly_datas[0:5]
input_poly_datas = input_poly_datas[0:10]
print input_poly_datas

## parameters to test
#number_of_fibers = 150
#number_of_fibers_step_one = 50
#number_of_fibers_step_two = 75
#number_of_fibers_step_three = 100
#maxfun=200,

def test_registration_parameters(input_poly_datas, outdir, number_of_fibers=150,
    number_of_fibers_per_step=[75, 100, 100],
    parallel_jobs=2,
    points_per_fiber=5,
    sigma=20,
    maxfun=150,
    distance_method='Hausdorff',
    final_number_of_fibers=250):

    minimum_length = 60
    number_of_fibers_step_one = number_of_fibers_per_step[0]
    number_of_fibers_step_two = number_of_fibers_per_step[1]
    number_of_fibers_step_three = number_of_fibers_per_step[2]

    print 'Read and preprocess'
    input_pds = list()
    for fname in input_poly_datas:
        print fname
        pd = wma.io.read_polydata(fname)
        pd3 = wma.filter.downsample(pd, number_of_fibers)
        input_pds.append(pd3)
 
    # view input data
    #ren = wma.registration_functions.view_polydatas(input_pds)

    # create registration object and apply settings
    register = wma.congeal.CongealTractography()
    register.parallel_jobs = parallel_jobs
    register.threshold = 0
    register.points_per_fiber = points_per_fiber
    register.fiber_sample_size = number_of_fibers_step_one
    register.distance_method = distance_method
    register.sigma = sigma
    
    # add inputs to the registration
    for pd in input_pds:
        register.add_subject(pd)

    # view downsampled fibers
    #model_pds=list()
    #for subj in register._subjects:
    #    model_pds.append(subj._original_fibers.convert_to_polydata())
    #ren = wma.registration_functions.view_polydatas(model_pds)

    # RUN registration (initial)
    register.sigma = sigma
    register.maxfun = maxfun

    # run the basic iteration of translate, rotate, scale
    register.translate_only()
    register.compute()
    register.rotate_only()
    register.compute()
    register.scale_only()
    register.compute()

    #if 0:
    # run the basic iteration of translate, rotate, scale AGAIN
    register.translate_only()
    register.compute()
    register.rotate_only()
    register.compute()
    register.scale_only()
    register.compute()

    if 0:
        # run the basic iteration of translate, rotate, scale AGAIN
        register.translate_only()
        register.compute()
        register.rotate_only()
        register.compute()
        register.scale_only()
        register.compute()
    
    # view output data from this big iteration
    output_pds = wma.registration_functions.transform_polydatas(input_pds, register)
    ren = wma.registration_functions.view_polydatas(output_pds)
    ren.save_views(outdir)
    
    plt.figure() # to avoid all results on same plot
    plt.plot(range(len(register.objective_function_values)), register.objective_function_values)
    plt.savefig(os.path.join(outdir, 'objective_function.pdf'))

    # calculate measures of success
    # number of clusters inherent at some scale. Pick 5mm...
    # must re-read input data and apply transforms
    print 'Read and preprocess'
    input_full_pds = list()
    for fname in input_poly_datas:
        print fname
        pd = wma.io.read_polydata(fname)
        pd3 = wma.filter.downsample(pd, final_number_of_fibers)
        input_full_pds.append(pd3)

    output_full_pds = wma.registration_functions.transform_polydatas(input_full_pds, register)
    
    appender = vtk.vtkAppendPolyData()
    for pd in output_full_pds:
        appender.AddInput(pd)
    appender.Update()
    pd_out = appender.GetOutput()
    pd_centroids, count, pdclusters, cluster_num, cluster_count = wma.filter.anisotropic_smooth(pd_out, 5.0, points_per_fiber=25, n_jobs=parallel_jobs)
    
    # return the registration information
    return register, pd_centroids, count, pdclusters, cluster_num, cluster_count 

# settings to test
range_number_of_fibers = [100, 150, 200, 250]
#range_fibers_step_one = [50, 100, 150]
range_points_per_fiber = [3, 5, 9, 21]
#range_sigma = [5, 10, 15, 20, 25, 30, 35, 40]
range_sigma = [5, 10, 20, 30, 40]

#range_sigma = range_sigma[0:2]

#range_number_of_fibers = [100, 200]
#range_sigma = [30, 35, 40]

#range_number_of_fibers = [100, 200]
#range_sigma = [30, 40]

idx = 0
for sigma in range_sigma:
    for number_of_fibers in range_number_of_fibers:
        for points_per_fiber in range_points_per_fiber:
            outdir_current =  os.path.join(outdir, 'test_{0}'.format(idx))
            if not os.path.exists(outdir_current):
                os.makedirs(outdir_current)
            [register, pd_centroids, count, pdclusters, cluster_num, cluster_count] = \
                test_registration_parameters(input_poly_datas, outdir_current, sigma=sigma, \
                                            number_of_fibers=number_of_fibers,
                                            points_per_fiber=points_per_fiber,
                    parallel_jobs=parallel_jobs)
            f = open(os.path.join(outdir_current, 'count.txt'), 'w')
            f.write('{0}\n'.format(len(count)))
            f.close()
            f = open(os.path.join(outdir_current, 'params.txt'), 'w')
            f.write('sigma:{0}\n'.format(sigma))
            f.write('number_of_fibers:{0}\n'.format(number_of_fibers))
            f.write('points_per_fiber:{0}\n'.format(points_per_fiber))
            f.close()
            idx += 1

count_list = list()
sigma_list = list()
number_of_fibers_list = list()
idx = 0
for sigma in range_sigma:
    for number_of_fibers in range_number_of_fibers:
        outdir_current =  os.path.join(outdir, 'test_{0}'.format(idx))
        f = open(os.path.join(outdir_current, 'count.txt'), 'r')
        count_list.append(int(f.read()))
        f.close()
        sigma_list.append(sigma)
        number_of_fibers_list.append(number_of_fibers)
        idx += 1
    
plt.figure() # to avoid all results on same plot
plt.plot(sigma_list, count_list,'o')
plt.savefig(os.path.join(outdir, 'count_vs_sigma.pdf'))
plt.figure() # to avoid all results on same plot
plt.plot(number_of_fibers_list, count_list,'o')
plt.savefig(os.path.join(outdir, 'count_vs_numfibers.pdf'))

        