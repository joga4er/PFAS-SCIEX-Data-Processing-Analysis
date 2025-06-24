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

    raw_data_files_list = sorted(raw_data_files_list)  # make sure core method is read in first, then extended method.

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
        base_name = ".".join(file.split(".")[:-1])
        file_ending = file.split(".")[-1]
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
            # make sure each sample name ends with Ext for extended method and with Core for core method
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
                f"The file {file} does not comply with file naming conventions." + \
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
    data.loc[~data['Used'],  ['Calculated Concentration', 'Actual Concentration', 'Area', 'Retention Time', 'IS Retention Time']] = np.nan
    
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
                core_sample_names = [sample_name for sample_name in sample_names if sample_name.endswith("Core")]
                extended_sample_names = [sample_name for sample_name in sample_names if sample_name.endswith("Ext")]
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

    return sample_list

def clean_up_data(data: pd.DataFrame, sample_list: pd.DataFrame) -> pd.DataFrame:
    """Performs major cleanup steps for raw data:
     (i) replace strings in concentration with np.nan or 0.
     (ii) correct patterns of TOF MS channel names

    :param data: Data frame containing merged raw data of all files.
    :type data: pd.DataFrame
    :param sample_list: Data frame containing all samples occuring in raw data. One row combines samples from core method and extended method.
    :type sample_list: pd.DataFrame
    :type channel_selection: str
    :return: Cleaned up data.
    :rtype: pd.DataFrame
    """    
    # TODO make NaNs to zeros and convert zeros to ND at a later stage

    # Clean up 'Calculated Concentration' column
    # first set all NAN values (originally None for non-detect) to zero
    data.loc[data['Calculated Concentration'].isnull(), 'Calculated Concentration'] = 0
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

    data.loc[:,'Sample Number'] = [np.nan] * len(data)

    # introduce column sample number and save right sample number to each sample
    # sample number corresponds to unique index for combination of core and extended, while sample index is unique for every injection
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
        else:
            raise NameError(
                f'Sample with name {sample_name} is not available in sample list. You might have to rerun create_project_folder.ipynb'
                )
        # set column sample number
        data.loc[row_index, 'Sample Number'] = sample_number

    return data

