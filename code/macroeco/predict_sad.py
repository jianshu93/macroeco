#!/usr/bin/python

'''
Calculate pmf and likelihood of spatial-abundance distributions.

All distributions have an argument summary, which if False returns the entire 
pmf for the inputted values of n, and if true returns the summed negative 
log-likelihood of the inputted values (useful for likelihood ratio tests or 
AIC).

Distributions
-------------
- `lgsr_pmf` -- Fisher's log series (Fisher et al. 1943)
- `neg_binom_pmf` -- Negative Binomial
- `plognorm_pmf` -- Poisson lognormal (Bulmer 1974)
- 'trun_plognorm_pmf -- Truncated poisson log-normal (Bulmer 1974)
- `mete_logser_pmf` -- METE log series (Harte 2011)
- `mete_logser_approx_pmf` -- METE log series using approximation (Harte 2011)

Misc Functions
--------------
- `make_rank_abund` -- convert any SAD pmf into a rank abundance curve

References
----------
Bulmer, M. G. 1974. On fitting the poisson lognormal distribution to species
abundance data. Biometrics, 30:101-110.

Fisher, R. A., Corbet, A. S., and C. B. Williams. 1943. The relation between
The number of species and the number of individuals in a random sample
of an animal populatin. Journal of Animal Ecology, 12:42-58.

Harte, J. 2011. Maximum Entropy and Ecology: A Theory of Abundance,
Distribution, and Energetics. Oxford University Press.

Hubbell, S. P. 2001. The unified theory of biodiversity and biogeography. 
Monographs in Population Biology, 32,1:375.
'''

from __future__ import division
import numpy as np
import scipy.stats as stats
import scipy.optimize 
import scipy.special
import math as m
import scipy.integrate as integrate
import sys
from math import factorial, floor
from numpy import array, exp, histogram, log, matlib, sort, sqrt, pi, std, mean
from scipy import integrate, stats, optimize, special

#NOTE: Assertion statements needed!


class RootError(Exception):
    '''Error if no root or multiple roots exist for the equation generated
    for specified values of S and N'''

    def __init__(self, value=None):
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        return '%s' % self.value

def lgsr_pmf(S, N, abundances=[], pmf_ret=False):
    '''
    Fisher's log series pmf (Fisher et al. 1943, Hubbel 2001)

    Parameters
    ----------
    S : int
        Total number of species in landscape
    N : int
        Total number of indviduals in landscape
    abundances : array like object
        Array-like object containing sad

    Returns
    -------
    : ndarray (1D)
        Returns array with pmf for values [1, N] if pmf=True. If pmf=False
        and len(abundances) > 1, returns ndarray with likelihoods for each
        abundance. 

    Notes
    -----
    Multiplying the pmf by S yields the predicted number of species
    with a given abundance.
    '''
    assert S < N, "S must be less than N"
    assert S > 1, "S must be greater than 1"
    assert N > 0, "N must be greater than 0"
    if pmf_ret == False:
        abundances = np.array(abundances)
        assert len(abundances) == S, "Length of abundances must equal S"
        assert np.sum(abundances) == N, "Sum of abundances must equal N"

    start = -2
    stop = 1 - 1e-10
    
    eq = lambda x,S,N: (((N/x) - N) * (-(m.log(1 - x)))) - S
    
    x = scipy.optimize.brentq(eq, start, stop, args=(S,N), disp=True)
    if pmf_ret == True:
        k = np.linspace(1, N, num=N)
    elif pmf_ret == False:
        k = abundances
    pmf = stats.logser.pmf(k,x)

    return pmf


