""" The following file contains functions, which are used from the jupyter notebooks. """

# imports
import pandas as pd
import os
import numpy as np
from itertools import zip_longest
from math import log10, floor

# functions
def read_in_data_files(project_folder: str) -> pd.DataFrame:
    """Reads in all raw data files and merges them in a common pandas data frame.
    Ensures that all sample names from core method files end with Core,
    and all sample names from extended method files end with Extended.

    :project_folder: path to project folder
    :project_folder: str
    :raises ImportError: Data files must be of either CSV or TXT type
    :return: Data frame containing merged raw data of all files.
    :rtype: pd.DataFrame
    """

    # Check if project folder exists and throw an error if it does not.
    if not os.path.isdir(project_folder):
        raise NameError("""
            Your project folder does not exist. Carefully read the instructions to understand what you have to do.
            """)

    # Get all .csv and .txt files contained in the project folder
    raw_data_files_list = [
        elem for elem in os.listdir(project_folder) if \
            any(file_extension in elem for file_extension in ['.txt', '.csv'])
            ]

    # Check if project folder contains raw input data files and throw error if it does not.
    if len(raw_data_files_list) == 0:
        raise ImportError("""
            Your project folder does not contain data files.
            Place the exported results from Sciex Analyst in the project folder.
            """)

    # iterate through raw filenames and ensure that file naming conventions hold true
    for raw_data_file_name in raw_data_files_list:
        base_name = raw_data_file_name.split(".")[0]
        if not (base_name.endswith('_extended') or base_name.endswith('_core')):
            raise NameError(
                f"The file {raw_data_file_name} does not comply with file naming conventions." + \
                "Read the instructions for details regarding the filenaming conventions."
                )

    # Define columns of input which are needed for further processes:
    columns_considered = [
        'Sample Index', 'Sample Name', 'Sample ID', 'Sample Type',
        'Component Name',  'Component Group Name', 'IS Name',
        'Acquisition Date & Time', 'Used', 'IDA Average Response Factor',
        'Calculated Concentration', 'Actual Concentration',
        'Area', 'Retention Time', 'IS Retention Time',
    ]

    # Load input data files and put them all in one dataframe
    data = pd.DataFrame()  # initialize empty data frames
    sample_index = 0  # initialize Component Index
    for file in raw_data_files_list:
        # read in file
        if file[-4:] == '.csv':
            this_data = pd.read_csv(
                os.path.join(project_folder, file), delimiter=',', encoding='utf-8', low_memory=False, header=0,
                )
        elif file[-4:] == '.txt':
            this_data = pd.read_csv(
                os.path.join(project_folder, file), delimiter='\t', encoding='utf-8', low_memory=False, header=0,
                )
        else:
            raise ImportError('Raw input file paths must either be .csv or .txt files.')

        # make sure each sample name ends with Ext for extended method and with Core for core method
        if file[-12:-4] == 'extended':
            mask_names = this_data['Sample Name'].str.endswith('Ext')
            this_data.loc[~mask_names, 'Sample Name'] = [sample_name + ' Ext' for sample_name in this_data['Sample Name'][~mask_names].to_list()]

        elif file[-8:-4] == 'core':
            mask_names = this_data['Sample Name'].str.endswith('Core')
            this_data.loc[~mask_names, 'Sample Name'] = [sample_name + ' Core' for sample_name in this_data['Sample Name'][~mask_names].to_list()]
        
        # upcount sample indices and make sure they are unique
        highest_sample_index = this_data['Sample Index'].max()
        this_data['Sample Index'] = this_data['Sample Index'] + sample_index
        sample_index += highest_sample_index

        # append actual dataframe in list (this_data) to huge dataframe (data)
        if data.empty:
            data = this_data[columns_considered]  # initialize data in first step (when data is empty)
        else:
            data = pd.concat([data, this_data[columns_considered]], ignore_index=True)  # append to data

    # Only work with data, which is 'Used' -> Relevant for Calibration, where some of the calibration points are excluded for some compounds
    data = data.loc[data['Used'], :]
    data.drop('Used', axis=1, inplace=True)
    
    return data

