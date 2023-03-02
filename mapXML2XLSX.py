import datetime
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET
import time
from auxFunctions import *

from openpyxl import Workbook
from openpyxl import load_workbook
from datetime import date


# requirements: xlsxwriter, pandas, numpy


# IMPORTANT: THIS XML LIBRARY IS NOT SECURE AGAINST XML VULNERABILITIES
# Read more: https://docs.python.org/3/library/xml.etree.elementtree.html

XML_FILE = "data/SraExperimentPackage.xml"
TEMPLATE_PATH="input_template_empty.xlsx"
OUTPUT_PATH="data/output.xlsx"

FILL_STATIC_VALUES = True # if True, fill static values specific to this dataset

# Sheets names
ANALYSES_SHEET_NAME = "analyses"
BIOSAMPLES_SHEET_NAME = "biosamples"
COHORTS_SHEET_NAME = "cohorts"
DATASETS_SHEET_NAME = "datasets"
INDIVIDUALS_SHEET_NAME = "individuals"
RUNS_SHEET_NAME = "runs"

SHEET_NAMES = [ANALYSES_SHEET_NAME, BIOSAMPLES_SHEET_NAME, COHORTS_SHEET_NAME, DATASETS_SHEET_NAME, INDIVIDUALS_SHEET_NAME, RUNS_SHEET_NAME]

# Pass the path of the xml document 
tree = ET.parse(XML_FILE) 

# get the parent tag 
root = tree.getroot() 

# read excel file with the template + filled information
analyses = pd.read_excel(TEMPLATE_PATH, sheet_name=ANALYSES_SHEET_NAME)
biosamples = pd.read_excel(TEMPLATE_PATH, sheet_name=BIOSAMPLES_SHEET_NAME)
cohorts = pd.read_excel(TEMPLATE_PATH, sheet_name=COHORTS_SHEET_NAME)
datasets = pd.read_excel(TEMPLATE_PATH, sheet_name=DATASETS_SHEET_NAME)
individuals = pd.read_excel(TEMPLATE_PATH, sheet_name=INDIVIDUALS_SHEET_NAME)
runs = pd.read_excel(TEMPLATE_PATH, sheet_name=RUNS_SHEET_NAME)

# create a BFFSheets object
bff = BFFSheets()

# add the sheets to the BFFSheets object
bff.analyses = analyses
bff.biosamples = biosamples
bff.cohorts = cohorts
bff.datasets = datasets
bff.individuals = individuals
bff.runs = runs

for package in root:
    parsePackage(bff, package)

# ---- Final data addings/adjustements ----

# mark empty cells as NaN
bff.analyses.replace("",np.NaN, inplace=True)
bff.biosamples.replace("",np.NaN, inplace=True)
bff.cohorts.replace("",np.NaN, inplace=True)
bff.datasets.replace("",np.NaN, inplace=True)
bff.individuals.replace("",np.NaN, inplace=True)
bff.runs.replace("",np.NaN, inplace=True)

# -- fill cohort generic values --

# create datafram an empty line
emptyDf = pd.DataFrame({
    "id": [np.NaN],
})

# add empty row to cohort table if needed
if ( len(bff.cohorts) == 0 ):
    bff.cohorts = pd.concat((bff.cohorts, emptyDf), ignore_index=True)
    
# add empty row to dataset table if needed
if ( len(bff.datasets) == 0 ):
    bff.datasets = pd.concat((bff.datasets, emptyDf), ignore_index=True)

bff.cohorts['cohortSize'] = len(bff.individuals)

# count number of non-NaN values on the age column in individuals table
ageAvailableCount = bff.individuals['phenotypicFeatures_onset.age.iso8601duration'].count()
bff.cohorts['collectionEvents_eventAgeRange.availabilityCount'] = ageAvailableCount
bff.cohorts['collectionEvents_eventAgeRange.availability'] = 'TRUE' if ageAvailableCount > 0 else 'FALSE'
# same but for sex/gender
genderAvailableCount = bff.individuals['sex.id'].count()
bff.cohorts['collectionEvents_eventGenders.availabilityCount'] = genderAvailableCount
bff.cohorts['collectionEvents_eventGenders.availability'] = 'TRUE' if genderAvailableCount > 0 else 'FALSE'

# this function is called later so it doesn't drown the static values
def addListOfIdsToDataset():
    # get list of biosample ids
    biosampleIds = bff.biosamples['id'].tolist()
    bff.datasets['ids.biosampleIds'] = str(biosampleIds).replace("'", '"')
    # get list of individual ids
    individualIds = bff.individuals['id'].tolist()
    bff.datasets['ids.individualIds'] = str(individualIds).replace("'", '"')
    

