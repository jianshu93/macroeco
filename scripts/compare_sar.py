#!/usr/bin/python

'''
Script to compare sars
'''

__author__ = "Mark Wilber"
__copyright__ = "Copyright 2012, Regents of the University of California"
__credits__ = ["John Harte"]
__license__ = None
__version__ = "0.1"
__maintainer__ = "Mark Wilber"
__email__ = "mqw@berkeley.edu"
__status__ = "Development"

import macroeco.utils.global_strings as gb

gui_name = ''' Analyze Species-Area Relationships'''

summary = '''Compares a dataset's observed species-area relationships against 
theoretical species-area relationships'''

columns_to_divide = '''This parameter specifies which spatial columns you would
like to divide for the SAR analysis.  For example, if your data had spatial
columns 'x' and 'y' you would enter: ('x', 'y') '''

list_of_divisions_on_columns = '''This parameter specifies how you would like
to divide the columns you named in the columns_to_divide parameter.  For
example, if you specified that you wanted to divide on columns 'x' and 'y' in
the parameter columns_to_divide and you wanted to divide your plot into fourths
and eighths you would input: [(2,2), (2,4)].  The first value splits the plot
into fourths and the second splits the plot into eighths.  The values within
each parentheses are divisions on 'x' and 'y', respectively.  Please note that
the number of species of the entire plot will be calculated even if you do not
enter the division (1,1).'''

predicted_SAR_curves = '''A list of SAR curves to which you can compare your
observed data.

You may use any number of the following SAR distributions: 'powerlaw',
'mete_sar', 'mete_sar_iter', 'logser_ut_binm', 'lognorm_binm', etc.

Example input: ['mete_sar', 'powerlaw', 'mete_sar_iter']  
'''

name = '''A name for the plot that will be generated.

Example input: My SAR Plot  
'''

explanation = '''ANALYSIS EXPALANTION\n
This script allows you to compare observed species-area relationships (SAR)
with any number of predicted SARs.  An SAR is a commonly used macroecological
metric which examines the number of species found in a given area. All SAR
curves show increasing species with increasing area, but shape of this
increasing curve differs depending on the theory used to derive it. It is
common practice to examine SAR plots on a log-log scale because the curve often
becomes close to a straight line. Using this script, you can generate the
observed SARs for any nested plots within your data.  For example, if you had a
fully censused plot with spatial coordinates x,y and you wanted to examine an
SAR looking at the anchor area (A), 1/2 * A, 1/4 * A, and 1/8 * A, you
would input the appropriate parameters and this analysis would divide the plot
into halves, fourths, and eighths and take the average number of species across
all of the smaller plots. Therefore, you can have a fractional average number
of species per areas. For additional information on SARs, please see the
provided references and the references therein.

OUTPUT

This script outputs log(species) vs. log(area fraction) plot as a .png file.
Area fraction means that the anchor area (largest area) for the plot is 1 and
all smaller subplots are fractions less than one. Each plot will have the
observed SAR and any SAR generated by a predicted SAR specified in the
predicted_SAR_curves parameter. In addition to this plot, this script will
output csv files with the same file name as the plot, but with the name of the
predicted SAR appended to the end.  These files contain the data for the given
SAR used to make the plot.  For example, if you choose two predicted SARs and
run the analysis, you will get three csv files: two with the predicted SAR data
and one with the observed data. With these files, you can re-plot the data in
anyway you chose.  Please note that the file names provide a detailed
description of each file and should provide you with a basic understanding of
what the file contains.

PARAMETER EXPLANATIONS

*** subset ***:

{0}

*** criteria ***:

{1}

For the compare_sar analysis (this analysis), you DO NOT need to enter your
divisions in the 'criteria' parameter.  Instead, you enter them in the
'columns_to_divide' and 'list_of_divisions_on_columns' parameters.  If the
columns you entered in the parameter 'columns_to_divide' are repeated in the
parameter criteria, the values that you assigned in criteria will be ignored.
For example, if you want to divide the columns 'x' and 'y' for your SAR
analysis you would input them into columns to divide as ('x', 'y'). If you were
to give columns 'x' and/or 'y' a value in the 'criteria' parameter, it would
then be ignored. Generating multiple SARs is not yet implemented. 

*** columns_to_divide **

{2}

*** list_of_divisions_on_columns ***

{3}

*** predicted_SAR_curves ***

{4}

*** name ***

{5}

REFERENCES

Harte, J. 2011. Maximum Entropy and Ecology: A Theory of Abundance,
Distribution, and Energetics. Oxford University Press.

Rosenzweig, M. L. 1995. Species Diversity in Space and Time. Cambridge
University Press.

'''.format(gb.subset, gb.criteria, columns_to_divide,
list_of_divisions_on_columns, predicted_SAR_curves, name)


required_params = {'criteria' : gb.short_criteria + gb.req,
                   'columns_to_divide' : columns_to_divide + gb. req,
                   'list_of_divisions_on_columns' :
                   list_of_divisions_on_columns + gb.req,
                   'predicted_SAR_curves' : predicted_SAR_curves + gb.req}

optional_params = {'subset' : (gb.short_subset + gb.optional, {}), 'name' : 
                    (name + gb.optional, 'Plot')}

if __name__ == '__main__':

    import logging
    from macroeco.utils.workflow import Workflow
    from macroeco.empirical import Patch
    import macroeco.compare as comp
    from macroeco.output import SAROutput
    from copy import deepcopy

    wf = Workflow(required_params=required_params,
                optional_params=optional_params, clog=True, svers=__version__)
    
    for data_path, output_ID, params in wf.single_datasets():

        try:
            params['list_of_divisions_on_columns'].index((1,1))
        except:
            logging.info("Adding base area to parameter " +
                                       "'list_of_divisions_on_columns': (1,1)")
            params['list_of_divisions_on_columns'].append((1,1))
        sad_criteria = deepcopy(params['criteria'])

        for nm in params['columns_to_divide']:
            sad_criteria[nm] = 'whole'
        patch = Patch(data_path, subset=params['subset'])
        sad = patch.sad(sad_criteria, clean=True)
        sar = patch.sar(params['columns_to_divide'], 
                    params['list_of_divisions_on_columns'], params['criteria'])
        cmpr = comp.CompareSAR([sar], params['predicted_SAR_curves'],
                                                    [sad[0][1]], patch=True)
        srout = SAROutput(output_ID)
        srout.plot_sars(cmpr.compare_curves(), names=[params['name']])
        logging.info('Completed analysis %s\n' % output_ID)
    logging.info("Completed 'compare_sar' script")




        