# function to extract and map indices
def get_sample_id_and_name(data: pd.DataFrame) -> pd.DataFrame:
    """Creates dataframe containing list of samples with all related information from SCIEX raw data:
    Sample ID, Sample Type, Sample Name of Core Method, Sample Index of Core Method, Sample Name of Extended Method, Sample Index of Extended Method

    :param data: Data frame containing merged raw data of all files.
    :type data: pd.DataFrame
    :return: Data frame containing all samples occuring in raw data, where core and extended method are combined if possible. One combined sample corresponds to one row.
    :rtype: pd.DataFrame
    """    
    # get all sample IDs
    sample_ids = data['Sample ID'].unique()

    # initialize pandas dataframe with sample list
    sample_list = pd.DataFrame(
        {'Sample Number': [], 'Sample ID': [], 'Sample Type': [], 'Sample Name Core': [], 'Sample Index Core': [], 'Sample Name Extended': [], 'Sample Index Extended':[]}
        )
    # initialize sample number
    sample_number = 0

    # loop over sample ids
    for sample_id in sample_ids:
        # extract data for sample id and get all sample names for related ID
        sample_id_data = data.loc[data['Sample ID'] == sample_id, :]
        sample_names = sample_id_data['Sample Name'].unique()

        # get core sample names for related sample ID
        core_sample_names = [sample_name for sample_name in sample_names if 'Core' in sample_name]
        # Throw error if there is more than one sample ending with 'Core' for current sample_id in loop
        if len(core_sample_names) > 1:
            ImportError(f"You cannot have more than one sample names ending with Ext for the Sample ID {sample_id}. Check your raw data.")
        # Set core sample name to np.nan if it does not exist for current sample_id in loop
        elif len(core_sample_names) == 0:
            core_sample_name = np.nan
            core_sample_indices = []  # initialize core sample indices
        # Set core sample name variable to the available sample name for the extended method if it does exist for sample id in loop.
        else:
            core_sample_name = core_sample_names[0]
            # extract data for core method related to sample ID and get all sample indices running under the same sample name
            core_sample_id_data = sample_id_data.loc[data['Sample Name'] == core_sample_name, :]
            core_sample_indices = core_sample_id_data['Sample Index'].unique()

        # extract data for extended samples and get core sample names and indices for related sample ID
        extended_sample_names = [sample_name for sample_name in sample_names if 'Ext' in sample_name]
        # Throw error if there is more than one sample ending with 'Ext' for current sample_id in loop
        if len(extended_sample_names) > 1:
            ImportError(f"You cannot have more than one sample names ending with Ext for the Sample ID {sample_id}. Check your raw data.")
        # Set extended sample name to np.nan if it does not exist for current sample_id in loop
        elif len(extended_sample_names) == 0:
            extended_sample_name = np.nan
            extended_sample_indices = []  # initialize extended sample indices
        # Set extended sample name variable to the available sample name for the extended method if it does exist for sample id in loop.
        else:
            extended_sample_name = extended_sample_names[0]
            # extract data for extended method related to sample ID and get all sample indices running under the same sample name
            extended_sample_id_data = sample_id_data.loc[data['Sample Name'] == extended_sample_name, :]
            extended_sample_indices = extended_sample_id_data['Sample Index'].unique()

        # loop over all indices from core and extended and append sample number with all information to sample list
        for (core_sample_index, extended_sample_index) in zip_longest(core_sample_indices, extended_sample_indices, fillvalue=np.nan):
            
            # initialize sample types list
            sample_types = []
            
            # check if core sample is available, set name to nan if not
            if np.isnan(core_sample_index):
                core_sample_name = np.nan
            else:
                # extract sample type for core method and append to sample type list
                sample_types.append(core_sample_id_data.loc[data['Sample Index'] == core_sample_index, 'Sample Type'].unique()[0])

            if np.isnan(extended_sample_index):
                extended_sample_name = np.nan
            else:
                # extract sample type for extended method and append to sample type list
                sample_types.append(extended_sample_id_data.loc[data['Sample Index'] == extended_sample_index, 'Sample Type'].unique()[0])

            # make sure the sample type is the same for core method and extended method
            if len(list(set(sample_types))) > 1:
                raise ImportError(
                    f"The sample {core_sample_name} with index {core_sample_index} has a different " + \
                    f"sample type as the sample {extended_sample_name} with index {extended_sample_index}."
                )
            else:
                sample_type = list(set(sample_types))[0]  # save sample type variable

            # append line to data frame
            sample_list.loc[sample_number] = [sample_number, sample_id, sample_type, core_sample_name, core_sample_index, extended_sample_name, extended_sample_index]
            sample_number += 1  # upcount sample number

    # Use sample number as index and delete column
    sample_list.index = sample_list['Sample Number']
    sample_list.drop('Sample Number', axis=1, inplace=True)

    return sample_list