def neg_binom_pmf(S, N, k, abundances=[], pmf_ret=False):
    '''
    Negative binomial distribution 
    
    Parameters
    ----------
    S : int
        Total number of species in landscape
    N : int
        Total number of individuals in landscape
    k : int
        Aggregation parameter
    summary: bool (optional)
        see Returns

    Returns
    -------
     : ndarray (1D)
        Returns array with pmf for values [1, N] if pmf=True. If pmf=False
        and len(abundances) > 1, returns ndarray with likelihoods for each
        abundance in object abundances. 
    '''
    assert S < N, "S must be less than N"
    assert S > 1, "S must be greater than 1"
    assert N > 0, "N must be greater than 0"
    if pmf_ret == False:
        abundances = np.array(abundances)
        assert len(abundances) == S, "Length of abundances must equal S"
        assert np.sum(abundances) == N, "Sum of abundances must equal N"

    mu = float(N) / S
    p = float(k) / (mu + k)
    if pmf_ret == True:
        n = np.arange(1, N + 1)
    elif pmf_ret == False:
        n = abundances
    pmf = stats.nbinom.pmf(n, k, p)

    return pmf


def fit_neg_binom_pmf(sad, guess_for_k=1):
    '''
    Function fits a negative binomial to the sad and returns the negative
    log-likelihood for the model

    Parameters
    ----------
    sad : ndarray
        Array like object containing a species abundance distribution
    
    guess_for_k : float
        A default parameter for the approximate k given the data

    Returns
    -------
    : tuple
        The negative log-likelihood of the model for the given sad and 
        the mle for k

    '''

    #NOTE: Need to check for convergence
    def nll_nb(k, sad):
        return -sum(np.log(neg_binom_pmf(len(sad), np.sum(sad), k, abundances=sad)))
    mlek = scipy.optimize.fmin(nll_nb, np.array([guess_for_k]), args=(sad,))[0]
    return mlek
        

def plognorm_pmf(mean, var, abundances, pmf_ret=False):
    '''
    Poisson log-normal pmf (Bulmer 1974)

    Parameters
    ----------
    mean : float
        the logmean of the poisson log normal
    var : float
        the logvar of the poisson log normal
        
    abundances : A list, np.array, or tuple of the abundance of each
                 species in the plot.  len(abundance) should equal 
                 the total number of species in the plot and sum(abundances)
                 should equal the total number of individuals in the plot

     Returns
    -------
     : ndarray (1D)
        Returns array with pmf for values [1, N] if pmf_ret=True. If pmf_ret=False
        and len(abundances) > 1, returns ndarray with likelihoods for each
        abundance. 

    Notes
    -----
    This fuction was adopted directly from the VGAM package in R by Mark
    Wilber. The VGAM R package was adopted directly from Bulmer (1974).

    '''
    assert type(abundances) == list or type(abundances) == tuple \
           or type(abundances) == np.ndarray, "Invalid parameter type"

    assert len(abundances) >= 1, "Abundance vector cannot be empty"
    
    abundances = np.array(abundances)
    if pmf_ret == True:
        n_array = np.arange(1, int(np.sum(abundances) + 1))
    if pmf_ret == False:
        n_array = abundances
        

    if var <= 0 or mean <= 0: #Parameters can be negative when optimizer is running
        pmf = np.repeat(1e-120, len(n_array))
    else:
        sd = var**0.5
        eq = lambda t, x: np.exp(t * x - np.exp(t) - 0.5*((t - mean) / sd)**2)
        pmf = np.empty(len(n_array), dtype=np.float)
        for i, n in enumerate(n_array):
            if n <= 170:
                integral = integrate.quad(eq, -np.inf, np.inf, args=(n))[0]
                norm = np.exp((-0.5 * m.log(2 * m.pi * var) - m.lgamma(n + 1)))
                pmf[i] = norm * integral
            else:
                z = (m.log(n) - mean) / sd
                pmf[i] = (1 + (z**2 + m.log(n) - mean - 1) / (2 * n * sd**2)) *\
                         np.exp(-0.5 * z**2) / (m.sqrt(2 * m.pi) * sd * n)   
        
    return pmf


