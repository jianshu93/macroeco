#!/usr/bin/python

'''
Script to compare energy distributions
'''

__author__ = "Mark Wilber"
__copyright__ = "Copyright 2012, Regents of the University of California"
__credits__ = ["John Harte"]
__license__ = None
__version__ = "0.1"
__maintainer__ = "Mark Wilber"
__email__ = "mqw@berkeley.edu"
__status__ = "Development"

gui_name = '''Energetics Analysis'''

summary = '''Compares a dataset's observed energy distributions against 
             theoretical energy distributions'''

explantion = ''''''

if __name__ == '__main__':

    import logging
    from macroeco.utils.workflow import Workflow
    from macroeco.empirical import Patch
    import macroeco.compare as comp
    from macroeco.output import SEDOutput, IEDOutput

    wf = Workflow(clog=True, svers=__version__)
    
    for data_path, output_ID, params in wf.single_datasets():

        # Put data in patch object
        patch = Patch(data_path, subset=params['subset'])

        # Calculate empirical metrics
        sad = patch.sad(params['criteria'])
        cmengy = patch.ied(params['criteria'])
        spengy = patch.sed(params['criteria'])

        # Make comparison objects 
        cmprt = comp.CompareSED((spengy, cmengy, sad),
                                    params['dist_list_sed'], patch=True)
        cmprp = comp.CompareIED((cmengy, sad), params['dist_list_ied'],
                                        patch=True)

        # Make output objects and output plots
        sout = SEDOutput(output_ID)
        soup = IEDOutput(output_ID)
        sout.plot_reds(cmprt.compare_reds(), criteria=cmprt.sad_criteria)
        soup.plot_reds(cmprp.compare_reds(), criteria=cmprp.sad_criteria)

        logging.info('Completed analysis %s\n' % output_ID)
    logging.info("Completed 'compare_energy.py' script")




        







