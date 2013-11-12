import os
import glob
import matplotlib.pyplot as plt
import numpy
import scipy.stats

import vtk

import whitematteranalysis as wma

import multiprocessing

execfile('/Users/odonnell/Dropbox/Coding/Python/WhiteMatterAnalysis/bin/miccai-stats-paper/test_compute_FA.py')

# create some polydata objects to view the results
def fiber_list_to_fiber_array(fiber_list):
    fiber_array = wma.fibers.FiberArray()    
    fiber_array.number_of_fibers = len(fiber_list)
    fiber_array.points_per_fiber = len(fiber_list[0].r)
    dims = [fiber_array.number_of_fibers, fiber_array.points_per_fiber]
    # fiber data
    fiber_array.fiber_array_r = numpy.zeros(dims)
    fiber_array.fiber_array_a = numpy.zeros(dims)
    fiber_array.fiber_array_s = numpy.zeros(dims)
    curr_fidx = 0
    for curr_fib in fiber_list:
        fiber_array.fiber_array_r[curr_fidx] = curr_fib.r
        fiber_array.fiber_array_a[curr_fidx] = curr_fib.a
        fiber_array.fiber_array_s[curr_fidx] = curr_fib.s
        curr_fidx += 1
    return fiber_array


def add_array_to_polydata(pd, array, array_name='Test', array_type='Cell'):
    out_array = vtk.vtkFloatArray()
    for idx in range(len(array)):
        out_array.InsertNextTuple1(array[idx])
    out_array.SetName(array_name)
    ret = pd.GetCellData().AddArray(out_array)
    print ret
    pd.GetCellData().SetActiveScalars(array_name)
    return(pd)


parallel_jobs = multiprocessing.cpu_count()
print 'CPUs detected:', parallel_jobs
#parallel_jobs *= 3
#parallel_jobs = 101
parallel_jobs = 15
#parallel_jobs = 10
print 'Using N jobs:', parallel_jobs

#group_indices = [1, 0, 1, 0, 0, 1, 1, 0]
# 1 T, 2 C, 3 T, 4 C, 5 C, 6 T, 7 T, 8 C

execfile('/Users/odonnell/Dropbox/Coding/Python/WhiteMatterAnalysis/bin/miccai-stats-paper/test_compute_FA.py')

#indir = '/Users/odonnell/Dropbox/Coding/OUTPUTS/MICCAI2012/tbi_with_scalars'
indir = '/Users/odonnell/Desktop/OLD-Results-MICCAI-notused/tbi_with_scalars'

input_mask = "{0}/*.vtk".format(indir)
input_poly_datas = glob.glob(input_mask)

print input_poly_datas

input_pds = list()
input_pds_downsampled = list()

#number_of_fibers_per_subject = 3000
#number_of_fiber_centroids = 1000
# this is about 2.4 GB of memory for the distances...
number_of_fibers_per_subject = 6000
number_of_fiber_centroids = 2000
number_of_subjects = len(input_poly_datas)
points_per_fiber = 30

# this is to produce the files with scalars
if 0:
    for fname in input_poly_datas:
        print fname
        pd = wma.io.read_polydata(fname)
        pd, fa_lines_list, fa_avg_list = compute_scalar_measures(pd)
        fname2 =  'scalars_' + os.path.basename(fname)
        wma.io.write_polydata(pd, fname2)

# read in ones with scalars already
# this is SLOW
for fname in input_poly_datas:
    print fname
    pd = wma.io.read_polydata(fname)
    input_pds.append(pd)

# downsample for analysis
input_mean_fas_per_subject = list()
input_pds_downsampled = list()
downsample_indices = list()
for pd in input_pds:
    pd2, fiber_indices = wma.filter.downsample(pd, number_of_fibers_per_subject,return_indices=True)
    input_pds_downsampled.append(pd2)
    downsample_indices.append(fiber_indices)

# convert to arrays for dist and averaging

# use entire appended polydata (perhaps in future compute per-subject)
print 'Appending inputs into one polydata'
appender = vtk.vtkAppendPolyData()
for pd in input_pds_downsampled:
    appender.AddInputData(pd)
appender.Update()
print 'Done appending inputs into one polydata'

# convert to array representation
print 'Converting fibers to array representation for dist and averaging'
fiber_array = wma.fibers.FiberArray()
fiber_array.convert_from_polydata(appender.GetOutput(), points_per_fiber)
print 'Done converting fibers to array representation for dist and averaging'
 
   

# random sample of fibers for distance computation. random centroids.
total_number_of_fibers = number_of_fibers_per_subject*number_of_subjects
fiber_sample = numpy.random.permutation(total_number_of_fibers - 1)
fiber_sample = fiber_sample[0:number_of_fiber_centroids]

# compute dists
# find the sample's distances to all other fibers
distances = numpy.zeros([number_of_fiber_centroids, total_number_of_fibers])

for idx in range(number_of_fiber_centroids):
    print idx, '/', number_of_fiber_centroids
    fiber = fiber_array.get_fiber(fiber_sample[idx])
    distances[idx,:] = wma.similarity.fiber_distance(fiber, fiber_array, threshold=0, distance_method='Hausdorff')


# grab scalars of interest
input_min_fa_per_subject = list()
input_max_fa_per_subject = list()
input_mean_fa_per_subject = list()
pidx = 0
for pd in input_pds:
    print pidx, '----------------------------------------------------------'
    pd = compute_min_max_mean_array_along_lines(pd, 'FA', 'min_FA', 'max_FA', 'mean_FA')
    min_fa = pd.GetCellData().GetArray('min_FA')
    max_fa = pd.GetCellData().GetArray('max_FA')
    mean_fa = pd.GetCellData().GetArray('mean_FA')    
    min_fa_subj = list()
    max_fa_subj = list()
    mean_fa_subj = list()
    fiber_indices = downsample_indices[pidx]
    for idx in fiber_indices:
        min_fa_subj.append(min_fa.GetTuple1(idx))
        max_fa_subj.append(max_fa.GetTuple1(idx))
        mean_fa_subj.append(mean_fa.GetTuple1(idx))
    input_min_fa_per_subject.append(min_fa_subj)    
    input_max_fa_per_subject.append(max_fa_subj)    
    input_mean_fa_per_subject.append(mean_fa_subj)    
    pidx += 1


