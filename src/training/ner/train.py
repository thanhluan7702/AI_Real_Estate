import os
import argparse 
import torch
import evaluate
import numpy as np 
import seaborn as sns
import matplotlib.pyplot as plt
from seqeval.metrics import classification_report
from sklearn.metrics import confusion_matrix
from transformers import (AutoConfig, 
                          AutoTokenizer, 
                          AutoModelForTokenClassification,
                          set_seed)

from src.training.labels import ner_label2id, ner_id2label
from src.training.dataloader import NerLoader
from src.training.datacollator import DataCollator
from src.training.metrics import NerComputeMetrics
from src.training.training_argument import training_args
from src.training.my_trainer import get_trainer_class

import warnings
warnings.filterwarnings('ignore')

set_seed(42)

seqeval = evaluate.load("seqeval")

parser = argparse.ArgumentParser(description='training_params')
parser.add_argument(
    '--pretrain_model', 
    type = str,
    default = 'vinai/phobert-base-v2', 
    help = "Pretrained model" 
)

parser.add_argument(
    '--output_dir', 
    type = str,
    default = 'ner', 
    help = "Save model path" 
)

parser.add_argument(
    '--bs', 
    type = int,
    default = 8, 
    help = "Batch size" 
)

parser.add_argument(
    '--epochs', 
    type = int,
    default = 5, 
    help = "Epochs" 
)

parser.add_argument(
    '--lr', 
    type = float,
    default = 2e-4, 
    help = "Learning rate" 
)

parser.add_argument(
    '--label_smoothing', 
    type = float,
    default = 0.0, 
    help = "Label smoothing" 
)

parser.add_argument(
    '--num_classes', 
    type = int,
    default = 25, 
    help = "Number of class" 
)

parser.add_argument(
    '--max_len', 
    type = int,
    default = 256, 
    help = "Max length of sequence" 
)

parser.add_argument(
    '--device', 
    type = str,
    default = '0', 
    help = "Device" 
)

parser.add_argument(
    '--trainer', 
    type = str,
    default = 'base', 
    help = "Trainer type" 
)

args = parser.parse_args()

os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"]=args.device
os.environ["CUDA_LAUNCH_BLOCKING"]="1"

class NERTraining:
    def __init__(self):
        self.pretrain = args.pretrain_model 
        self.max_length = args.max_len
        
        # init model 
        self.tokenizer, self.model, self.config = self._load_model()
        
    def _load_model(self): 
        tokenizer=AutoTokenizer.from_pretrained(self.pretrain, 
                                          max_length=self.max_length)
        
        model=AutoModelForTokenClassification.from_pretrained(self.pretrain, 
                                                                num_labels=len(ner_id2label),
                                                                id2label=ner_id2label, 
                                                                label2id=ner_label2id, 
                                                                ignore_mismatched_sizes=True)

        config=AutoConfig.from_pretrained(self.pretrain)

        return tokenizer, model, config
    
    def fit_eval(self): 
        # prepare data 
        dataset = NerLoader(tokenizer=self.tokenizer,
                            task = 'ner').build_dataset()
        dataset.set_format('torch', columns=['input_ids', 'attention_mask', 'labels'])
        data_collator=DataCollator(tokenizer=self.tokenizer).ner_collator()

        # calculate class_weigth for focal_loss base
        if args.trainer in ('focal_loss', 'intrust_focal_loss'): 
            import pandas as pd 
            data = pd.read_csv('src/training/ner/dataset/train_dataset.csv')   
            labels = list(data.label.values)

            class_weight = {} 
            count = 0 
            for label in labels: 
                for l in label.split(): 
                    if l not in class_weight: 
                        class_weight[l] = 1 
                    else: 
                        class_weight[l] += 1 
                    count += 1 

            for tag, num in class_weight.items():
                class_weight[tag] = 1/(num/count)    
            class_weight = list(dict(sorted(class_weight.items())).values())
           
            # move Other from last to first
            cp = class_weight
            class_weight = []
            class_weight.append(cp[0])
            class_weight += cp[0:-1]
        else: 
            class_weight = None
            
        trainer = get_trainer_class( 
                            trainer_type=args.trainer, 
                            smooth = args.label_smoothing,
                            num_classes = args.num_classes,
                            alpha = class_weight,
                            task = 'ner'
                            )
        
        training_argument = training_args( output_dir=args.output_dir,
                                            smoothing=args.label_smoothing, 
                                            lr=args.lr,
                                            epochs = args.epochs,
                                            bs = args.bs)
        
        trainer= trainer(model=self.model,
                        args=training_argument,
                        train_dataset=dataset['train'],
                        eval_dataset=dataset['valid'],
                        tokenizer=self.tokenizer,
                        data_collator=data_collator,
                        compute_metrics=NerComputeMetrics 
                    )
        trainer.train() # training process
        if args.label_smoothing: 
            trainer.save_model("src/training/" + args.output_dir + '/best_models/' + args.trainer + '_smooth/')
        else: 
            trainer.save_model("src/training/" + args.output_dir + '/best_models/' + args.trainer + '/')
        # evaluation
        print(trainer.evaluate(dataset["test"]))
        predictions, labels, _ = trainer.predict(dataset["test"])
        predictions = np.argmax(predictions, axis=2)

        # Remove ignored index (special tokens)
        true_predictions = [
            [ner_id2label[p] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        true_labels = [
            [ner_id2label[l] for (p, l) in zip(prediction, label) if l != -100]
            for prediction, label in zip(predictions, labels)
        ]
        
        report = classification_report(true_labels, true_predictions, mode='macro')
        print(report)
        
        cm = confusion_matrix(y_true = [l for label in true_labels for l in label],
                              y_pred = [l for label in true_predictions for l in label])
        
        all_labels = list(ner_label2id.keys()) 
        
        plt.figure(figsize=(12, 9))
        sns.heatmap(cm, annot=True, fmt="d", xticklabels=all_labels, yticklabels=all_labels)
        plt.xlabel("Predicted")
        plt.ylabel("Actual")
        plt.title("Confusion Matrix")
        
        if args.label_smoothing: 
            file_path = f'src/training/ner/confusion_matrix/{args.trainer}_smooth.png'
        else:
            file_path = f'src/training/ner/confusion_matrix/{args.trainer}.png'
        plt.savefig(file_path)
        
        # Write the report to the file
        if args.label_smoothing: 
            file_path = f'src/training/ner/report/{args.trainer}_smooth.txt'
        else:
            file_path = f'src/training/ner/report/{args.trainer}.txt'
            
        with open(file_path, 'w') as file:
            import json
            file.write(report)
            
if __name__ == "__main__": 
    NERTraining().fit_eval()