# 1 Data Analysis Pipeline for targeted LCMS Analysis (data_analysis.ipynb)
Jupyter notebook (python based), which processes data from Sciex QTOF high resolution liquit chromatography - tandem mass spectroscopy (LCMS-MS) and evaluates quality control criteria in line with EPA1633A.
It takes raw data (exported tables from SCIEX Analyst Software) from two methods containing targeted PFAS compounds, combines the methods for each batch, and computes the following :
- retention time differences (RTD) to related extracted internal standard
- method detection limits (MDL)
- extracted internal standard (EIS) recovery rates (RR) or standard response deviations (RSD)
- ion abundance ratio deviations (IARD).
Generates plots, flags concentration values according to QAQC criteria, and writes results to excel. Creates long format table (.csv) for data publications.
The analysis is targeted at the precedure of the Lohmann lab located at University of Rhode Island at the Graduate School of Oceanography.

### Workflow
Collect all input data in a project directory of your choice and run the script **create_project_folder.ipynb**. Make sure you set the path variable **project_folder** accordingly. The script creates templates for your input parameters (recovery_or_standard_response_thresholds.csv, rt_iar_thresholds_channel_selection.csv, sample_parameters.csv and simulation_parameters.csv) based on sample and compound names extracted from your raw data.
You find detailed instructions in the notebook itself.

Once you set all input parameters accordingly, make sure you use the right path as project folder and run the script **data_analysis.ipynb**. It will generate an excel spreadsheet with detailed QAQC results, as well as a .csv long format table suitable for data sharing and publications.

Note: Both jupyter notebooks are using functions defined in **utils.py** and data deposited within the folder lab_parameters. In case you are manually downloading scripts, make sure that utils.py and the two mentioned jupyter notebooks are located in the same directory, as well as the data folder lab_parameters.

##### input data and filenameing conventions
- exported data from Sciex Analyst software. The filename has to end either with '_core' for results originating from the core method, or with '_extended' for results originating from the extended method. The batches to be combined must have the same base name before the fileending: e.g. batch_1_core.txt, and batch_1_extended.txt.
- a test data set is available in the test project folder "test".

##### software
To run the jupyter notebook, you will need any kind of integrated code environment (IDE).
E. g. you can install Anaconda and start jupyter lab from there. Alternatively cloud solutions like google colab can be used.

##### definitions
- **extracted internal standards (EIS)**: mass-labeled internal standards spiked to the sample before the analytical process (extraction, clean-up, etc.), formally known as **IDA**.
- **non-extracted internal standards (NIS)**: mass-labeled internal standards spiked to the sample after the analytical process (extraction, clean-up, etc), but before LCMS/MS, also known as **injection standard**, formally known as **IPS**.
- **target analytes**: PFAS compounds to be quantified in LCMS/MS analysis, also known as **native compounds**.
- **HRMS** channel: high resolution mass spectrometry channel, which screens for ionized native compounds. Used to confirm the detection of native compounds. Formally known as time of flight **TOF** channel.
- **MS/MS** channel: mass spectrometry channel, which screens for ionized, fragmented ions. Used to quantify concentration of native compounds. 

# 2 Pipeline to link lcms data and observe correlations (link_data.ipynb)
Jupyter notebook (R based), which links results from lcms data analysis pipeline and proteomics results, evaluates Pearson correlation coefficients and p-values, and creates plots.

##### input data
- .csv file containing name of all samples and links to the sample name in lcms and proteomics respectively
- .xlsx containing lcms results (will be combined to data analysis workflow above in the future)
- .xlsx containg proteomics results
- at this stage no test data set is publicly available.

### Contact
johanna.ganglbauer@uri.edu

### Ackknowledgement
This work is supported by the National Institute of Environmental Health under grant P42ES027706 in superfund research project Sources, Transport, Exposure & Effects of PFAS (STEEP).
<img src="https://web.uri.edu/wp-content/uploads/sites/1022/NIEHS_SRP_Log_horz_600.png" width="40%">
<img src="https://web.uri.edu/wp-content/uploads/sites/1022/NIEHS_SRP_Log_horz_600.png](https://web.uri.edu/wp-content/uploads/sites/1022/steep-logo.png" width="40%">
