import pickle
import time
from functools import partial
import os
import xarray as xr
from tabulate import tabulate

from memristor_learning.Networks import *

# parameters to search
start_r_0 = 1
end_r_0 = 4
num_r_0 = 10
start_r_1 = 5
end_r_1 = 9
num_r_1 = 10
start_a = -0.001
end_a = -1
num_a = 10

r_0_list = np.logspace( start_r_0, end_r_0, num=num_r_0 )
r_1_list = np.logspace( start_r_1, end_r_1, num=num_r_1 )
a_list = np.linspace( start_a, end_a, num=num_a )
total_iterations = num_a * num_r_0 * num_r_1
assert (end_r_0 < start_r_1)
print( "Total iterations:", total_iterations )

dims = [ "r_0", "r_1", "a" ]
coords = dict.fromkeys( dims, 0 )
coords[ dims[ 0 ] ] = r_0_list
coords[ dims[ 1 ] ] = r_1_list
coords[ dims[ 2 ] ] = a_list

data = [ ]
results_dict = nested_dict( len( dims ), dict )

if os.path.exists( "../data/progress.txt" ):
    os.remove( "../data/progress.txt" )

start_time = time.time()
curr_iteration = 0
for i, r_0 in enumerate( r_0_list ):
    data.append( [ ] )
    for j, r_1 in enumerate( r_1_list ):
        data[ i ].append( [ ] )
        for k, a in enumerate( a_list ):
            net = SupervisedLearning( memristor_controller=MemristorArray,
                                      memristor_model=
                                      partial( MemristorPair, model=
                                      partial( OnedirectionalPowerlawMemristor, a=a, r_0=r_0, r_1=r_1 ) ),
                                      seed=0,
                                      neurons=4,
                                      verbose=True,
                                      generate_figures=False )
            res = net()
            print( res[ "mse" ] )
            data[ i ][ j ].append( res[ "mse" ] )
            results_dict[ r_0 ][ r_1 ][ a ] = res
            curr_iteration += 1
            print( f"{curr_iteration}/{total_iterations}: {r_0}, {r_1}, {a}\n" )
            
            with open( "../data/progress.txt", "a+" ) as f:
                f.write( f"{curr_iteration}/{total_iterations}: {r_0}, {r_1}, {a}\n" )

# for i, x in enumerate( results ):
#     x[ "fig_pre_post" ].show()
#     time.sleep( 2 )
time_taken = time.time() - start_time
dir_name, dir_images = make_timestamped_dir()
dataf = xr.DataArray( data=data, dims=dims, coords=coords )
with open( f"{dir_name}mse.pkl", "wb" ) as f:
    pickle.dump( dataf, f )
table = [ [ "a", start_a, end_a, num_a ],
          [ "r_0", start_r_0, end_r_0, num_r_0 ],
          [ "r_1", start_r_1, end_r_1, num_r_1 ] ]
headers = [ "Parameter", "Start", "End", "Number" ]
with open( f"{dir_name}param.txt", "w+" ) as f:
    f.write( tabulate( table, headers=headers ) )
    f.write( f"\n\nTotal time: {datetime.timedelta( seconds=time_taken )}" )
    f.write( f"\nTime per iteration: {round( time_taken / total_iterations, 2 )} s" )
    
    # loaded = pickle.load( open( f"{dir_name}mse.pkl", "rb" ) )