def trun_plognorm_pmf(mean, var, abundances, pmf_ret=False):
    '''
    Truncated Poisson log-normal (Bulmer 1974)

    Parameters
    ----------
    mean : float
        the logmean of the poisson log normal
    var : float
        the logvar of the poisson log normal
        
    abundances : A list, np.array, or tuple of the abundance of each
                 species in the plot.  len(abundance) should equal 
                 the total number of species in the plot and sum(abundances)
                 should equal the total number of individuals in the plot

    Returns
    -------
     : ndarray (1D)
        Returns array with pmf for values [1, N] if pmf_ret=True. If pmf_ret=False
        and len(abundances) > 1, returns ndarray with likelihoods for each
        abundance. 


    Notes:  This function was adopted from both Bulmer (1974) and Ethan White's code
    from weecology.  Truncating the plognormal changes the mean of the distribution'''

    untr_pmf = plognorm_pmf(mean, var, abundances, pmf_ret=pmf_ret)
    pmf0 = plognorm_pmf(mean, var, [0], pmf_ret=False)
    tr_pmf = (untr_pmf / (1 - pmf0)) #Truncating based on Bulmer 1974 equation A1

    return tr_pmf

def plognorm_MLE(abundances, trun=True):
    '''
    Maximum likelihood Estimates for Poisson log normal

    Parameter
    ---------
    abundances : A list, np.array, or tuple of the abundance of each
                 species in the plot.  len(abundance) should equal 
                 the total number of species in the plot and sum(abundances)
                 should equal the total number of individuals in the plot
    trun : bool
        If true, calculates the MLE's for the truncated poisson lognormal.
        If false, calulates the MLE's for the untruncated poisson lognormal.

    Returns
    -------
    mu, var : float
        The ML estimates of mu and var

    Notes
    -----
    This function was adapted from Ethan White's pln_solver function in weecology. 

    '''
    assert type(abundances) == list or type(abundances) == tuple \
           or type(abundances) == np.ndarray, "Invalid parameter type"

    assert len(abundances) >= 1, "len(abundances) must be greater than or equal to 1"

    abundances = np.array(abundances)
    mu0 = np.mean(np.log(abundances))
    var0 = np.var(np.log(abundances), ddof=1)
    def pln_func(x):
        if trun == True:
            return -sum(np.log(trun_plognorm_pmf(x[0], x[1], abundances)))
        else:
            return -sum(np.log(plognorm_pmf(x[0], x[1], abundances)))
    mu, var = optimize.fmin(pln_func, x0 = [mu0, var0], disp=0)
    return mu, var





###Functions from Ethan White's weecology###

def pln_lik(mu,sigma,abund_vect,approx_cut = 10, full_output=0):
    #TODO remove all use of matrices unless they are necessary for some
    #     unforseen reason
    """Probability function of the Poisson lognormal distribution
    
    Method derived from Bulmer 1974 Biometrics 30:101-110    
    
    Bulmer equation 7 - approximation for large abundances
    Bulmer equation 2 - integral for small abundances    
    
    Adapted from Brian McGill's MATLAB function of the same name that was
    originally developed as part of the Palamedes software package by the
    National Center for Ecological Analysis and Synthesis working group on
    Tools and Fresh Approaches for Species Abundance Distributions
    (http://www.nceas.ucsb.edu/projects/11121)
    
    """
   
    L = matlib.repmat(None, len(abund_vect), 1)
    if sigma <= 0:
        L = matlib.repmat(1e-120, len(abund_vect), 1) #very unlikely to have negative params
    else:
        for i, ab in enumerate(abund_vect):
            if ab > approx_cut:
            #use approximation for large abundances    
            #Bulmer equation 7
            #tested vs. integral below - matches to about 6 significant digits for
            #intermediate abundances (10-50) - integral fails for higher
            #abundances, approx fails for lower abundances - 
            #assume it gets better for abundance > 50
                V = sigma ** 2
                L[i,] = (1 / sqrt(2 * pi * V) / ab *
                         exp(-(log(ab) - mu) ** 2 / (2 * V)) *
                         (1 + 1 / (2 * ab * V) * ((log(ab) - mu) ** 2 / V +
                                                  log(ab) - mu - 1)))
            else:
            # Bulmer equation 2 -tested against Grundy Biometrika 38:427-434
            # Table 1 & Table 2 and matched to the 4 decimals in the table except
            # for very small mu (10^-2)
            # having the /gamma(ab+1) inside the integrand is inefficient but
            # avoids pseudo-singularities        
            # split integral into two so the quad function finds the peak
            # peak apppears to be just below ab - for very small ab (ab<10)
            # works better to leave entire peak in one integral and integrate 
            # the tail in the second integral
                if ab < 10:
                    ub = 10
                else: 
                    ub = ab       
                term1 = ((2 * pi * sigma ** 2) ** -0.5)/ factorial(ab)
            #integrate low end where peak is so it finds peak
                term2a = integrate.quad(lambda x: ((x ** (ab - 1)) * 
                                                   (exp(-x)) * 
                                                   exp(-(log(x) - mu) ** 2 / 
                                                       (2 * sigma ** 2))), 0,
                                               ub, full_output=full_output, limit=100)
            #integrate higher end for accuracy and in case peak moves
                term2b = integrate.quad(lambda x: ((x ** (ab - 1)) * 
                                                   (exp(-x)) * exp(-(log(x) - mu) ** 
                                                                   2/ (2 * sigma ** 
                                                                       2))), ub,
                                               float('inf'), full_output=full_output, limit=100)
                Pr = term1 * term2a[0]
                Pr_add = term1 * term2b[0]                
                L[i,] = Pr + Pr_add            
            
                if L[i,] <= 0:
                #likelihood shouldn't really be zero and causes problem taking 
                #log of it
                    L[i,] = 1e-120
    return (L)

