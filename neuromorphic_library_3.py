import nengo
import numpy as np


def plot_network( model ):
    from nengo_extras import graphviz
    
    net = graphviz.net_diagram( model )
    from graphviz import Source
    
    s = Source( net, filename="./net.png", format="png" )
    s.view()


def plot_pre_post( sim, pre, post, input, error ):
    import datetime
    import matplotlib.pyplot as plt
    
    # plot input, neural representations and error
    plt.figure()
    # plt.suptitle( datetime.datetime.now().strftime( '%H:%M:%S %d-%m-%Y' ) )
    plt.subplot( 2, 1, 1 )
    plt.plot( sim.trange(), sim.data[ input ], c="k", label="Input" )
    plt.plot( sim.trange(), sim.data[ pre ], c="b", label="Pre" )
    plt.plot( sim.trange(), sim.data[ post ], c="g", label="Post" )
    plt.title( "Values" )
    plt.legend( loc='best' )
    plt.subplot( 2, 1, 2 )
    plt.plot( sim.trange(), error, c="r" )
    plt.title( "Error" )
    plt.show()


def plot_ensemble_spikes( sim, name, ensemble, input=None ):
    import datetime
    from nengo.utils.matplotlib import rasterplot
    import matplotlib.pyplot as plt
    
    # plot spikes from pre
    plt.figure()
    # plt.suptitle( datetime.datetime.now().strftime( '%H:%M:%S %d-%m-%Y' ) )
    fig, ax1 = plt.subplots()
    ax1 = plt.subplot( 1, 1, 1 )
    rasterplot( sim.trange(), sim.data[ ensemble ], ax1 )
    ax1.set_xlim( 0, max( sim.trange() ) )
    ax1.set_ylabel( 'Neuron' )
    ax1.set_xlabel( 'Time (s)' )
    if input:
        ax2 = plt.twinx()
        ax2.plot( sim.trange(), sim.data[ input ], c="k" )
    plt.title( name + " neural activity" )
    plt.show()


class MemristorArray:
    def __init__( self, post_encoders, in_size, out_size, dimensions, type, learning_rate=10e-4,
                  dt=0.001, r0=100, r1=2.5 * 10**8, a=-0.128, b=-0.522 ):
        
        self.input_size = in_size
        self.pre_dimensions = dimensions[ 0 ]
        self.post_dimensions = dimensions[ 1 ]
        self.output_size = out_size
        
        assert type == "single" or type == "pair"
        self.encoders = post_encoders
        self.learning_rate = learning_rate
        self.dt = dt
        self.filter = nengo.Lowpass( tau=0.005 )
        self.type = type
        
        # error buffer for delayed updates
        
        # save error for analysis
        self.error_history = [ ]
        
        # to hold future weights
        self.weights = np.zeros( (self.output_size, self.input_size), dtype=np.float )
        
        # create memristor array that implement the weights
        self.memristors = np.empty( (self.output_size, self.input_size), dtype=Memristor )
        for i in range( self.output_size ):
            for j in range( self.input_size ):
                if self.type == "single":
                    self.memristors[ i, j ] = Memristor( "excitatory", r0, r1, a, b )
                if self.type == "pair":
                    self.memristors[ i, j ] = MemristorPair( self.input_size, self.output_size, r0, r1, a, b )
                self.weights[ i, j ] = self.memristors[ i, j ].get_state( value="conductance", scaled=True )
    
    def __call__( self, t, x ):
        input_activities = x[ :self.input_size ]
        pre_filtered = self.filter.filt( input_activities )
        # squash error to zero under a certain threshold or learning rule keeps running indefinitely
        error = x[ self.input_size: ] if abs( x[ self.input_size: ] ) > 10**-5 else 0
        alpha = self.learning_rate * self.dt / self.input_size
        
        # we are adjusting weights so calculate local error
        local_error = alpha * np.dot( self.encoders, error )
        self.error_history.append( error )
        
        # squash spikes to False (0) or True (100/1000 ...) or everything is always adjusted
        spiked = np.array( np.rint( input_activities ), dtype=bool )
        
        # TODO broken
        for j in range( self.output_size ):
            for i in range( self.input_size ):
                # save resistance states for later analysis
                self.memristors[ j, i ].save_state()
        
        # we only need to update the weights for the neurons that spiked so we filter for their columns
        if spiked.any():
            for j in range( self.output_size ):
                for i in np.nditer( np.where( spiked ) ):
                    self.weights[ j, i ] = self.memristors[ j, i ].pulse( local_error[ j ], value="conductance" )
        
        # calculate the output at this timestep
        return_value = np.dot( self.weights, input_activities )
        
        return return_value
    
    def get_components( self ):
        return self.memristors.flatten()
    
    def plot_state( self, sim, value, err_probe=None, combined=False ):
        import datetime
        import matplotlib.pyplot as plt
        from matplotlib.pyplot import cm
        from nengo.utils.matplotlib import rasterplot
        
        # plot memristor resistance and error
        plt.figure()
        # plt.suptitle( datetime.datetime.now().strftime( '%H:%M:%S %d-%m-%Y' ) )
        if not combined:
            fig, axes = plt.subplots()
        if combined:
            fig, axes = plt.subplots( self.output_size, self.input_size )
        plt.xlabel( "Post neurons on rows\nPre neurons on columns" )
        plt.ylabel( "Post neurons on columns" )
        # fig.suptitle( "Memristor " + value, fontsize=16 )
        colour = iter( cm.rainbow( np.linspace( 0, 1, self.memristors.size ) ) )
        for i in range( self.memristors.shape[ 0 ] ):
            for j in range( self.memristors.shape[ 1 ] ):
                c = next( colour )
                if not combined:
                    self.memristors[ i, j ].plot_state( value, i, j, sim.trange(), axes, c, combined )
                if combined:
                    self.memristors[ i, j ].plot_state( value, i, j, sim.trange(), axes[ i, j ], c, combined )
        if err_probe:
            ax2 = plt.twinx()
            ax2.plot( sim.trange(), sim.data[ err_probe ], c="r", label="Error" )
        plt.show()
    
    def get_error( self ):
        return self.error_history


