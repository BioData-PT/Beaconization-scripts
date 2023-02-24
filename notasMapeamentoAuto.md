# Mapeamento automatico

## Fica a faltar:
Biosamples:
- info.accession : Não existe no template, só no cineca. É derivavel facilmente do XML
- info.taxId: msm coisa

Cohorts:
- gender e age distribution: Distribuição de idades e generos, n tenho a certeza do formato

## notas do que meter (dinamico)
Analyses:
- id (igual ao biosampleId?)
- biosampleId
- runId

Biosamples:
- id (e.g. CR245_tumor_S1)
- inidividualId (e.g. CR245)
- tumorGrade (id + label)

Individuals:
- sex.id e label
- id
- age

Runs:
- id (e.g. SRR1334528)
- biosampleId
- individualId (e.g. CR245)
- runDate (e.g 2021-10-18)


## notas do que meter (estatico)
Analyses:
- tudo

Biosamples:
- biosampleStatus (id + label)
- id (e.g. CR228_tumor_S3)
- individualId (e.g. CR228)
- sampleOriginType (id + label)

Cohorts:
- collectionEvents_eventGenders.availability (TRUE)
- cohortType(study-defined)
- cohortSize ( len(individuals) )
- collectionEvents_eventAgeRange.availabilityCount ( igual cohortSize )
- collectionEvents_eventGenders.availability (TRUE)
- collectionEvents_eventGenders.availabilityCount ( igual cohortSize )
- id (stage_II/III_colorectal_cancer)

Datasets:
- Tudo

Individuals:
- diseases_diseaseCode.id e label (meter como está no excel)

Runs:
- tudo o resto q n tá no dinamico