def pln_ll(mu, sigma, ab, full_output=0):
    """Log-likelihood of a truncated Poisson lognormal distribution
    
    Method derived from Bulmer 1974 Biometrics 30:101-110    
    
    Bulmer equation A1
    
    Adapted from Brian McGill's MATLAB function of the same name that was
    originally developed as part of the Palamedes software package by the
    National Center for Ecological Analysis and Synthesis working group on
    Tools and Fresh Approaches for Species Abundance Distributions
    (http://www.nceas.ucsb.edu/projects/11121)    
    
    """
    #purify abundance vector
    ab = array(ab)
    ab.transpose()
    ab = ab[ab>0]
    ab.sort()
    
    cts = histogram(ab, bins = range(1, max(ab) + 2))
    observed_abund_vals = cts[1][cts[0] != 0]
    counts = cts[0][cts[0] != 0]
    plik = log(array(pln_lik(mu, sigma, observed_abund_vals, full_output=full_output), dtype = float))
    term1 = array([], dtype = float)
    for i, count in enumerate(counts):
        term1 = np.append(term1, count * plik[i])
        
    #Renormalization for zero truncation
    term2 = len(ab) * log(1 - array(pln_lik(mu, sigma, [0], full_output=full_output), dtype = float))
    
    ll = sum(term1) - term2
    return ll[0]

def pln_solver(ab):
    """Given abundance data, solve for MLE of pln parameters mu and sigma
    
    Adapted from MATLAB code by Brian McGill that was originally developed as
    part of the Palamedes software package by the National Center for Ecological
    Analysis and Synthesis working group on Tools and Fresh Approaches for
    Species Abundance Distributions (http://www.nceas.ucsb.edu/projects/11121)
    
    """

    mu0 = mean(log(ab))
    sig0 = std(log(ab))
    def pln_func(x): 
        return -pln_ll(x[0], x[1], ab, full_output=1)
    mu, sigma = optimize.fmin(pln_func, x0 = [mu0, sig0], disp=0)
    return mu, sigma


###End functions from Ethan White's weecology###

