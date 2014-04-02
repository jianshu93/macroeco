import numpy as np
import pandas as pd

# TODO: docstring inheritance


def data_read_write(data_path_in, data_path_out, format_type, **kwargs):
    """
    General function to read, format, and write data.

    Parameters
    ----------
    data_path_in : str
        Path to the file that will be read
    data_path_out : str
        Path of the file that will be output
    format_type : str
        Either 'dense', 'grid', 'columnar', or 'transect'
    kwargs
        Specific keyword args for given data types. See Notes


    Notes
    -----

    'Dense Parameters'

    non_label_cols : str
        Comma separated list of non label columns. ex. "lat, long, tree"
    sep : str
        The delimiter for the dense data. Default, ","
    na_values : int, float, str
        Value to be labeled as NA. Default, ""

    See misc.format_dense() for additional keyword parameters
    """

    if format_type == "dense":

        # Set dense defaults
        kwargs = _set_dense_defaults_and_eval(kwargs)

        # Try to parse non label columns appropriately
        try:
            nlc = [nm.strip() for nm in kwargs['non_label_cols'].split(",")]
            kwargs.pop('non_label_cols', None)
        except KeyError:
            raise KeyError("'non_label_cols' is a required keyword dense data")

        # Read data with dense specific keywords
        arch_data = pd.read_csv(data_path_in, sep=kwargs['delimiter'],
                                na_values=kwargs['na_values'])

        form_data = format_dense(arch_data, nlc, **kwargs)

    elif format_type == "grid":
        pass
    elif format_type == "columnar":
        pass
    elif format_type == "transect":
        pass
    else:
        raise NameError("%s is not a supported data format" % format_type)

    form_data.to_csv(data_path_out, index=False)

def format_columnar():
    """
    """
    pass


def format_dense(base_data, non_label_cols, **kwargs):
    """
    Formats dense data type to columnar data type.

    Takes in a dense data type and converts into a stacked data type.

    Parameters
    ----------
    data_path : str
        A path to the dense data
    non_label_cols : list
        A list of columns in the data that are not label columns
    evaluate : bool
        If True, eval values in kwargs
    delimiter : str
        The delimiter for the dense data. Default, ","
    na_values : int, float, str
        Value to be labeled as NA. Default, ""
    item_col : str
        Name of the item column in the formatted data. Default, "label"
    count_col : str
        Name of the count column in the formatted data. Default, "count"
    nan_to_zero : bool
        Set all nans to zero. Default, False
    drop_na : bool
        Drop all columns with nan in the dataset. Default, False

    Notes
    -----
    Examples of Dense Data conversion...TODO


    """
    kwargs = set_defaults_and_eval(kwargs, evaluate)

    base_data = pd.read_csv(data_path, sep=kwargs['delimiter'],
                    na_values=kwargs['na_values'])

    # Stack data in columnar form.
    indexed_data = base_data.set_index(keys=non_label_cols)
    columnar_data = indexed_data.stack(dropna=False)
    columnar_data = columnar_data.reset_index()

    # Rename columns
    num = len(non_label_cols)
    columnar_data.rename(columns={0: kwargs['count_col'], 'level_%i' % num:
        kwargs['label_col']}, inplace=True)

    # Set nans to zero?
    if kwargs['nan_to_zero']:
        ind = np.isnan(columnar_data[kwargs['count_col']])
        columnar_data[kwargs['count_col']][ind] = 0

    # Drop nans?
    if kwargs['drop_na']:
        columnar_data = columnar_data.dropna(how="any")

    return columnar_data


def set_defaults_and_eval(kwargs, evaluate):
    """
    Sets default values in kwargs if kwargs are not already given
    """

    kwargs['delimiter'] = kwargs.get('delimiter', ',')
    kwargs['na_values'] = kwargs.get('na_values', '')
    kwargs['nan_to_zero'] = kwargs.get('nan_to_zero', False)
    kwargs['drop_na'] = kwargs.get('drop_na', False)
    kwargs['label_col'] = kwargs.get('label_col', 'label')
    kwargs['count_col'] = kwargs.get('count_col', 'count')

    for key, val in kwargs.iteritems():
        try:
            kwargs[key] = eval(val)
        except:
            kwargs[key] = val

    return kwargs

def format_transect():
    """
    """
    pass

def format_grid():
    """
    """
    pass