def clean_up_data(data: pd.DataFrame, sample_list: pd.DataFrame, channel_selection: str) -> pd.DataFrame:
    """Performs major cleanup steps for raw data:
     (i) replace strings in concentration with np.nan or 0.
     (ii) correct patterns of TOF MS channel names
     (iii) reset sample index from raw data with sample number (combining core and extended method)
     (iv) replace duplicate compounds (from comination of core method and extended method) with either
     compounds from core method only, compounds from extended method only, or average of compounds from both methods.

    :param data: Data frame containing merged raw data of all files.
    :type data: pd.DataFrame
    :param sample_list: Data frame containing all samples occuring in raw data. One row combines samples from core method and extended method.
    :type sample_list: pd.DataFrame
    :param channel_selection: For some cases, when using both core and extended method, some compounds in the TOF channels are avaialbe twice within the same sample.
        Set channel_selection to 'core' if you want to use the channel from the core method for further caluclations.
        Set channel_selection to 'extended' if you want to use the channel from the extended method for further calculations.
        Set channel_selection to 'average' if you want to use the average of both channels for further calculations.
    :type channel_selection: str
    :return: Cleaned up data.
    :rtype: pd.DataFrame
    """    
    
    # Clean up 'Calculated Concentration' column
    # set all strange strings to NaN
    # set '<1 points' and '< 0' to 0
    data['Calculated Concentration'] = data['Calculated Concentration'].replace(
        {'<1 points': 0, '< 0': 0, 'no root': np.nan, 'NaN': np.nan, 'degenerate': np.nan,}
        ).astype('float')
    
    # Correct channel names in original data (all of the TOF channels are labelled by _TOF MS, only 2 of them are labeled by only _TOF)
    mask_names = data['Component Name'].str.endswith('_TOF')
    data.loc[data['Component Name'].str.endswith('_TOF'), 'Component Name'] = [compound + ' MS' for compound in data['Component Name'][mask_names].to_list()]

    # some have an underscore between TOF and MS, this is removed
    mask_names = data['Component Name'].str.endswith('_TOF_MS')
    data.loc[data['Component Name'].str.endswith('_TOF_MS'), 'Component Name'] = [compound[:-3] + ' MS' for compound in data['Component Name'][mask_names].to_list()]

    # reset sample index from raw data with corresponding sample number from sample list
    # iterate over data rows
    for (row_index, row_data) in data.iterrows():
        # get sample id, sample index and sample name from current row
        sample_id = row_data['Sample ID']
        sample_index = row_data['Sample Index']
        sample_name = row_data['Sample Name']
        # if the sample is from the core method get the sample number from the core sample index
        if "Core" in sample_name:
            sample_number = sample_list.loc[(
                (sample_list['Sample ID']==sample_id) & 
                (sample_list['Sample Name Core']==sample_name) & 
                (sample_list['Sample Index Core']==sample_index)
                    ),:].index
        # if the sample is from the extended method get the sample number from the extended sample index
        elif "Ext" in sample_name:
            sample_number = sample_list.loc[(
                (sample_list['Sample ID']==sample_id) & 
                (sample_list['Sample Name Extended']==sample_name) & 
                (sample_list['Sample Index Extended']==sample_index)
                ),:].index
        # reset sample index with sample number
        data.loc[row_index, 'Sample Index'] = sample_number

    # Due to the merging of data from core method and extended method some pfas compounds may occur twice in the same sample.
    # The following code block removes duplicates by either deleting all duplicates from the core method, deleting all duplicates from the extended method,
    # or using average from core and extended method

    # initialize lists before going into the loop
    all_compounds = data['Component Name'].unique()  # all compound names
    # all columns of data frame, which are numeric and thus can be averaged
    numeric_data_columns = [
        'IDA Average Response Factor', 'Calculated Concentration', 'Actual Concentration',
        'Area', 'Retention Time', 'IS Retention Time',
        ]
    # loop over combined samples (sample number)
    for sample_number in sample_list.index:
        # extract data for the sample of concern
        sample_number_data = data.loc[data['Sample Index'] == sample_number, :]
        # delete duplicate compounds from the extended method if 'core' is the channel_selection
        if channel_selection == 'core':
            extended_duplicate_compounds = sample_number_data.loc[
                ((sample_number_data['Component Name'].duplicated(keep=False))&(sample_number_data['Sample Name'].str.contains('Ext'))),:
            ].index
            data.drop(extended_duplicate_compounds, axis='index', inplace=True)
        # delete duplicate compounds from the core method if 'extended' is the channel_selection
        elif channel_selection == 'extended':
            core_duplicate_compounds = sample_number_data.loc[
                ((sample_number_data['Component Name'].duplicated(keep=False))&(sample_number_data['Sample Name'].str.contains('Core'))),:
            ].index
            data.drop(core_duplicate_compounds, axis='index', inplace=True)

        # loop over all compounds, calculate average over duplicates replace first duplicate with average and delete all other duplicates
        elif channel_selection == 'average':
            for compound in all_compounds:
                sample_number_data_compound = sample_number_data.loc[sample_number_data['Component Name']==compound, :]
                if len(sample_number_data_compound.index > 1):
                    data.loc[sample_number_data_compound.index[0], numeric_data_columns] = sample_number_data_compound[numeric_data_columns].mean()
                    data.drop(sample_number_data_compound.index[1:], axis='index', inplace=True)

    return data