def get_tof_and_msms_compounds(
        data: pd.DataFrame, sample_list: pd.DataFrame, hrms_identifier: str, standard_identifiers: str,
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Order of PFAS compounds is conserved and the names are split to the (MS/MS) channel, and the HRMS channel. If either channel is not available or available twice,
    it is saved to a dataframe meant to delete compounds at a later stage.

    :param data: Data frame containing merged raw data of all files.
    :type data: pd.DataFrame
    :param sample_list: Data frame containing all samples occuring in raw data.
    :type sample_list: pd.DataFrame
    :param hrms_identifier: Identifier for high resolution mass spectrometry channel, usually '_HRMS' or '_TOF MS'.
    :type hrms_identifier: str
    :param standard_identifiers: All substrings necessary to identify mass labeled internal standards from compound names.
    :type standard_identifiers: str
    :return: - compounds: Dataframe containing compounds in right order and the information of which method is used to extract the information from.
             - delete_compounds: Dataframe containing compounds which should be deleted, because they do not have a MSMS or HRMS counterpart or two identicals exist.
    :rtype: tuple[pd.DataFrame, pd.DataFrame]
    """

    # find suitable sample to iterate over compound names
    # get all sample indices where both methods core and extended are available
    sample_rows = sample_list.loc[((~np.isnan(sample_list['Sample Index Core'])) & ((~np.isnan(sample_list['Sample Index Extended'])))), :].index
    # choose first sample from full sample list if only one method either core or extended is available for all samples
    if len(sample_rows) == 0:
        compounds_filtered = data.loc[data['Sample Number'] == 0, ['Sample Index', 'Component Name']]
        if pd.isnull(sample_list.loc[0, 'Sample Index Core']):
            core_index = np.nan
        else:
            core_index = int(sample_list.loc[0, 'Sample Index Core'])
        if pd.isnull(sample_list.loc[0, 'Sample Index Extended']):
            extended_index = np.nan
        else:
            extended_index = int(sample_list.loc[0,'Sample Index Extended'])
    else:
        # get first sample where both methods are available in case that's possible
        sample_row = sample_rows[0]
        core_index = int(sample_list.loc[sample_row, 'Sample Index Core'])
        extended_index = int(sample_list.loc[sample_row,'Sample Index Extended'])
        compounds_filtered = data.loc[data['Sample Number'] == sample_row, ['Sample Index', 'Component Name']]

    index_to_method_mapper = {core_index: 'core', extended_index: 'extended'}
    # make sure core sample comes first in order
    compounds_sorted = compounds_filtered.loc[~compounds_filtered['Component Name'].str.contains(standard_identifiers), :]  # channel names and sample indices excluding IPS and IDA
    # initialize lists for dataframes of compounds, and compounds to delete
    compounds = []
    delete_compounds = []
    # list of compounds already considered (can be skipped in following iterations in loop)
    skip_compounds = []
    # loop over all compounds from first sample row
    for (_, compound_row) in compounds_sorted.iterrows():
        compound = compound_row['Component Name']
        if compound in skip_compounds:  # skip iteration if compound was already considered in previous iterations
            continue
        if compound.endswith(hrms_identifier):  # in case compound is from HRMS channel
            # get related MSMS compound
            msms_compound = compounds_sorted.loc[compounds_sorted['Component Name'] == compound[:-(1) * len(hrms_identifier)],:]
            # if no msms_compound is available, make sure component is deleted at a later point
            if msms_compound.empty:
                compounds.append(
                    {'MSMS Compound Name': np.nan, 'HRMS Compound Name': compound, 'from method': index_to_method_mapper[int(compound_row['Sample Index'])]}
                )
            # if only one msms compound is available save compound and related msms to dataframe
            elif len(msms_compound) == 1:
                compounds.append(
                    {'MSMS Compound Name': msms_compound['Component Name'].values[0], 'HRMS Compound Name': compound, 'from method': index_to_method_mapper[int(msms_compound['Sample Index'].values[0])]}
                )
                # if there are two HRMS compounds, delete the one from the current method - works as long as ms compound becomes for HRMS in order.
                if len(compounds_sorted.loc[compounds_sorted['Component Name'] == compound,:]) > 1:
                    delete_compounds.append({'Compound Name': compound, 'from method': index_to_method_mapper[int(compound_row['Sample Index'])]})
            # keep track of problems
            else:
                print('We obviously have a problem here')
            skip_compounds.append(compound)  # make sure the HRMS compound is not considered more than once
            skip_compounds.append(compound[:-(1) * len(hrms_identifier)])  # make sure the MS MS compound is not considered twice
        else:  # in case compound is from MSMS channel
             # get related HRMS compound
            hrms_compound = compounds_sorted.loc[compounds_sorted['Component Name'] == compound + hrms_identifier,:]
            # if no hrms_compound is available, make sure component is deleted at a later point
            if hrms_compound.empty:
                compounds.append(
                    {'MSMS Compound Name': compound, 'HRMS Compound Name': np.nan, 'from method': index_to_method_mapper[int(compound_row['Sample Index'])]}
                )
            # if only one hrms compound is available save compound and related msms to dataframe
            elif len(hrms_compound) == 1:
                compounds.append(
                    {'MSMS Compound Name': compound, 'HRMS Compound Name': hrms_compound['Component Name'].values[0], 'from method': index_to_method_mapper[int(compound_row['Sample Index'])]}
                )
            else:
                if index_to_method_mapper[int(compound_row['Sample Index'])] == 'core':
                    compounds.append(
                    {'MSMS Compound Name': compound, 'HRMS Compound Name': hrms_compound['Component Name'].values[0], 'from method': 'core'}
                    )
                    delete_compounds.append({'Compound Name': hrms_compound['Component Name'].values[0], 'from method': 'extended'})
                else:
                    compounds.append(
                        {'MSMS Compound Name': compound, 'HRMS Compound Name': hrms_compound['Component Name'].values[0], 'from method': 'extended'}
                    )
                    delete_compounds.append({'Compound Name': hrms_compound['Component Name'].values[0], 'from method': 'core'})

            skip_compounds.append(compound)  # make sure the HRMS compound is not considered more than once
            skip_compounds.append(compound + hrms_identifier)  # make sure the MS MS compound is not considered twice
    compounds = pd.DataFrame(compounds)
    delete_compounds = pd.DataFrame(delete_compounds)
    return(compounds, delete_compounds)

def get_tof_and_msms_standards(
        data: pd.DataFrame, sample_list: pd.DataFrame, hrms_identifier: str, standard_identifiers: str, eis_identifier: str, nis_identifier: str,
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Order of standards is conserved and the names are split to the (MS/MS) channel, and the HRMS channel. If either channel is not available,
    it is saved to a dataframe meant to delete standards at a later stage.

    :param data: Data frame containing merged raw data of all files.
    :type data: pd.DataFrame
    :param sample_list: Data frame containing all samples occuring in raw data.
    :type sample_list: pd.DataFrame
    :param standard_identifiers: All substrings necessary to identify mass labeled internal standards from compound names.
    :type standard_identifiers: str
    :param hrms_identifier: Identifier for high resolution mass spectrometry channel, usually '_HRMS' or '_TOF MS'.
    :type hrms_identifier: str
    :param eis_identifier: Identifier for EIS channel, usually 'EIS' or 'IDA'.
    :type eis_identifier: str
    :param nis_identifier: Identifier for NIS channel, usually 'NIS' or 'IPS'.
    :type nis_identifier: str
    :return: - standards: Dataframe containing standards in right order and the type of standard.
             - delete_standards: Dataframe containing standards which should be deleted, because they do not have a MSMS or HRMS counterpart.
    :rtype: tuple[pd.DataFrame, pd.DataFrame]
    """
    # find suitable sample to iterate over compound names
    # get all sample indices where both methods core and extended are available
    sample_rows = sample_list.loc[((~np.isnan(sample_list['Sample Index Core'])) & ((~np.isnan(sample_list['Sample Index Extended'])))), :].index
    # choose first sample from full sample list if only one method either core or extended is available for all samples
    if len(sample_rows) == 0:
        compounds_filtered = data.loc[data['Sample Number'] == 0, ['Sample Index', 'Component Name']]
        if pd.isnull(sample_list.loc[0, 'Sample Index Core']):
            core_index = np.nan
        else:
            core_index = int(sample_list.loc[0, 'Sample Index Core'])
        if pd.isnull(sample_list.loc[0, 'Sample Index Extended']):
            extended_index = np.nan
        else:
            extended_index = int(sample_list.loc[0,'Sample Index Extended'])
    else:
        # get first sample where both methods are available in case that's possible
        sample_row = sample_rows[0]
        core_index = int(sample_list.loc[sample_row, 'Sample Index Core'])
        extended_index = int(sample_list.loc[sample_row,'Sample Index Extended'])
        compounds_filtered = data.loc[data['Sample Number'] == sample_row, ['Sample Index', 'Component Name']]

    index_to_method_mapper = {core_index: 'core', extended_index: 'extended'}
    # make sure core sample comes first in order
    eis_nis_sorted = compounds_filtered.loc[compounds_filtered['Component Name'].str.contains(standard_identifiers), :]  # channel names and sample indices excluding IPS and IDA

    # initialize lists for dataframes of standards
    standards = []
    delete_standards = []

    skip_standards = []  # list of standards already considered (can be skipped in followin iterations in loop)
    # loop over all standards from first sample
    for (_,standard_row) in eis_nis_sorted.iterrows():
        standard = standard_row['Component Name']
        if standard in skip_standards: # skip iteration if standard was already considered in previous iterations
            continue
        if not standard.endswith(hrms_identifier):  # in case standard is from MSMS channel
            hrms_standard = eis_nis_sorted.loc[eis_nis_sorted['Component Name'] == standard[4:] + hrms_identifier,:]
            if len(hrms_standard) == 0:
                # exclude IPS-1802_PFHxS
                if standard == 'IPS-18O2_PFHxS':
                    standards.append({'MSMS Standard Name': standard, 'HRMS Standard Name': np.nan, 'Standard Type': standard[:3]})
                else:
                    delete_standards.append({'Compound Name': standard})
            elif len(hrms_standard) <= 2:
                standards.append({'MSMS Standard Name': standard, 'HRMS Standard Name': standard[4:] + hrms_identifier, 'Standard Type': standard[:3]})
            else:
                print('problem')
            skip_standards.append(standard)  # make sure the MSMS standard is not considered more than once
            skip_standards.append(standard[4:] + hrms_identifier)  # make sure the HRMS standard is not considered more than once  
        else:  # in case standard is from HRMS channel
            msms_eis_standard = eis_nis_sorted.loc[eis_nis_sorted['Component Name'] == eis_identifier + standard[:-(1) * len(hrms_identifier)],:]
            msms_nis_standard = eis_nis_sorted.loc[eis_nis_sorted['Component Name'] == nis_identifier + standard[:-(1) * len(hrms_identifier)],:]
            if len(msms_eis_standard) == 0:
                if len(msms_nis_standard) == 0:
                    delete_standards.append({'Compound Name': standard})
                elif len(msms_nis_standard) == 1:
                    standards.append({'MSMS Standard Name': msms_nis_standard.loc['Component Name', :].values[0], 'HRMS Standard Name': standard, 'Standard Type': nis_identifier})
                    skip_standards.append(msms_nis_standard.loc['Component Name', :].values[0])  # make sure the MSMS standard is not considered more than once
                else:
                    print('problem: ', standard)
            elif len(msms_eis_standard) == 1:
                if len(msms_nis_standard) == 0:
                    standards.append({'MSMS Standard Name': msms_nis_standard.loc['Component Name', :].values[0], 'HRMS Standard Name': standard, 'Standard Type': nis_identifier})
                    skip_standards.append(msms_eis_standard.loc['Component Name', :].values[0])  # make sure the MSMS standard is not considered more than once
                else:
                    print('problem', standard)
            else:
                print('problem: ', standard)
            skip_standards.append(standard)  # make sure the MSMS standard is not considered more than once

    standards = pd.DataFrame(standards)
    delete_standards = pd.DataFrame(delete_standards)

    return standards, delete_standards

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

    example_data = data.loc[data['Sample Number'] == sample_row, ['Component Name', 'IS Name']]
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
    if not os.path.isfile(os.path.join(project_folder, 'code_parameters', 'rt_iar_thresholds_channel_selection.csv')):
        raise ImportError(
            "There is no rt_iar_thresholds_channel_selection.csv in code_parameters or your project folder." \
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
    """Inputs correctly assigned NIS in column 'Component Group Name' for all EIS of the HRMS channel.
    Assigment is based on the csv input file nis_to_eis_assignment.csv located in the lab_folders_directory.
    If needed change accordingly.

    :param data: Data frame containing merged raw data of all files.
    :type data: pd.DataFrame
    :return: Data Frame with corrected column 'Component Group Name' for all EIS of HRMS channels
    :rtype: pd.DataFrame
    """    
    assignment = pd.read_csv(os.path.join('lab_parameters', 'nis_to_eis_assignment.csv'))
    eis_compounds = assignment['eis compound'].to_list()
    related_nis_compounds = assignment['nis compound'].to_list()
    for (eis_hrms_compound, related_nis_hrms_compound) in zip(eis_compounds, related_nis_compounds):
        data.loc[data['Component Name']==eis_hrms_compound, 'Component Group Name'] = related_nis_hrms_compound
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
    data = read_in_data_files(project_folder='julie_liver_kansas')
    sample_list = get_sample_id_and_name(data=data)
    data = clean_up_data(data=data, sample_list=sample_list)
    data = reassign_tof_nis_to_eis(data)

    standard_identifiers = 'EIS|NIS|IDA|IPS|13C|d-|d3-|d5-|18O'
    hrms_identifier = '_TOF MS'
    compounds, delete_compounds = get_tof_and_msms_compounds(
        data=data, sample_list=sample_list, hrms_identifier=hrms_identifier, standard_identifiers=standard_identifiers,
        )
    standards, delete_standards = get_tof_and_msms_standards(
        data=data, sample_list=sample_list, hrms_identifier=hrms_identifier, standard_identifiers=standard_identifiers, eis_identifier='IDA', nis_identifier='IPS',
    )