""" The following file contains functions, which are used from the jupyter notebooks. """

# imports
import pandas as pd
import os
import numpy as np
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from math import log10, floor
from typing import Optional

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

    # Define columns of input which are needed for further processes:
    columns_considered = [
        'Sample Index', 'Sample Name', 'Sample ID', 'Sample Type', 'Batch Name',
        'Component Name',  'Component Group Name', 'IS Name',
        'Acquisition Date & Time', 'Used',
        'Calculated Concentration', 'Actual Concentration',
        'Area', 'Retention Time', 'IS Retention Time',
    ]

    # Load input data files and put them all in one dataframe
    data = pd.DataFrame()  # initialize empty data frames
    sample_index = 0  # initialize Component Index
    core_calibration_detected = False  # set flag variables to be able to delete calibration data if multiple batches are available
    extended_calibration_detected = False  # set flag variables to be able to delete calibration data if multiple batches are available

    # iterate over all files in project folder
    for file in raw_data_files_list:
        # extract relevant information from file
        [base_name, file_ending] = file.split(".")
        batch_name = "_".join(base_name.split("_")[:-1])
        batch_type = base_name.split("_")[-1]

        # read in file
        if file_ending == 'csv':
            this_data = pd.read_csv(
                os.path.join(project_folder, file), delimiter=',', encoding='utf-8', low_memory=False, header=0,
                )
        elif file_ending == 'txt':
            this_data = pd.read_csv(
                os.path.join(project_folder, file), delimiter='\t', encoding='utf-8', low_memory=False, header=0,
                )
        else:
            raise ImportError('Raw input file paths must either be .csv or .txt files.')
        
        # introduce new column batch name
        this_data['Batch Name'] = batch_name

        if batch_type == 'extended':
            # make sure each sample name ends with Ext for extended method and with Core for core method
            mask_names = this_data['Sample Name'].str.endswith('Ext')
            this_data.loc[~mask_names, 'Sample Name'] = [sample_name + ' Ext' for sample_name in this_data['Sample Name'][~mask_names].to_list()]
            # delete calibration data if already included in previous samples
            if extended_calibration_detected:
                this_data = this_data.loc[this_data['Sample Type'] != 'Standard', :]
            else:
                if len(this_data.loc[this_data['Sample Type'] == 'Standard', :]) > 500:
                    extended_calibration_detected = True

        elif batch_type == 'core':
            mask_names = this_data['Sample Name'].str.endswith('Core')
            this_data.loc[~mask_names, 'Sample Name'] = [sample_name + ' Core' for sample_name in this_data['Sample Name'][~mask_names].to_list()]
            # delete calibration data if already included in previous samples
            if core_calibration_detected:
                this_data = this_data.loc[this_data['Sample Type'] != 'Standard', :]
            else:
                if len(this_data.loc[this_data['Sample Type'] == 'Standard', :]) > 500:
                    core_calibration_detected = True
        else:
            raise NameError(
                f"The file {raw_data_file_name} does not comply with file naming conventions." + \
                "Read the instructions for details regarding the filenaming conventions."
                )
        
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
    Batch Name, Sample ID, Sample Type, Sample Name of Core Method, Sample Index of Core Method,
    Sample Name of Extended Method, Sample Index of Extended Method

    :param data: Data frame containing merged raw data of all files.
    :type data: pd.DataFrame
    :return: Data frame containing all samples occuring in raw data, where core and extended method are combined if possible. One combined sample corresponds to one row.
    :rtype: pd.DataFrame
    """    
    # get all sample IDs
    sample_ids = data['Sample ID'].unique()

    # initialize pandas dataframe with sample list
    sample_list = pd.DataFrame(
        {'Sample Number': [], 'Batch Name': [], 'Sample ID': [], 'Sample Type': [], 
         'Sample Name Core': [], 'Sample Index Core': [], 'Sample Name Extended': [], 'Sample Index Extended':[]}
        )
    # initialize sample number
    sample_number = 0

    # loop over sample ids
    for sample_id in sample_ids:
        # extract data for sample id and get all names for related batch
        sample_id_data = data.loc[data['Sample ID'] == sample_id, :]
        batch_names = sample_id_data['Batch Name'].unique()
        for batch_name in batch_names:
            # extract data for batch and get all names for related samples
            sample_id_batch_data = sample_id_data.loc[data['Batch Name'] == batch_name,:]
            sample_types = sample_id_batch_data['Sample Type'].unique()
            for sample_type in sample_types:
                sample_id_batch_type_data = sample_id_batch_data.loc[data['Sample Type'] == sample_type,:]
                sample_names = sample_id_batch_type_data['Sample Name'].unique()
                # get core sample names for related sample ID from related bath
                core_sample_names = [sample_name for sample_name in sample_names if sample_name[-4:] == "Core"]
                extended_sample_names = [sample_name for sample_name in sample_names if sample_name[-3:] == "Ext"]
                # iterate over core sample names
                for core_sample_name in core_sample_names:
                    # get data of core sample name (and batch type and id)
                    core_sample_id_batch_type_name_data = sample_id_batch_type_data.loc[data['Sample Name'] == core_sample_name, :]
                    # get all indices of core samples name (and batch type and id)
                    core_sample_indices = core_sample_id_batch_type_name_data['Sample Index'].unique()
                    # get name of extended sample to pair with
                    extended_sample_name = core_sample_name[:-4] + 'Ext'
                    # drop extended sample from extended sample name list because it is already treated here
                    extended_sample_names = [sample_name for sample_name in extended_sample_names if sample_name != extended_sample_name]
                    # get data of extended sample to pair with 
                    extended_sample_id_batch_type_name_data = sample_id_batch_type_data.loc[data['Sample Name'] == extended_sample_name, :]
                    # get all possible indices of extended samples to pair with
                    extended_sample_indices = extended_sample_id_batch_type_name_data['Sample Index'].unique()

                    # iterate over core sample indices
                    for core_sample_index in core_sample_indices:
                        # if there is an extended sample to pair with, do it and delete corresponding data from extended sample data to pair with
                        if len(extended_sample_indices) > 0:
                            # get index
                            extended_sample_index = extended_sample_indices[0]
                            # drop data of index from sub data frame
                            extended_sample_indices = [sample_index for sample_index in extended_sample_indices if sample_index != extended_sample_index]
                            # save sample to sample list
                            sample_list.loc[sample_number] = [
                                sample_number, batch_name, sample_id, sample_type,
                                core_sample_name, core_sample_index, extended_sample_name, extended_sample_index
                                ]
                        else:
                            # save core sample without extended pairing to sample list
                            sample_list.loc[sample_number] = [
                                sample_number, batch_name, sample_id, sample_type,
                                core_sample_name, core_sample_index, np.nan, np.nan
                                ]
                        # count up sample number
                        sample_number += 1

                    # write unpaired extended data to sample list
                    for extended_sample_index in extended_sample_indices:
                        sample_list.loc[sample_number] = [
                                sample_number, batch_name, sample_id, sample_type,
                                np.nan, np.nan, extended_sample_name, extended_sample_index
                                ]
                        # count up sample number
                        sample_number += 1

                # iterate over remaining extended sample names
                for extended_sample_name in extended_sample_names:
                    # get data of extended sample name (and batch type and id)
                    extended_sample_id_batch_type_name_data = sample_id_batch_type_data.loc[data['Sample Name'] == extended_sample_name, :]
                    # get all indices of extended samples name (and batch type and id)
                    extended_sample_indices = extended_sample_id_batch_type_name_data['Sample Index'].unique()

                    # iterate over extended sample indices
                    for extended_sample_index in extended_sample_indices:
                        # save core sample without extended pairing to sample list
                        sample_list.loc[sample_number] = [
                            sample_number, batch_name, sample_id, sample_type,
                            np.nan, np.nan, extended_sample_name, extended_sample_index, 
                            ]
                        # count up sample number
                        sample_number += 1


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
        {'<1 points': 0, '< 0': 0, 'no root': np.nan, 'NaN': np.nan, 'degenerate': np.nan, 'two roots': np.nan}
        ).astype('float')
    
    # Correct channel names in original data (all of the TOF channels are labelled by _TOF MS, only 2 of them are labeled by only _TOF)
    mask_names = data['Component Name'].str.endswith('_TOF')
    data.loc[mask_names, 'Component Name'] = [compound + ' MS' for compound in data.loc[mask_names, 'Component Name'].to_list()]

    # some have an underscore between TOF and MS, this is removed
    mask_names = data['Component Name'].str.endswith('_TOF_MS')
    data.loc[mask_names, 'Component Name'] = [compound[:-3] + ' MS' for compound in data.loc[mask_names, 'Component Name'].to_list()]

    # some have an underscore between TOF and MS, this is removed
    mask_names = data['Component Name'].str.endswith(' _TOF MS')
    data.loc[mask_names, 'Component Name'] = [compound[:-8] + '_TOF MS' for compound in data.loc[mask_names, 'Component Name'].to_list()]

    # reset sample index from raw data with corresponding sample number from sample list
    # iterate over data rows
    for (row_index, row_data) in data.iterrows():
        # get sample id, sample index and sample name from current row
        sample_index = row_data['Sample Index']
        sample_name = row_data['Sample Name']
        # if the sample is from the core method get the sample number from the core sample index
        if sample_name[-4:] == "Core":
            sample_number = sample_list.loc[(
                (sample_list['Sample Name Core']==sample_name) & 
                (sample_list['Sample Index Core']==sample_index)
                    ),:].index
        # if the sample is from the extended method get the sample number from the extended sample index
        elif sample_name[-3:] == "Ext":
            sample_number = sample_list.loc[(
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
        'Calculated Concentration', 'Actual Concentration',
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

def get_compounds_and_standards(
        data: pd.DataFrame, sample_list: pd.DataFrame, standard_identifiers: str, eis_identifier: str, nis_identifier: str,
        ) -> tuple[list, list, list, list, list, list, list, list]:
    """Order of PFAS compounds is conserved and the names are split to the (MS/MS) channel, and the TOF channel. If either channel is not available it is set to nan.

    :param data: Data frame containing merged raw data of all files.
    :type data: pd.DataFrame
    :param sample_list: Data frame containing all samples occuring in raw data.
    :type sample_list: pd.DataFrame
    :param standard_identifiers: All substrings necessary to identify mass labeled internal standards from compound names.
    :type standard_identifiers: str
    :param eis_identifier: prefix used to identify extracted internal standards (previously known as IDA)
    :type eis_identifier: str
    :param nis_identifier: prefix used to identify non-extracted internal standards (previously known as IPS)
    :type nis_identifier: str
    :return: - compounds_msms: list of pfas compounds from the msms channel in the right order
             - compounds_tof: list of pfas compounds from the tof channel in the right order
             - eis_nis_msms: list of internal standards from the msms channel in the right order
             - eis_nis_tof: list of internal standards from the tof channel in the right order
             - eis_msms: list of extracted internal standards from the msms channel in the right order
             - eis_tof: list of extracted internal standards from the tof channel in the right order
             - nis_msms: list of non-extracted internal standards from the msms channel in the right order
             - nis_tof: list of non-extracted internal standards from the tof channel in the right order
    :rtype: tuple[list, list, list, list, list, list, list, list]
    """

    # find suitable sample to iterate over compound names
    # get all samples where both methods core and extended are available
    sample_rows = sample_list.loc[((~np.isnan(sample_list['Sample Index Core'])) & ((~np.isnan(sample_list['Sample Index Extended'])))), :].index
    # choose first sample from full sample list if only one method either core or extended is available for all samples
    if len(sample_rows) == 0:
        sample_row = 0
    else:
        # get first sample where both methods are available in case that's possible
        sample_row = sample_rows[0]

    # get list of all compound names considered
    compounds_filtered = data.loc[data['Sample Index'] == sample_row, 'Component Name']
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
            if eis_identifier + '-' + standard[:-7] in eis_nis_sorted:
                eis_nis_tof.append(standard)  # add TOF standard to TOF list
                skip_standards.append(standard)  # make sure the TOF standard is not considered more than once
                if standard[4:] + '_TOF MS' in eis_nis_sorted:  # check if standard is available in corresponding TOF channel
                    eis_nis_msms.append(eis_identifier + '-' + standard[:-7])  # add MSMS standard to MSMS list
                    skip_standards.append(eis_identifier + '-' + standard[:-7])  # make sure the MSMS standard is not considered more than once
                else:
                    eis_nis_msms.append(np.nan)  # add NaN to TOF list if corresponding tof standard is not available
            elif nis_identifier + '-' + standard[:-7] in eis_nis_sorted:  # in case standard is an IPS
                eis_nis_tof.append(standard)  # add TOF standard to TOF list
                skip_standards.append(standard)  # make sure the TOF standard is not considered more than once
                if standard[4:] + '_TOF MS' in eis_nis_sorted:  # check if standard is available in corresponding TOF channel
                    eis_nis_msms.append(nis_identifier + '-' + standard[:-7])  # add MSMS standard to MSMS list
                    skip_standards.append(nis_identifier + '-' + standard[:-7])  # make sure the MSMS standard is not considered more than once
                else:
                    eis_nis_msms.append(np.nan)  # add NaN to TOF list if corresponding tof standard is not available
            else:
                print(f'The standard: {standard} has no corresponding IDA or IPS in the default MS channel. It is ignored in the following calculations.')

    # seperate standard list into nis and eis accordingly
    eis_msms = []  # initialize extracted internal standard list of msms channel
    eis_tof = []  # initialize extracted internal standard list of tof channel
    nis_msms = []  # initialize non-extracted internal standard list of msms channel
    nis_tof = []  # initialize non-extracted internal standard list of tof channel
    for (is_msms, is_tof) in zip(eis_nis_msms, eis_nis_tof):
        identifier = is_msms[:3]
        if identifier == nis_identifier:
            nis_msms.append(is_msms)
            nis_tof.append(is_tof)
        elif identifier == eis_identifier:
            eis_msms.append(is_msms)
            eis_tof.append(is_tof)

    return compounds_msms, compounds_tof, eis_nis_msms, eis_nis_tof, eis_msms, eis_tof, nis_msms, nis_tof

def get_eis_for_pfas(data: pd.DataFrame, sample_list: pd.DataFrame, pfas_compounds: list[str]) -> list[str]:
    """Returns list of internal standards corresponsing to input list of pfas_compounds in the corresponding order.

    ::param data: Data frame containing merged raw data of all files.
    :type data: pd.DataFrame
    :param sample_list: Data frame containing all samples occuring in raw data.
    :type sample_list: pd.DataFrame
    :param pfas_compounds: list of native PFAS compounds you want the related extracted internal standards for.
    :type pfas_compounds: list[str]
    :return: List of extracted internal standards corresponding to the native pfas compounds in the order of the input list.
    :rtype: list[str]
    """    
    # find suitable sample to iterate over compound names
    # get all samples where both methods core and extended are available
    sample_rows = sample_list.loc[((~np.isnan(sample_list['Sample Index Core'])) & ((~np.isnan(sample_list['Sample Index Extended'])))), :].index
    # choose first sample from full sample list if only one method either core or extended is available for all samples
    if len(sample_rows) == 0:
        sample_row = 0
    else:
        # get first sample where both methods are available in case that's possible
        sample_row = sample_rows[0]

    example_data = data.loc[data['Sample Index'] == sample_row, ['Component Name', 'IS Name']]
    eis = []

    for native_pfas in pfas_compounds:
        eis_correlated = example_data.loc[example_data['Component Name'] == native_pfas, 'IS Name']
        if len(eis_correlated) >= 1:
            eis.append(example_data.loc[example_data['Component Name'] == native_pfas, 'IS Name'].to_list()[0])
        else:
            eis.append(np.nan)

    return eis


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
    if not os.path.isfile(os.path.join(project_folder, 'code_parameters', 'retention_time_and_iar_thresholds.csv')):
        raise ImportError(
            "There is no retention_time_and_iar_thresholds.csv in code_parameters or your project folder." \
            "Make sure you followed all the instructions indicated in the create_project_folder.ipynb notebook."
            )
    if not os.path.isfile(os.path.join(project_folder, 'code_parameters', 'recovery_or_standard_response_thresholds.csv')):
        raise ImportError(
            "There is no recovery_or_standard_response_thresholds.csv in code_parameters or your project folder." \
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

def reassign_tof_nis_to_eis(data: pd.DataFrame) -> pd.DataFrame:
    """Inputs correctly assigned NIS in column 'Component Group Name' for all EIS of the TOF channel.
    Assigment is based on the csv input file nis_to_eis_assignment.csv located in the lab_folders_directory.
    If needed change accordingly.

    :param data: Data frame containing merged raw data of all files.
    :type data: pd.DataFrame
    :return: Data Frame with corrected column 'Component Group Name' for all EIS of TOF channels
    :rtype: pd.DataFrame
    """    
    assignment = pd.read_csv(os.path.join('lab_parameters', 'nis_to_eis_assignment.csv'))
    eis_compounds = assignment['eis compound'].to_list()
    related_nis_compounds = assignment['nis compound'].to_list()
    for (eis_tof_compound, related_nis_tof_compound) in zip(eis_compounds, related_nis_compounds):
        data.loc[data['Component Name']==eis_tof_compound, 'Component Group Name'] = related_nis_tof_compound
    return data

def change_worksheet_color(filepath: str, sheetnames: list[str], color: str) -> None:
    """changes color of worksheet description

    :param filepath: Filepath of excelfiles
    :type filepath: str
    :param sheetnames: List of sheet names which are coloured
    :type sheetnames: list[str]
    :param color: Colour in RRGGBB Code
    :type color: str
    """    
    workbook = load_workbook(filepath)
    for sheet_name in sheetnames:
        workbook[sheet_name].sheet_properties.tabColor = color
    workbook.save(filepath)
    workbook.close()

def color_fields(
        filepath: str, sheetname: str, rtd: pd.DataFrame, bdl: Optional[pd.DataFrame] = None,
        rr: Optional[pd.DataFrame] = None, iard: Optional[pd.DataFrame] = None
        ) -> None:

    workbook = load_workbook(filepath)
    sheet = workbook[sheetname]

    # 3. Define fills
    rtd_fill = PatternFill(start_color="FF0000", end_color="FF0000", fill_type="solid")
    bdl_fill = PatternFill(start_color="FF8000", end_color="FF8000", fill_type="solid")
    rr_fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
    iard_fill = PatternFill(start_color="7F00FF", end_color="7F00FF", fill_type="solid")

    # 4. Apply coloring based on boolean dataframes
    for row_idx in range(rtd.shape[0]):
        for col_idx in range(rtd.shape[1]):
            excel_row = row_idx + 2  # +2 because Excel rows start at 1, and row 1 is the header
            excel_col = col_idx + 2  # +2 because Excel column start at 1, and column 1 is the index

            cell = sheet.cell(row=excel_row, column=excel_col)

            if rtd.iloc[row_idx, col_idx]:
                cell.fill = rtd_fill
                continue
            if bdl is not None:
                if bdl.iloc[row_idx, col_idx]:
                    cell.fill = bdl_fill
                    continue
            if rr is not None:
                if rr.iloc[row_idx, col_idx]:
                    cell.fill = rr_fill
                    continue
            if iard is not None:
                if iard.iloc[row_idx, col_idx]:
                    cell.fill = iard_fill
                    continue

    # 5. IARD contains internal standards too, make sure they are flagged accordingly.
    if iard is not None:
        for row_idx in range(rtd.shape[0]):
            for col_idx in range(rtd.shape[1], iard.shape[1]):

                excel_row = row_idx + 2  # +2 because Excel rows start at 1, and row 1 is the header
                excel_col = col_idx + 2  # +2 because Excel column start at 1, and column 1 is the index

                cell = sheet.cell(row=excel_row, column=excel_col)

                if iard.iloc[row_idx, col_idx]:
                    cell.fill = iard_fill

    # 5. Save changes
    workbook.save(filepath)
    workbook.close()

if __name__ == "__main__":
    data = read_in_data_files(project_folder='test')
    sample_list = get_sample_id_and_name(data=data)
    data = clean_up_data(data=data, sample_list=sample_list, channel_selection='average')
    data = reassign_tof_nis_to_eis(data)

    standard_identifiers = 'EIS|NIS|IDA|IPS|13C|d-|d3-|d5-|18O'
    compounds_msms, compounds_tof, ida_ips_msms, ida_ips_tof, _, _, _, _ = get_compounds_and_standards(
        data=data, sample_list=sample_list, standard_identifiers=standard_identifiers,
        eis_identifier='IDA', nis_identifier='IPS',
        )