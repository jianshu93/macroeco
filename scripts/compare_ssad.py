#!/usr/bin/python

'''
Script to compare ssads
'''

__author__ = "Mark Wilber"
__copyright__ = "Copyright 2012, Regents of the University of California"
__credits__ = ["John Harte"]
__license__ = None
__version__ = "0.1"
__maintainer__ = "Mark Wilber"
__email__ = "mqw@berkeley.edu"
__status__ = "Development"

gui_name = '''Analysis of Species-level Spatial Abundance Distributions'''

summary = '''Compares a dataset's observed species-level spatial abundance
distribution against predicted species-level spatial abundance distributions'''

class global_str:
    subset = '''You should examine the columns in your data set and decide if
    you would like to subset your data in some particular way before the
    analysis begins. It is important to note that only the subsetted data will
    be analyzed.  For example,  if you have a column named 'year' in your data
    set with values 1998, 1999, and 2000 and you only want to look at the year
    2000 for a particular analysis, you should select the == operator from the
    drop down list and type 2000 in the value field.  Similarly, you could use
    <, >, <=, >=, or !='''

    criteria = '''You should examine the columns in your dataset and decide if
    you would like to divide the data in a particular way for this analysis.
    For example, if the you have a spatial dataset with x,y coordinates and you
    are interested in examining macroecological metrics for two separate halves
    of your plot along the x coordinate, you could cut the x coordinate in two
    halves by giving the 'x' column a value of 2.  If the column that you would
    like to divide contains discrete values (e.g. year), you could enter the
    keyword 'split' and each unique value will be analyzed separately.
    Conversely, the value 'whole' could be given to specify the entire column.
    The value 'whole' is equivalent to 1 or leaving the value blank. If you
    would like to divide a given column, please select the word 'division' from
    the GUI dropdown menu and input a value as discussed above.\n\n

    There are four special words that can be used on a given column: 'species',
    'energy', 'count', and 'mass'.  When assigned to a column in your data set,
    the special word 'species' indicates the column that contains your species
    IDs, the special word 'energy' indicates the column that contains some type
    of energy measure, the special word 'mass' indicates a column that contains
    some type of mass measure, and the special word 'count' indicates the
    column that contains your species counts.  In the GUI, these special words
    can be chosen from the dropdown menu next to each column header. The
    special word 'species' MUST be assigned for every analysis.  If the special
    word 'count' is not assigned, the species counts are all assumed to be
    one.\n\n'''

    rarity_measure = '''This parameter allows you to specify the counts that
    you will consider rare.  If, for example, you want to know how many species
    in your plot have an abundance of 2 or less you would set this parameter to
    2. If you enter more then one value, each value will be examined.

    Example input: [2] or [2, 5]. The brackets MUST be included.'''

    SAD_distributions = ''' 'logser','logser_ut', 'logser_ut_appx',
    'plognorm_lt', 'nbd_lt', 'geo_ser', 'broken_stick', 'lognorm' '''

    SSAD_distributions = ''' 'nbd', 'binm', 'tgeo', 'fgeo', 'fnbd', 'pois' '''


subset = '''Specifications for how you want to subset your data before the
analysis.  Only the subsetted data will be included in the analysis.  See
explanation link for more detail.'''

criteria = '''Specifications for how you want to divide your data during the
analysis.  See explanation link for more detail.'''

# NOTE: Need to find a different way to specify which distributions they can
# use
predicted_SSAD_distributions = '''A list of SSAD
distributions to which you can compare your observed data. 

You may use any number of the following SSAD distributions: {!s} 

Example input: ['binm', 'pois'] or ['fnbd']. The brackets MUST be
included.'''.format(global_str.SSAD_distributions)

rarity_measure = global_str.rarity_measure + ''' In this analysis, the rarity
counts refer to the number of individuals of a single species per cell.'''

explanation = '''
ANALYSIS EXPLANATION\n This script allows you to compare an observed
species-level spatial abundance distribution (SSAD) against any number of
predicted SSADs. An SSAD can be thought of as the probability that a given
species with n_o individuals will have n individuals in a cell of size A <=
A_o, where A_o is the anchor scale for a given plot.  Some common predictions
of SSADs include binomial distributions and negative binomial distributions.
These distributions are are among some of the distributions against which you
can compare your observed SSADs. Because SSADs are species specific, a given
plot with 30 species will have 30 associated SSADs regardless of how you divide
it.  For example, if you consider the whole plot, each species has an SSAD with
one sample that is equal to its abundance.  If you were to divide the plot into
sixteenths, each species would have an SSAD with 16 samples which summed to its
total abundance in the plot. For more information on SSADs please see the
provided references and the references therein.

This script outputs cumulative density function (cdf) plots and rank abundance
distribution (rad) plots in which the observed SSAD distribution for each
species is compared to the distributions given in the required parameter
predicted_SSAD_distributions.  For each plot, a corresponding csv file with the
same name as the plot except with a .csv extension is output containing the
data used to make the plot.  In addition, a summary .txt file is output
containing summary values for the plot and fitting statistics for the different
predicted distributions you choose. If you perform an SSAD analysis on a plot
with 30 species, you will get 30 cdf plots, 30 rad plots, 30 + 30 csv files,
and 30 summary txt files, one for each species.   


PARAMETER EXPLANATIONS

*** subset ***:

{0}

*** criteria ***:

{1}

*** rarity_measure ***:

{2}

*** predicted_SSAD_distributions ***:

{3}

REFERENCES

Magurran, A. E. 1988. Ecological Diversity and Its Measuremnt. Princeton
University Press.

May, R. M. 1975. Patterns of species abundance and diversity. In Ecology and
Evolution of Communities (eds M. L. Cody and J. M. Diamond), Harvard University
Press.
'''.format(global_str.subset, global_str.criteria, rarity_measure,
predicted_SSAD_distributions)

required_params = {'criteria' : criteria, 'rarity_measure' : rarity_measure,
		           'predicted_SSAD_distributions': predicted_SSAD_distributions}

optional_params = {'subset' : (subset + ''' Optional. Default: ''', {})}

if __name__ == '__main__':

    import logging
    from macroeco.utils.workflow import Workflow
    from macroeco.empirical import Patch
    import macroeco.compare as comp
    from macroeco.output import DistOutput

    wf = Workflow(required_params=required_params, clog=True, 
                                                            svers=__version__)
    
    for data_path, output_ID, params in wf.single_datasets():
        for optpar in optional_params: #TODO: Move to workflow
            if not optpar in params:
                logging.info("Default value for {!s}: {!s}".format(optpar,
                              str(optional_params[optpar][1])))
                params[optpar] = optional_params[optpar][1]

        patch = Patch(data_path, subset=params['subset'])
        ssad = patch.ssad(params['criteria'])

        cmpr = comp.CompareDistribution(ssad,
                           params['predicted_SSAD_distributions'],patch='ssad')
        rads = cmpr.compare_rads()

        sout = DistOutput(output_ID, 'ssad')
        sout.write_summary_table(cmpr.summary(rads,
                   mins_list=params['rarity_measure']), criteria=cmpr.spp_list)
        sout.plot_rads(rads, criteria=cmpr.spp_list)
        sout.plot_cdfs(cmpr.compare_cdfs(), cmpr.data_list,
                        criteria=cmpr.spp_list)
        logging.info('Completed analysis %s\n' % output_ID)
    logging.info("Completed 'compare_ssad.py' script")




        