def mete_lgsr_pmf(S, N, abundances=[], pmf_ret=False):
    '''
    mete_logsr_pmf(S, N, summary=False)

    Truncated log series pmf (Harte 2011)

    Parameters:
    -----------
    S : int
        Total number of species in landscape
    N : int
        Total number of individuals in landscape
    abundances : array-like object
        Array-like object containing sad
        
    Returns
    -------
     : ndarray (1D)
        Returns array with pmf for values [1, N] if pmf_ret=True. If pmf_ret=False
        and len(abundances) > 1, returns ndarray with likelihoods for each
        abundance. 

    Notes
    -----
    This function uses the truncated log series as described in Harte 2011
    eq (7.32).  The equation used in this function to solve for the Lagrange 
    multiplier is equation (7.27) as described in Harte 2011. 
    
    Also note that realistic values of x where x = e**-(beta) (see Harte 2011) are
    in the range (1/e, 1) (exclusive). Therefore, the start and stop parameters 
    for the brentq procedure are close to these values. However, x can
    occasionally be greater than one so the maximum stop value of the brentq optimizer
    is 2.
    '''
    assert S < N, "S must be less than N"
    assert S > 1, "S must be greater than 1"
    assert N > 0, "N must be greater than 0"
    if pmf_ret == False:
        abundances = np.array(abundances)
        assert len(abundances) == S, "If pmf_ret = False, length of abundances must equal S"
        assert np.sum(abundances) == N, "If pmf_ret = False, sum of abundances must equal N"
    start = 0.3
    stop = 2
    
       
    n = np.linspace(1, N, num=N)
    eq = lambda x: sum(x ** n / float(N) * S) -  sum((x ** n) / n)
    x = scipy.optimize.brentq(eq, start, min((sys.float_info[0] / S)**(1/float(N)),\
                              stop), disp=True)
    #Taken from Ethan White's trun_logser_pmf
    if pmf_ret == True:
        nvals = np.linspace(1, N, num=N)
    elif pmf_ret == False:
        nvals = abundances
    norm = sum(x ** n / n)        
    pmf = (x ** nvals / nvals) / norm

    return pmf


def mete_lgsr_approx_pmf(S, N, abundances=[], pmf_ret=False, root=2):
    '''
    mete_lgsr_approx_pmf(S, N, summary=False, root=2)

    Truncated log series using approximation (7.30) and (7.32) in Harte 2011

    Parameters
    ----------
    S : int
        Total number of species in landscape
    N : int
        Total number of individuals in landscape
    abundances : array-like object
        Array-like object containing sad
    root: int (optional)
        1 or 2.  Specifies which root to use for pmf calculations        
    Returns
    -------
     : ndarray (1D)
        Returns array with pmf for values [1, N] if pmf_ret=True. If pmf_ret=False
        and len(abundances) > 1, returns ndarray with likelihoods for each
        abundance. 
    
    Notes:
    ------
    This function uses the truncated log series as described in Harte 2011
    eq (7.32).  The equation used in this function to solve for the Lagrange 
    multiplier is equation (7.30) as described in Harte 2011.     
       
    Also note that realistic values of x where x = e^-(beta) (see Harte 2011) are
    in the range (1/e, 1) (exclusive). Therefore, the start and stop parameters
    for the brentq optimizer have been chosen near these values.
    '''

    assert S < N, "S must be less than N"
    assert S > 1, "S must be greater than 1"
    assert N > 0, "N must be greater than 0"
    if pmf_ret == False:
        abundances = np.array(abundances)
        assert len(abundances) == S, "If pmf_ret = False, length of abundances must equal S"
        assert np.sum(abundances) == N, "If pmf_ret = False, sum of abundances must equal N"
    start = 0.3
    stop = 1 - 1e-10
    
    eq = lambda x: ((-m.log(x))*(m.log(-1/(m.log(x))))) - (float(S)/N)
    try:
        x = scipy.optimize.brentq(eq, start, stop, disp=True)
    except ValueError:
        values = np.linspace(start, stop, num=1000)
        solns = []
        for i in values:
            solns.append(eq(i))#Find maximum
        ymax = np.max(np.array(solns))
        xmax = values[solns.index(ymax)]
        if ymax > 0:
            print "Warning: More than one solution."
            if root == 1:
                x = scipy.optimize.brentq(eq, start, xmax, disp=True)
            if root == 2:
                x = scipy.optimize.brentq(eq, xmax, stop, disp=True)
                       
        if ymax < 0:
            raise RootError('No solution to constraint equation with given ' + \
                            'values of S and N') 
    if pmf_ret == True:
        k = np.linspace(1, N, num = N)
    if pmf_ret == False:
        k = abundances
    g = -1/m.log(x)
    pmf = (1/m.log(g)) * ((x**k)/k) 
    
    return pmf


