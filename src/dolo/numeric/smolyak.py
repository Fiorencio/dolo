import numpy as np

from operator import mul

from operator import mul

from itertools import product

from scipy import optimize

from chebychev import cheb_extrema,chebychev,chebychev2

def enum(d,l):
    r = range(l)
    b = l - 1
    #stupid :
    res = []
    for maximum in range(b+1):
        res.extend( [e for e in product(r, repeat=d ) if sum(e)==maximum ] )
    return res

def build_indices_levels(l):
    return [(0,)] + [(1,2)] + [ tuple(range(2**(i-1)+1, 2**(i)+1)) for i in range(2,l) ]
    
def build_basic_grids(l):
    ll = [ np.array( [0.5] ) ]
    ll.extend( [ np.linspace(0.0,1.0,2**(i)+1) for i in range(1,l) ]  )
    ll = [ - np.cos( e * np.pi ) for e in ll]
    incr = [[0.0],[-1.0,1.0]]
    for i in range(2,len(ll)):
        t = ll[i]
        tt =  [ t[2*n+1] for n in range( (len(t)-1)/2 ) ]
        incr.append( tt )
    incr = [np.array(i) for i in incr]
    return [ll,incr]

def smolyak_grids(d,l):
    
    ret,incr = build_basic_grids(l)
    tab =  build_indices_levels(l)
    
    eee =  [ [ tab[i] for i in e] for e in enum( d, l) ]
    smolyak_indices = []
    for ee in eee:
        smolyak_indices.extend( [e for e in product( *ee ) ] )
    
    fff =  [ [ incr[i] for i in e] for e in enum( d, l) ]
    smolyak_points = []
    for ff in fff:
        smolyak_points.extend( [f for f in product( *ff ) ] )

    smolyak_points = np.c_[smolyak_points]
    
    return [smolyak_points, smolyak_indices]
    

class SmolyakGrid:
    
    def __init__(self,bounds,l):
        self.bounds = bounds

        d = bounds.shape[1]
        self.d = d
        self.l = l
        
        [self.smolyak_points, self.smolyak_indices] = smolyak_grids(d,l)
        
        self.isup = max(max(self.smolyak_indices))
        self.n_points = len(self.smolyak_points)
        self.real_grid = self.Ainv(self.smolyak_points.T)
        self.grid = self.real_grid
        
        #####

        Ts = chebychev( self.smolyak_points.T, self.n_points - 1 )
        ket = []
        for comb in self.smolyak_indices:
            p = reduce( mul, [Ts[comb[i],i,:] for i in range(self.d)] )
            ket.append(p)           
        ket = np.row_stack( ket )

        self.__ket__ = ket
        self.__Ts__ = Ts
    
    def __call__(self,x):
        return self.interpolate(x)[0]

    def __interpolate__(self,x):

        x = x.real ## ? justification ?

        theta = self.theta

        [n_v, n_t] = theta.shape
        assert( n_t == self.n_points )

        [n_d, n_p] = x.shape

        assert( n_d == self.d )
        s = self.A(x)
        Ts = chebychev( s, self.n_points - 1 )

        ket = []
        for comb in self.smolyak_indices:
            p = reduce( mul, [Ts[comb[i],i,:] for i in range(self.d)] )
            ket.append(p)

        ket = np.row_stack( ket )

        val = np.dot(theta,ket)

        return val

    def interpolate(self, x, with_derivative=True):
        eps = 1e-5
        val = self.__interpolate__(x)
        n_x = x.shape[0]
        dval = np.zeros( (val.shape[0], n_x, val.shape[1]))
        for i in range(n_x):
            xx = x.copy()
            xx[i,:] += eps
            delta = (self.__interpolate__(xx) - val)/eps
            dval[:,i,:] = delta
        return [val,dval]
