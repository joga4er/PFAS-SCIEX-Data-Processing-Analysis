### Calculated instrumentation detection limits from calibration data
from typing import Optional
import pandas as pd

from utils import clean_up_data, reassign_tof_nis_to_eis, get_tof_and_msms_compounds, get_sample_id_and_name

# global variable definitions
standard_identifiers = 'EIS|NIS|IDA|IPS|13C|d-|d3-|d5-|18O'
hrms_identifier = '_TOF MS'
import os

def calculate_idls(matrix_name: str, filepath_core: Optional[str], filepath_extended: Optional[str],):

    # Define columns of input which are needed for further processes:
    columns_considered = [
        'Sample Index', 'Sample Name', 'Sample ID', 'Sample Type', 'Calculated Concentration',
        'Actual Concentration', 'Component Name', 'Used', 'Signal / Noise'
    ]

    if filepath_core is not None:
        # Read core data
        if filepath_core.endswith('.csv'):
            data_core = pd.read_csv(
                filepath_core, delimiter=',', encoding='utf-8', header=0,
                )
        elif filepath_core.endswith('.txt'):
            data_core = pd.read_csv(
                filepath_core, delimiter='\t', encoding='utf-8', header=0,)
        else:
            raise ImportError('Raw input file paths must either be .csv or .txt files.')
        data_core = data_core[columns_considered]
        mask_names = data_core['Sample Name'].str.endswith('Core')
        data_core.loc[~mask_names, 'Sample Name'] = [sample_name + ' Core' for sample_name in data_core['Sample Name'][~mask_names].to_list()]

    if filepath_extended is not None:
        # Read core data
        if filepath_extended.endswith('.csv'):
            data_extended = pd.read_csv(
                filepath_extended, delimiter=',', encoding='utf-8', low_memory=False, header=0,
                )
        elif filepath_extended.endswith('.txt'):
            data_extended = pd.read_csv(
                filepath_extended, delimiter='\t', encoding='utf-8', header=0,
                )
        else:
            raise ImportError('Raw input file paths must either be .csv or .txt files.')
        data_extended = data_extended[columns_considered]
        mask_names = data_extended['Sample Name'].str.endswith('Ext')
        data_extended.loc[~mask_names, 'Sample Name'] = [sample_name + ' Ext' for sample_name in data_extended['Sample Name'][~mask_names].to_list()]

    # Combine data
    if filepath_core is not None and filepath_extended is not None:
        data_extended['Sample Index'] = data_extended['Sample Index'] + data_core['Sample Index'].max() + 1
        data = pd.concat([data_core, data_extended], ignore_index=True)
    elif filepath_core is not None:
        data = data_core
    elif filepath_extended is not None:
        data = data_extended
    else:
        raise ValueError('At least one file path must be provided for core or extended data.')
    
    data['Batch Name'] = matrix_name  # add batch name to data
    
    # extract sample names and compound names from raw data
    sample_list = get_sample_id_and_name(data)
    
    # calls function to get complete list of samples
    data = clean_up_data(data=data, sample_list=sample_list)

    # get the assignment of NIS for HRMS channel EIS right
    data = reassign_tof_nis_to_eis(data=data)

    # get compounds dataframe and delete 'useless compounds'
    compounds, delete_compounds = get_tof_and_msms_compounds(data=data, sample_list=sample_list, hrms_identifier=hrms_identifier, standard_identifiers=standard_identifiers)

    # delete detected compounds accordingly. 
    # Usualy HRMS channels from the core method have to be deleted, because they also occur in the extended method, where they are integrated with more care.
    if not delete_compounds.empty:  # check if data frame is empty
        for method in delete_compounds['from method'].unique():  # loop over 'core' method and 'extended method'
            # get all sample indices from relevant method
            if method == 'core':
                indices = [int(index) for index in sample_list['Sample Index Core'].dropna().tolist()]
            elif method == 'extended':
                indices = [int(index) for index in sample_list['Sample Index Extended'].dropna().tolist()]
            # loop over compounds to be deleted within the method and delete them accordingly
            for compound in delete_compounds.loc[delete_compounds['from method'] == method, 'Compound Name'].tolist():
                data = data.loc[~(
                    (data['Component Name'] == compound) & (data['Sample Index'].isin(indices))
                ), :]

    idl_data = pd.DataFrame(columns=["Sample Code", "Unit"] + compounds['MSMS Compound Name'].tolist())
    idl_data.loc[0, 'Sample Code'] = 'MSMS IDL'
    idl_data.loc[1, 'Sample Code'] = 'MSMS LOQ'
    idl_data.loc[2, 'Sample Code'] = 'HRMS IDL'
    idl_data.loc[3, 'Sample Code'] = 'HRMS LOQ'
    idl_data['Unit'] = 'ng/sample'
    
    calibration_data = data.loc[data['Sample Type'] == 'Standard', :]
    for (msms_compound, tof_compound) in zip(compounds['MSMS Compound Name'].tolist(), compounds['HRMS Compound Name'].tolist()):
        msms_data = calibration_data.loc[calibration_data['Component Name'] == msms_compound, :]
        tof_data = calibration_data.loc[calibration_data['Component Name'] == tof_compound, :]
        min_idl = 1e-3
        for calibration_point in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            previous = msms_data.loc[(
                (msms_data['Sample ID'] == f'CS{calibration_point}') &
                (msms_data['Used'] == True)
            ), :]
            if previous['Signal / Noise'].isna().sum() == 0:
                this_point = msms_data.loc[(
                    (msms_data['Sample ID'] == f'CS{calibration_point + 1}') &
                    (msms_data['Used'] == True)
                ), :]
                idl = 10 * this_point['Actual Concentration'].mean() / this_point['Signal / Noise'].mean()
                idl = max(idl, min_idl)
                idl_data.loc[0, msms_compound] = round(idl, ndigits=3)
                idl_data.loc[1, msms_compound] = previous['Actual Concentration'].mean()
                break
            else:
                min_idl = previous['Actual Concentration'].mean()
        min_idl = 1e-3
        for calibration_point in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]:
            previous = tof_data.loc[(
                (tof_data['Sample ID'] == f'CS{calibration_point}') &
                (tof_data['Used'] == True)
            ), :]
            if previous['Signal / Noise'].isna().sum() == 0:
                this_point = tof_data.loc[(
                    (tof_data['Sample ID'] == f'CS{calibration_point + 1}') &
                    (tof_data['Used'] == True)
                ), :]
                idl = 10 * this_point['Actual Concentration'].mean() / this_point['Signal / Noise'].mean()
                idl = max(idl, min_idl)
                idl_data.loc[2, msms_compound] = round(idl, ndigits=3)
                idl_data.loc[3, msms_compound] = previous['Actual Concentration'].mean()
                break
            else:
                min_idl = previous['Actual Concentration'].mean() # ensure that IDL is not smaller than point where peak was not detected.

    idl_data.to_csv(
        os.path.join('lab_parameters', f'{matrix_name}_idl.csv'), index=False, encoding='utf-8'
    )


if __name__ == "__main__":
    calculate_idls(
        matrix_name='Test Matrix',
        filepath_core=r'test\241031_test_data_core.txt',
        filepath_extended=r'test\241031_test_data_extended.txt',
    )