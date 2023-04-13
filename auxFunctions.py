# Description: Auxiliary functions
import pandas as pd
from pandas import DataFrame

class BFFSheets:
    analyses: DataFrame = pd.DataFrame()
    biosamples = pd.DataFrame()
    cohorts : DataFrame = pd.DataFrame()
    datasets : DataFrame = pd.DataFrame()
    individuals : DataFrame = pd.DataFrame()
    runs : DataFrame = pd.DataFrame()

def parsePackage(bffSheets:BFFSheets, package) -> int:
    
    # --- Parse XML values in this package ---
    
    exp = package.find('EXPERIMENT')
    individualId = exp.attrib['alias'].split("_")[0]
    libStrategy = exp.find("DESIGN").find("LIBRARY_DESCRIPTOR").find("LIBRARY_STRATEGY").text
    
    libSourceText = exp.find("DESIGN").find("LIBRARY_DESCRIPTOR").find("LIBRARY_SOURCE").text
    libSourceId, libSourceLabel = getOntologyCodeFromLabelLibSource(libSourceText)
    
    
    libSelection = libSource = exp.find("DESIGN").find("LIBRARY_DESCRIPTOR").find("LIBRARY_SELECTION").text
    
    # this should contain at most 1 value, but in case it has more the script adds all of them
    libLayout = ""
    for layout in exp.find("DESIGN").find("LIBRARY_DESCRIPTOR").find("LIBRARY_LAYOUT"):
        libLayout += layout.tag + ","
    libLayout = libLayout.strip(",") # remove last separator
    
    platform = exp.find("PLATFORM")[0].tag
    platformLabel = exp.find("PLATFORM")[0].find("INSTRUMENT_MODEL").text
    
    sample = package.find('SAMPLE')
    for attribute in sample.find("SAMPLE_ATTRIBUTES"):
        attribTag = attribute.find("TAG").text
        attribVal = attribute.find("VALUE").text
        
        if attribTag == "age":
            age = attribVal
        elif attribTag == "sex":
            sex = attribVal
            sexId, sexLabel = getOntologyCodeFromLabelSex(sex)
        elif attribTag == "disease_stage":
            stage = attribVal
            
    runSet = package.find("RUN_SET")
    if len(runSet) != 1:
        print(f"ERROR: This script was designed to handle run_sets with a single element, found a run_set with {len(runSet)} elements")
        return -1
    
    run = runSet[0]
    runId = run.find("IDENTIFIERS").find("PRIMARY_ID").text
    
    # ATENTION: We use this way to get biosampleId to match the VCF values presented in genomicVariations
    biosampleId = run.find("IDENTIFIERS").find("SUBMITTER_ID").text.split("_L")[0].replace("-","_")
    #biosampleId = sample.attrib['alias']
    
    runDate = -1
    for sraFile in run.find("SRAFiles").findall("SRAFile"):
        if sraFile.attrib['filename'] == runId:
            runDate = sraFile.attrib['date'].split(" ")[0] # remove the hour part of the date
    
    if runDate == -1:
        print("ERROR: Couldn't find runDate")
        return -1
    
    
    # --- Fill database with parsed values ---
    
    # handle data not found in the XML
    analysesId = biosampleId
    analysesDate = runDate
    
    # create dataframe with new analyses data
    analysesDf = pd.DataFrame({
        "id": [analysesId],
        "biosampleId": [biosampleId],
        "individualId": [individualId],
        "runId": [runId],
        "analysisDate": [analysesDate],
    })
    
    # add data to table
    bffSheets.analyses = pd.concat((bffSheets.analyses, analysesDf), ignore_index=True)
    
    # create dataframe with new biosamples data
    biosamplesDf = pd.DataFrame({
      "id": [biosampleId],
      "individualId": [individualId],
      #"phenotypicFeatures_onset.age.iso8601duration": [getISO8601DurationFromAge(age)],
      #"measurements_observationMoment.age.iso8601duration": [getISO8601DurationFromAge(age)],
      "tumorGrade.label": [mapTumorGrade2Ontology(stage)[1]],
      "tumorGrade.id": [mapTumorGrade2Ontology(stage)[0]],
    })
    
    # add data to table
    bffSheets.biosamples = pd.concat((bffSheets.biosamples, biosamplesDf), ignore_index=True)
    
    # add data to individuals table
    # check if the individual is already in the table
    if individualId not in bffSheets.individuals["id"].values:
        # the individual is not in the table, add it
        individualsDf = pd.DataFrame({
            "id": [individualId],
            "sex.label": [sexLabel],
            "sex.id": [sexId],
            # TODO FIND OUT HOW TO ENABLE THIS
            #"phenotypicFeatures_onset.age.iso8601duration": [getISO8601DurationFromAge(age)],
            # TODO CHECK THAT THIS IS CORRECT
            #"phenotypicFeatures_onset": ["Age"], # adding column to select the type of age param 
        })
        
        bffSheets.individuals = pd.concat((bffSheets.individuals, individualsDf), ignore_index=True)
        
    # add data to runs table
    runsDf = pd.DataFrame({
        "id": [runId],
        "biosampleId": [biosampleId],
        "individualId": [individualId],
        "libraryLayout": [libLayout],
        "librarySelection": [libSelection],
        "librarySource.label": [libSourceLabel],
        "librarySource.id": [libSourceId],
        "libraryStrategy": [libStrategy],
        "platform": [platform],
        "platformModel.label": [platformLabel],
        "platformModel.id": [ getOntologyCodeFromLabelPlatform(platformLabel) ],
        "runDate": [runDate],
    })

    # add data to table
    bffSheets.runs = pd.concat((bffSheets.runs, runsDf), ignore_index=True)
    
    return 0