class MemristorPair():
    def __init__( self, in_size, out_size, r0=100, r1=2.5 * 10**8, a=-0.128, b=-0.522 ):
        # input/output sizes
        self.input_size = in_size
        self.output_size = out_size
        
        # instantiate memristor pair
        self.mem_plus = Memristor( "excitatory", r0, r1, a, b )
        self.mem_minus = Memristor( "inhibitory", r0, r1, a, b )
    
    def pulse( self, err, value, scaled=True ):
        if err < 0:
            self.mem_plus.pulse()
        if err > 0:
            self.mem_minus.pulse()
        
        self.save_state()
        
        return self.mem_plus.get_state( value, scaled ) - self.mem_minus.get_state( value, scaled )
    
    def get_state( self, value, scaled ):
        return (self.mem_plus.get_state( value, scaled ) - self.mem_minus.get_state( value, scaled ))
    
    def save_state( self ):
        self.mem_plus.save_state()
        self.mem_minus.save_state()
    
    def plot_state( self, value, i, j, range, ax, c, combined=False ):
        if value == "resistance":
            tmp_plus = self.mem_plus.history
            tmp_minus = self.mem_minus.history
        if value == "conductance":
            tmp_plus = np.divide( 1, self.mem_plus.history )
            tmp_minus = np.divide( 1, self.mem_minus.history )
        ax.plot( range, tmp_plus, c="r", label='Excitatory' )
        ax.plot( range, tmp_minus, c="b", label='Inhibitory' )
        if not combined:
            ax.annotate( str( j + 1 ) + "->" + str( i + 1 ), xy=(range[ 0 ], tmp_plus[ 0 ]), c="r" )
            ax.annotate( str( j + 1 ) + "->" + str( i + 1 ), xy=(range[ 0 ], tmp_minus[ 0 ]), c="b" )
        if combined:
            ax.set_title( str( j + 1 ) + "->" + str( i + 1 ) )
            ax.label_outer()
            ax.set_yticklabels( [ ] )


class Memristor:
    def __init__( self, type, r0=100, r1=2.5 * 10**8, a=-0.128, b=-0.522 ):
        # set parameters of device
        self.r_min = r0
        self.r_max = r1
        self.a = a
        self.b = b
        
        self.n = 0
        # save resistance history for later analysis
        self.history = [ ]
        
        assert type == "inhibitory" or type == "excitatory"
        self.type = type
        if self.type == "inhibitory":
            # initialise memristor to highest resistance state
            self.r_curr = self.r_max
        if self.type == "excitatory":
            # initialise memristor to random low resistance state
            import random
            self.r_curr = random.randrange( 5.0 * 10**7, 15.0 * 10**7 )
        
        # Weight initialisation
        import random
        # self.r_curr = random.uniform( 10**7, 2.5 * 10**8 )
        # self.r_curr = self.r_max
    
    # pulse the memristor with a tension
    def pulse( self, V=0.1 ):
        c = self.a + self.b * V
        self.r_curr = self.r_min + self.r_max * (((self.r_curr - self.r_min) / self.r_max)**(1 / c) + 1)**c
        
        return self.r_curr
    
    def get_state( self, value="conductance", scaled=True, gain=10**4 ):
        epsilon = np.finfo( float ).eps
        
        if value == "conductance":
            g_curr = 1.0 / self.r_curr
            g_min = 1.0 / self.r_max
            g_max = 1.0 / self.r_min
            if scaled:
                ret_val = ((g_curr - g_min) / (g_max - g_min)) + epsilon
            else:
                ret_val = g_curr + epsilon
        
        if value == "resistance":
            if scaled:
                ret_val = ((self.r_curr - self.r_min) / (self.r_max - self.r_min)) + epsilon
            else:
                ret_val = self.r_curr + epsilon
        
        return gain * ret_val
    
    def save_state( self ):
        self.history.append( self.r_curr )
    
    def plot_state( self, value, i, j, range, ax, c ):
        if value == "resistance":
            tmp = self.history
        if value == "conductance":
            tmp = np.divide( 1.0, self.history )
        
        ax.plot( range, tmp, c=c )
        ax.annotate( "(" + str( i ), xy=(10, 10) )
