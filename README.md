# 1 Data Analysis Pipeline for targeted LCMS Analysis (data_analysis.ipynb)
Jupyter notebook (python based), which takes raw liquit chromatography mass spectroscopy (LCMS) data (exported table from SCIEX Analyst Software),
computes retention time differences (RTD), method detection limits, recovery rates (RR) or standard response deviations (RSD), and ion abundance ratio deviations (IARD).
Generates plots, flags concentration values according to QAQC criteria, and writes results to excel. Creates long format table (.csv) for data publications.
The analysis is targeted at the precedure of the Lohmann lab located at University of Rhode Island at the graduate school of oceanography.

### Workflow
Collect all input data in a project directory of your choice and run the script **create_project_folder.ipynb**, which creates templates for your input parameters (sample_parameters.csv, recovery_thresholds.csv and simulation_parameters.csv) based on sample and compound names extracted from your raw data.
You find detailed instructions in the notebook itself.

Once you set all input parameters accordingly, make sure you use the right path as project folder and run the script **data_analysis.ipynb**.

Note: Both jupyter notebooks are using functions defined in **utils.py**. In case you are manually downloading scripts, make sure that utils.py and the two mentioned jupyter notebooks are located in the same directory.

##### input data and filenameing conventions
- exported data from Sciex Analyst software. The filename has to end either with '_core' for results originating from the core method, or with '_extended' for results originating from the extended method. The batches to be combined must have the same base name before the fileending: e.g. batch_1_core.txt, and batch_1_extended.txt.
- a test data set is available in the test project folder "test".

##### software
To run the jupyter notebook, you will need any kind of integrated code environment (IDE).
E. g. you can install Anaconda and start jupyter lab from there. Alternatively cloud solutions like google colab can be used.

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
