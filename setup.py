from setuptools import setup, find_packages

setup(
    name='lohmann',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        "pandas>=0.23",
        "numpy",
        "matplotlib",
        "seaborn",
        "scikit-learn==1.5.0",
        "jinja2"
    ],
)