def get_compounds_and_standards(data: pd.DataFrame, sample_list: pd.DataFrame, standard_identifiers: str) -> tuple[list, list, list, list]:
    """Order of PFAS compounds is conserved and the names are split to the (MS/MS) channel, and the TOF channel. If either channel is not available it is set to nan.

    :param data: Data frame containing merged raw data of all files.
    :type data: pd.DataFrame
    :param sample_list: Data frame containing all samples occuring in raw data.
    :type sample_list: pd.DataFrame
    :param standard_identifiers: All substrings necessary to identify mass labeled internal standards from compound names.
    :type standard_identifiers: str
    :return: - compounds_msms: list of pfas compounds from the msms channel in the right order
             - compounds_tof: list of pfas compounds from the tof channel in the right order
             - eis_nis_msms: list of internal standards from the msms channel in the right order
             - eis_nis_tof: list of internal standards from the tof channel in the right order
    :rtype: tuple[list, list, list, list]
    """

    # find suitable sample to iterate over compound names
    # get all samples where both methods core and extended are available
    sample_rows = sample_list.loc[((~np.isnan(sample_list['Sample Index Core'])) & ((~np.isnan(sample_list['Sample Index Extended'])))), :].index
    # choose first sample from full sample list if only one method either core or extended is available for all samples
    if len(sample_rows) == 0:
        sample_rows = 0
    else:
        # get first sample where both methods are available in case that's possible
        sample_row = sample_rows[0]

    # get indices of core and exteded method sample of the selected sample
    [sample_index_core, sample_index_extended] = sample_list.loc[sample_row, ['Sample Index Core', 'Sample Index Extended']]
    sample_indices = [int(sample_index) for sample_index in [sample_index_core, sample_index_extended] if not np.isnan(sample_index)] # delete np.NaNs

    # get list of all compound names considered
    compounds_filtered = data.loc[data['Sample Index'].isin(sample_indices), 'Component Name']
    compounds_sorted = compounds_filtered[~compounds_filtered.str.contains(standard_identifiers)].to_list()  # channel names excluding IPS and IDA
    eis_nis_sorted = compounds_filtered[compounds_filtered.str.contains(standard_identifiers)].to_list()  # channel names excluding IPS and IDA
    
    # initialize lists
    compounds_msms = []  # msms compounds
    compounds_tof = []  # tof compounds
    skip_compounds = []  # list of compounds already considered (can be skipped in followin iterations in loop)
    # loop over all compounds from first sample
    for component in compounds_sorted:
        if component in skip_compounds:  # skip iteration if compound was already considered in previous iterations
            continue
        if '_TOF MS' in component:  # in case compound is from TOF channel
            compounds_tof.append(component)  # add compound to TOF list
            skip_compounds.append(component)  # make sure the TOF compound is not considered more than once
            if component[:-7] in compounds_sorted:  # check if compound is available in corresponding MSMS channel
                compounds_msms.append(component[:-7])  # add msms compound to MSMS list
            else:
                compounds_msms.append(np.nan)  # add NaN to MSMS list if corresponding msms compound is not available
            skip_compounds.append(component[:-7])    # make sure the MSMS compound is not considered more than once
        else:  # in case compound is from MSMS channel
            compounds_msms.append(component)  # add compound to MSMS list
            skip_compounds.append(component)  # make sure the MSMS compound is not considered more than once
            if component + '_TOF MS' in compounds_sorted:  # check if compound is available in corresponding TOF channel
                compounds_tof.append(component + '_TOF MS')  # add tof compound to TOF list
            else:
                compounds_tof.append(np.nan)  # add NaN to TOF list if corresponding tof compound is not available
            skip_compounds.append(component + '_TOF MS')  # make sure the TOF compound is not considered more than once

    # initialize and fill lists of sorted internal standards
    eis_nis_msms = []  # msms internal standards
    eis_nis_tof = []  # tof internal standards
    skip_standards = []  # list of standards already considered (can be skipped in followin iterations in loop)
    # loop over all standards from first sample
    for standard in eis_nis_sorted:
        if standard in skip_standards: # skip iteration if standard was already considered in previous iterations
            continue
        if '_TOF MS' not in standard:  # in case standard is from MSMS channel
            eis_nis_msms.append(standard)  # add standard to MSMS list
            skip_standards.append(standard)  # make sure the MSMS standard is not considered more than once
            if standard[4:] + '_TOF MS' in eis_nis_sorted:  # check if standard is available in corresponding TOF channel
                eis_nis_tof.append(standard[4:] + '_TOF MS')  # add tof standard to TOF list
                skip_standards.append(standard[4:] + '_TOF MS')
            else:
                eis_nis_tof.append(np.nan)  # add NaN to TOF list if corresponding tof standard is not available
        else:  # in case standard is from TOF channel
            # in case standard is an IDA (differentiatiation only possible based on MSMS, as IDA and IPS label not available in TOF channel names)
            if 'IDA-' + standard[:-7] in eis_nis_sorted:
                eis_nis_tof.append(standard)  # add TOF standard to TOF list
                skip_standards.append(standard)  # make sure the TOF standard is not considered more than once
                if standard[4:] + '_TOF MS' in eis_nis_sorted:  # check if standard is available in corresponding TOF channel
                    eis_nis_msms.append('IDA-' + standard[:-7])  # add MSMS standard to MSMS list
                    skip_standards.append('IDA-' + standard[:-7])  # make sure the MSMS standard is not considered more than once
                else:
                    eis_nis_msms.append(np.nan)  # add NaN to TOF list if corresponding tof standard is not available
            elif 'IPS-' + standard[:-7] in eis_nis_sorted:  # in case standard is an IPS
                eis_nis_tof.append(standard)  # add TOF standard to TOF list
                skip_standards.append(standard)  # make sure the TOF standard is not considered more than once
                if standard[4:] + '_TOF MS' in eis_nis_sorted:  # check if standard is available in corresponding TOF channel
                    eis_nis_msms.append('IPS-' + standard[:-7])  # add MSMS standard to MSMS list
                    skip_standards.append('IPS-' + standard[:-7])  # make sure the MSMS standard is not considered more than once
                else:
                    eis_nis_msms.append(np.nan)  # add NaN to TOF list if corresponding tof standard is not available
            else:
                print(f'The standard: {standard} has no corresponding IDA or IPS in the default MS channel. It is ignored in the following calculations.')

    return compounds_msms, compounds_tof, eis_nis_msms, eis_nis_tof