def addRow(df:DataFrame, row):
    df.append(row, ignore_index=True)

# "IIIA" -> ("NCIT:C28076", "Grade 3a")
def mapTumorGrade2Ontology(gradeStr) -> tuple[str, str]:
    mapDict = {}
    mapDict["not applicable"] = ("NCIT:C48660", "Not Applicable")
    mapDict["I"] = ("NCIT:C28077", "Grade 1")
    mapDict["II"] = ("NCIT:C28078", "Grade 2")
    mapDict["IIA"] = mapDict["II"] #("", "Grade 2a")
    mapDict["IIB"] = mapDict["II"] #("", "Grade 2b")
    mapDict["IIC"] = mapDict["II"] #("", "Grade 2c")
    mapDict["III"] = ("NCIT:C28079", "Grade 3")
    mapDict["IIIA"] = ("NCIT:C28076", "Grade 3a")
    mapDict["IIIB"] = ("NCIT:C28081", "Grade 3b")
    mapDict["IIIb"] = mapDict["IIIB"] # alias found in the XML
    mapDict["IIIC"] = mapDict["III"]  #("", "Grade 3c")
    
    if gradeStr not in mapDict:
        print(f"Warning: Unknown library source: {gradeStr}. No library source ontology code will be defined.")
        return ("",gradeStr)
    
    return mapDict[gradeStr]

def getOntologyCodeFromLabelPlatform(labelPlatform:str) -> str:
    label = labelPlatform.strip().lower()
    
    # build dictionary to map label to ontology code
    ontoDict = {} # key: label, value: ontology code
    ontoDict["illumina novaseq 6000"] = "OBI:0002630"
    
    if label not in ontoDict:
        return ""
    
    return ontoDict[label]
    
def getISO8601DurationFromAge(ageStr:str) -> str:
    return f"P{ageStr}Y"

def getOntologyCodeFromLabelLibSource(labelLibSource:str) -> tuple[str,str]:
    # all terms in:
    # www.ebi.ac.uk/ols/ontologies/genepio/terms?iri=http%3A%2F%2Fpurl.obolibrary.org%2Fobo%2FGENEPIO_0001965&lang=en&viewMode=All&siblings=false#
    label = labelLibSource.strip().lower()
    
    if label in ("genomic", "genomic source"):
        libSourceLabel = "genomic source"
        libSourceId = "GENEPIO:0001966"
    elif label in ("transcriptomic", "transcriptomic source"):
        libSourceLabel = "transcriptomic source"
        libSourceId = "GENEPIO:0001971"
    else:
        libSourceLabel = label
        libSourceId = ""
        print(f"Warning: Unknown library source: {label}. No library source ontology code will be defined.")
    
    return (libSourceId, libSourceLabel)

def getOntologyCodeFromLabelSex(labelSex:str) -> tuple[str,str]:
    label = labelSex.strip().lower()
    ontoDict = {}
    ontoDict['male'] = ('NCIT:C20197',"Male")
    ontoDict['female'] = ('NCIT:C16576', "Female")
    ontoDict['not collected'] = ("NCIT:C17998", "Unknown")
    ontoDict['unknown'] = ontoDict['not collected']
    
    if label not in ontoDict:
        print(f"Warning: Unknown sex/gender: {label}. No sex/gender ontology code will be defined.")
        return ("", label)
    
    return (ontoDict[label][0], ontoDict[label][1])