#
#    def interpolate(self, x, with_derivative=True):
#        # points in x must be stacked horizontally
#
#        theta = self.theta
#
#        [n_v, n_t] = theta.shape
#        assert( n_t == self.n_points )
#        n = theta.shape[1] - 1
#
##        if x is None:
##            x = self.real_grid
##            #s = self.A(x)
##            s = self.smolyak_points.T
##            ket = self.__ket__
##            Tx = self.__Ts__
##        else:
#        [n_d, n_p] = x.shape
#        n_obs = n_p # by def
#        assert( n_d == self.d )
#        s = self.A(x)
#        Ts = chebychev( s, self.n_points - 1 )
#        Tx = Ts
#
#        ket = []
#        for comb in self.smolyak_indices:
#            p = reduce( mul, [Ts[comb[i],i,:] for i in range(self.d)] )
#            ket.append(p)
#        ket = np.row_stack( ket )
#        s = ket.shape
#        #vprint('s')
#
#        val = np.dot(theta,ket)
#
#        if with_derivative:
#            # derivative w.r.t. to theta
#            l = []
#            for i in range(n_v):
#                block = np.zeros( (n_v,n_t,n_obs) )
#                block[i,:,:] = ket
#                l.append(block)
#                dval = np.concatenate( l, axis = 1 )
#
#            # derivative w.r.t. arguments
#            Ux = chebychev( x, n-1 )
#            Ux = np.concatenate([np.zeros( (1,n_d,n_obs) ), Ux],axis=0)
#            for i in range(Ux.shape[0]):
#                Ux[i,:,:] = Ux[i,:,:] * i
#
#            der_x = np.zeros( ( n_t, n_d, n_obs ) )
#            #vprint('n_t')
#            #print Tx.shap
#            for i in range(n_d):
#                BB = Tx.copy()
#                BB[:,i,:] = Ux[:,i,:]
#                el = []
#                for comb in self.smolyak_indices:
#                    p = reduce( mul, [BB[comb[j],j,:] for j in range(self.d)] )
#                    el.append(p)
#                el = np.row_stack(el)
#                der_x[:,i,:] =  el
#            dder = np.tensordot( theta, der_x, (1,0) )
#            return [val,dder]
#
#        #dval = ket # I should include the computation of the derivative here
#        return val


    def fit_values(self,res0):
        
        ket = self.__ket__
        #######
        # derivatives w.r.t theta on the grid
        l = []
        n_v = res0.shape[0]
        n_t = res0.shape[1]
        for i in range(n_v):
            block = np.zeros( (n_v,n_t,n_t) )
            block[i,:,:] = ket
            l.append(block)
        self.__dval__ = np.concatenate( l, axis = 1 )
        ######

        #res0 = f(self.real_grid)
        theta0 = np.zeros(res0.shape)
        dval = self.__dval__
        #[val,dval,dder] = self.evalfun(theta0,self.real_grid,with_derivative=True)

        idv = dval.shape[1]
        jac = dval.swapaxes(1,2)
        jac = jac.reshape((idv,idv))

        import numpy.linalg
        theta = + np.linalg.solve(jac,res0.flatten())
        theta = theta.reshape(theta0.shape)

        self.theta =  theta
        

    def A(self,X):
        bounds = self.bounds
        bounds_delta = bounds[1,:] - bounds[0,:]
        bounds_m = bounds[0,:] + bounds_delta/2.0
        tmp = [(X[i,:]-bounds_m[i])/bounds_delta[i]*2 for i in range(bounds.shape[1])]
        return np.r_[ tmp ] # strange !
        
    def Ainv(self,Y):
        #Y = Y.T
        bounds = self.bounds
        bounds_delta = bounds[1,:] - bounds[0,:]
        bounds_m = bounds[0,:] + bounds_delta/2.0
        tmp = [ bounds_m[i] + Y[i,:] * bounds_delta[i] / 2 for i in range(bounds.shape[1])]
        return np.r_[ tmp ] # strange !
        #val =  np.dot( theta, Tx )
        #dval = Tx.T        
        
# test smolyak library
if __name__ == '__main__':
    
    
    # we define a reference funcion :
    def testfun(x):
        val = np.row_stack([
            x[0,:]*x[0,:] * (1-np.sqrt(x[1,:])),
            x[0,:]*(1-np.sqrt(x[1,:])) + x[1,:]/4
        ])
        return val
    
    bounds = np.array([[0,1],[0,1]]).T
    sg2 = SmolyakGrid(bounds, 2)
    sg3 = SmolyakGrid(bounds, 3)
    
    
    theta2_0 = np.zeros( (2, sg2.n_points) )
    vals = testfun(sg2.real_grid)
    print vals
    print sg2.fit_values(vals)
    
    print sg2.interpolate(sg2.real_grid)
    
    from dolo.numeric.serial_operations import numdiff2

    fobj = lambda x: sg2.interpolate(x,with_derivative=True)
    [val,dval] = fobj(sg2.real_grid)
    print sg2.real_grid.shape
    print sg2.theta.shape
    print val.shape
    print dval.shape
    print dval
    
    ddval = numdiff2(sg2.interpolate,sg2.real_grid)
    print ddval

    print dval.shape
    print ddval.shape

    exit()
    
    def fobj2(theta):
        grid = sg2.real_grid
        return testfun(grid) - sg2.interpolate(theta, grid)
    theta2_0 = np.zeros( (2, sg2.n_points) )
    res_2 = fobj2(theta2_0)
    
    def fobj3(theta):
        grid = sg3.real_grid
        return testfun(grid) - sg3.interpolate(theta, grid)
    theta3_0 = np.zeros( (2, sg3.n_points) )
    res_3 = fobj3(theta3_0)
    
    theta3_0[:,:5]=res_2
    #print sg2.evalfun(res_2, sg2.real_grid )[0]
    #print sg2.evalfun(res_2, sg3.real_grid )[0]
    
    #print sg3.evalfun(theta3_0, sg2.real_grid )[0]
    #print sg3.evalfun(theta3_0, sg3.real_grid )[0]    
    
    theta3_0 = np.ones((2,13))
    theta3_0[:,:5] = 0
    print sg3.evalfun(theta3_0, sg3.real_grid )
    
    values = testfun(sg3.real_grid)