def mete_lgsr_cdf(S, N):
    '''
    mete_lgr_cdf(S, N)
    
    CDF for METE logseries distribution

    Parameters
    ----------
    S : int
        Total number of species in landscape
    N : int
        Total number of individuals in landscape

    Returns:
    : 1D structured array
        Field names in the structured array are 'n' (number of individuals) and 'cdf'


    '''
    pmf = mete_lgsr_pmf(S, N, pmf_ret=True)
    cdf = np.cumsum(pmf)
    cdf_struct = np.empty(len(cdf), dtype=[('cdf', np.float), ('n', np.int)])
    cdf_struct['cdf'] = cdf
    cdf_struct['n'] = np.arange(1, N + 1)
    return cdf_struct


def make_rank_abund(sad_pmf, S):
    '''
    Convert any SAD pmf into a rank abundance curve for S species using 
    cumulative distribution function.
 
    Parameters
    ----------
    sad_pmf : ndarray
        Probability of observing a species from 1 to length sad_pmf individs
    S : int
        Total number of species in landscape

    Returns
    -------
    : ndarray (1D)
        If summary is False, returns array with pmf. If summary is True,
        returns the summed log likelihood of all values in n.

    Notes
    -----
    Function actually implements (philosophically) a step quantile function. 
    Species indexes currently run from 0 to 1 - 1/S - this might be better 
    running from 1/2S to 1 - 1/2S.
    '''

    S_points = np.arange(1/(2*S), 1 + 1/(2*S), 1/S)
    S_abunds = np.zeros(S_points.shape[0])
    sad_pmf_w_zero = np.array([0] + list(sad_pmf)) # Add 0 to start of pmf
    cum_sad_pmf_w_zero = np.cumsum(sad_pmf_w_zero)
    
    for cutoff in cum_sad_pmf_w_zero:
        greater_thans = (S_points >= cutoff)
        S_abunds[greater_thans] += 1

        if not greater_thans.any():  # If no greater thans, ie done with all S
            break
    
    return S_abunds

def nll(sad, distribution):
    '''
    Calculates the negative log-likelihood for different distributions

    Parameters
    ----------
    sad : ndarray
        An array-like object with species abundances

    distribution : string
        Specifies the distribution for which to get the negative log-likelihood
        'mete' - mete distribution
        'mete_approx' - mete distribution with approximation
        'neg_binom' - negative binomial distribution
        'plognorm' - poisson log-normal distribution
        'trun_plognorm' - truncated poisson log-normal distribution
        'lgsr' - Fisher's log series 

    Returns
    -------
    : float
        The negative log-likelihood

    '''

    assert distribution is 'mete' or 'mete_approx' or 'neg_binom'\
            or 'lgsr' or 'trun_plognorm' or 'plognorm',\
           "Do not recognize %s distribution" % (distribution)

    if distribution == 'mete':
        pmf = mete_lgsr_pmf(len(sad), sum(sad), abundances=sad)
    if distribution == 'mete_approx':
        pmf = mete_lgsr_approx_pmf(len(sad), sum(sad), abundances=sad)
    if distribution == 'neg_binom':
        mlek = fit_neg_binom_pmf(sad)
        pmf = neg_binom_pmf(len(sad), sum(sad), mlek, abundances=sad)
    if distribution == 'trun_plognorm':
        mu, var = plognorm_MLE(sad, trun=True)
        pmf = trun_plognorm_pmf(mu, var, sad)
    if distribution == 'plognorm':
        mu, var = plognorm_MLE(sad, trun=False)
        pmf = plognorm_pmf(mu, var, sad)
    if distribution == 'lgsr':
        pmf = lgsr_pmf(len(sad), sum(sad), abundances=sad)

    return -sum(np.log(pmf))
    

        






