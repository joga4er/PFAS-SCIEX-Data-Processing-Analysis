### Data Analysis Pipeline for targeted LCMS Analysis
Jupyter notebook, which takes raw liquit chromatography mass spectroscopy (LCMS) data (exported table from SCIEX Analyst Software),
computes recovery rates, method detection limits, and ratios of default channel to MS TOF channel.
Generates plots and writes results to excel and creates long format table (.csv) for data publications.
The analysis is targeted at the precedure of the Lohmann lab located at University of Rhode Island at the graduate school of oceanography.

### Guidelines/Workflow
Collect all needed input data in a project directory of your choice and indicate the paths to your input data in the first code block of the script xx_xx_xxxx_data_analysis.ipynb. Decide where the result of the analysis should be saved to and indicate all result paths in the first code block.

When you run the script for the first time two .csv files will be created to input relevant information of your samples like volume and final desired concentration units. Once you provided all the information save the file, close it and run the script again.

##### input data
You will process

##### software
To run the jupyter notebook, you will need any kind of integrated code environment (IDE).
E. g. you can install Anaconda and start jupyter lab from there. Alternatively cloud solutions like google colab can be used.

### Contact
johanna.ganglbauer@uri.edu

### Ackknowledgement
This work is supported by the National Institute of Environmental Health under grant P42ES027706 in superfund research project Sources, Transport, Exposure & Effects of PFAS (STEEP).
<img src="https://web.uri.edu/wp-content/uploads/sites/1022/NIEHS_SRP_Log_horz_600.png" width="50%">
<img src="https://web.uri.edu/wp-content/uploads/sites/1022/NIEHS_SRP_Log_horz_600.png](https://web.uri.edu/wp-content/uploads/sites/1022/steep-logo.png" width="50%">