# ---- Satic values (added manually for this dataset) ----
if FILL_STATIC_VALUES:
    bff.analyses['aligner'] = 'BWA-MEM'
    bff.analyses['pipelineName'] = 'TSO500 and WES'
    bff.analyses['pipelineRef'] = 'https://www.nature.com/articles/s41525-021-00177-w'
    bff.analyses['variantCaller'] = 'Strelka-2.9.10'

    bff.biosamples['biosampleStatus.id'] = "EFO:0009655"
    bff.biosamples['biosampleStatus.label'] = "abnormal sample"
    bff.biosamples['sampleOriginType.id'] = "OBI:0001876"
    bff.biosamples['sampleOriginType.label'] = "cell culture"


    
    bff.cohorts['id'] = 'stage_II/III_colorectal_cancer'
    bff.cohorts['name'] = 'Stage II/III colorectal cancer'

    bff.cohorts['cohortType'] = 'study-defined'
        
    bff.datasets['dataUseConditions.duoDataUse'] = '[{"id": "DUO:0000019", \
        "label": "publication required", \
        "version": "2019-01-07"}, \
            {\
            "id": "DUO:0000042",\
            "label": "general research use",\
            "version": "2019-01-07"},\
                {\
                "id": "DUO:0000026",\
                "label": "user specific restriction",\
                "version": "2019-01-07"}, \
                    {\
                    "id": "DUO:0000028",\
                    "label": "institution specific restriction",\
                    "version": "2019-01-07"\
                    }\
    ]'.replace(' ', '') # remove spaces
    

    
    bff.datasets['description'] = 'Gene expression and whole exome sequencing of 113 stage II/III colorectal cancer patients with poor outcome'
    bff.datasets['externalUrl'] = 'https://www.nature.com/articles/s41525-021-00177-w'
    bff.datasets['id'] = 'PRJNA689313'
    bff.datasets['name'] = 'Molecular subtyping of stage II/III colorectal cancer with poor outcome'
    bff.datasets['info.origin'] = 'https://www.ncbi.nlm.nih.gov/bioproject/PRJNA689313'
    bff.datasets['info.credits.variantCallingAnalysis'] = "Daniel Sobral"
    bff.datasets['info.credits.studyAuthors'] = str(['Mahdi Golkaram', 'Michael L. Salmans', 'Shannon Kaplan', 'Raakhee Vijayaraghavan', 'Marta Martins', 'Nafeesa Khan', 'Cassandra Garbutt', 'Aaron Wise', 'Joyee Yao', 'Sandra Casimiro', 'Catarina Abreu', 'Daniela Macedo', 'Ana Lúcia Costa', 'Cecília Alvim', 'André Mansinho', 'Pedro Filipe', 'Pedro Marques da Costa', 'Afonso Fernandes', 'Paula Borralho', 'Cristina Ferreira', 'Fernando Aldeia', 'João Malaquias', 'Jim Godsey', 'Alex So', 'Traci Pawlowski', 'Luis Costa', 'Shile Zhang', 'Li Liu']).replace("'",'"')
    bff.datasets['info.credits.study'] = 'https://www.nature.com/articles/s41525-021-00177-w'
    bff.datasets['info.credits.biomaterialProvider'] = 'Luis Costa, Centro Hospitalar Universitário Lisboa Norte, Hospital de Santa Maria, Lisbon, Portugal'
    
    bff.individuals['diseases_diseaseCode.id'] = 'ICD10CM:C18.9'
    bff.individuals['diseases_diseaseCode.label'] = 'stage II/III colorectal cancer'
    bff.individuals['phenotypicFeatures_featureType.id'] = 'HP:0003003'
    bff.individuals['phenotypicFeatures_featureType.label'] = 'Colon cancer'

# call the function to add the lists of ids to the dataset table
addListOfIdsToDataset() 

if True: # If True, export to an Excel file
    try:
        # Create a Pandas Excel writer using XlsxWriter as the engine.
        writer = pd.ExcelWriter(OUTPUT_PATH, engine='xlsxwriter')
        
        # Write each dataframe to a different worksheet.
        bff.analyses.to_excel(writer, sheet_name='analyses', index=False)
        bff.biosamples.to_excel(writer, sheet_name='biosamples', index=False)
        bff.cohorts.to_excel(writer, sheet_name='cohorts', index=False)
        bff.datasets.to_excel(writer, sheet_name='datasets', index=False)
        bff.individuals.to_excel(writer, sheet_name='individuals', index=False)
        bff.runs.to_excel(writer, sheet_name='runs', index=False)
        
        # enlarge the columns to fit the data
        for sheetName in SHEET_NAMES:
            worksheet = writer.sheets[sheetName]
            worksheet.autofit()
        
    finally:
        # Close the Pandas Excel writer and output the Excel file.
        writer.close()
        
#print("Sleeping 10 seconds before exiting...")
#time.sleep(10)
print("* Finished OK! *")

exit(0)