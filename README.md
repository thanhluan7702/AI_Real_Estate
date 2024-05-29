### Description: 
Collect data from online platforms using Selenium and Beautifulsoup packages. The data is stored on a PostgreSQL database with 3 raw tables followed by ETL and saving the cleaned data to the fact table.

Use text data to analyze buyer and seller pain points, then analyze valuable information. After building extract information module with combined rule-base and model-base. Process improvement with noise adaptation and entity resolver module for normalize value

Link: [alonhadat](https://alonhadat.com.vn/?ads=1&gad_source=1&gclid=Cj0KCQjwpNuyBhCuARIsANJqL9Mwgez9UZefZKjoQZBiHdT85P7P09sAiWDaihkqA8dQcUbgXs6UHGsaAiM2EALw_wcB), [nhatot](https://www.nhatot.com/), [batdongsan](https://batdongsan.com.vn/)

### Opensouce: 
Programing language: Python=3.9 and libraries such as: numpy, pandas, ...\
Database: PostgreSQL \
Scraping: Selenium, Beautifulsoup \
BI Tool: PowerBI \
Labeling tool: [Doccano](https://github.com/doccano/doccano)\
Architecture: Transformers (Phobert: [Github](https://github.com/VinAIResearch/PhoBERT), [Paper](https://aclanthology.org/2020.findings-emnlp.92/)) \
Evaluation metrics: sklearn, seqeval

### Structure: 
```
crawling_bot: contains code that collects real estate platform data
data:
    source: contains the txt file for the backup process
        alonhadat
        batdongsan
        nhatot
    convert_doccano_to_csv.py: support convert doccano format to csv format
rules:
    patterns: contains patterns for extracting information module with a rule base
    entity_resolver.py: normalize value after extract for both approaches
    load_yaml.py: support load all yaml file 
src: main source code 
    inference
    training
web: deploy webap
data_augmentation.py: module support generate new data
postgresql_module.py: function support interactive with DB
```
### Script

#### 1. Training Script
```
python src/training/noise_filtering/train.py --bs 32 --epochs 10 --lr 2e-4 --device 0 --trainer focal_loss --label_smoothing 0.0 --aug
```

```
python src/training/ner/train.py --bs 32 --epochs 10 --lr 2e-5 --device 0 --trainer base --label_smoothing 0.0
```

* trainer type: method for training process: base (default), focal_loss, dice_loss, aug (data_augmentation), intrust_loss, intrust_focal_loss

#### 2. Inference Script
```
python src/inference/noise_filtering/inference.py
```
```
python src/inference/ner/inference.py
```

#### 3. Deploy webapp
```
python web/app.py
```