def parse_project_folder_structure(project_folder: str) -> None:
    """Checks if project folder matches given structure

    :param project_folder: Filepath to your project folder
    :type project_folder: str
    :raises ImportError: _description_
    :raises ImportError: _description_
    :raises ImportError: _description_
    :raises ImportError: _description_
    :raises ImportError: _description_
    :raises ImportError: _description_
    :raises ImportError: _description_
    """
    if not os.path.isdir(os.path.join(project_folder)):
        raise ImportError("The project folder is not accessible by the code. Make sure it exists, and the path is indicated correctly.")
    if not os.path.isdir(os.path.join(project_folder, 'processed_data')):
        raise ImportError(
            "There is no subfolder 'processed_data' in your project folder." \
            "Make sure you followed all the instructions indicated in the create_project_folder.ipynb notebook."
            )
    if not os.path.isdir(os.path.join(project_folder, 'processed_data', 'plots')):
        raise ImportError(
            "There is no plots subfolder in 'processed_data' in your project folder." \
            "Make sure you followed all the instructions indicated in the create_project_folder.ipynb notebook."
            )
    if not os.path.isdir(os.path.join(project_folder, 'code_parameters')):
        raise ImportError(
            "There is no subfolder 'code_parameters' in your project folder." \
            "Make sure you followed all the instructions indicated in the create_project_folder.ipynb notebook."
            )
    if not os.path.isfile(os.path.join(project_folder, 'code_parameters', 'recovery_thresholds.csv')):
        raise ImportError(
            "There is no recovery_thresholds.csv in code_parameters or your project folder." \
            "Make sure you followed all the instructions indicated in the create_project_folder.ipynb notebook."
            )
    if not os.path.isfile(os.path.join(project_folder, 'code_parameters', 'sample_parameters.csv')):
        raise ImportError(
            "There is no sample_parameters.csv in code_parameters or your project folder." \
            "Make sure you followed all the instructions indicated in the create_project_folder.ipynb notebook."
            )
    if not os.path.isfile(os.path.join(project_folder, 'code_parameters', 'simulation_parameters.csv')):
        raise ImportError(
            "There is no simulation_parameters.csv in code_parameters or your project folder." \
            "Make sure you followed all the instructions indicated in the create_project_folder.ipynb notebook."
            )
    
def round_to_n_sigfigs(x: float, n: int) -> float:
    """Round number to n significant digits. Author is chatGPT.

    :param x: Floating number to be rounded.
    :type x: float
    :param n: Number of digits to be displayed
    :type n: int
    :return: Rounded number
    :rtype: float
    """    
    if x == 0:
        return 0.0
    if np.isnan(x):
        return np.nan
    return round(x, -int(floor(log10(abs(x)))) + (n - 1))


if __name__ == "__main__":
    data = read_in_data_files(project_folder='test')
    sample_list = get_sample_id_and_name(data=data)
    data = clean_up_data(data=data, sample_list=sample_list, channel_selection='average')

    standard_identifiers = 'EIS|NIS|IDA|IPS|13C|d-|d3-|d5-|18O'
    compounds_msms, compounds_tof, ida_ips_msms, ida_ips_tof = get_compounds_and_standards(data=data, sample_list=sample_list, standard_identifiers=standard_identifiers)