import os
import argparse 
import torch
import evaluate
import numpy as np 
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (classification_report,
                            confusion_matrix)
from transformers import (AutoConfig, 
                          AutoTokenizer, 
                          AutoModelForSequenceClassification,
                          set_seed)

from src.training.labels import noisy_label2id, noisy_id2label
from src.training.dataloader import SeqLoader
from src.training.datacollator import DataCollator
from src.training.metrics import NoisyComputeMetrics
from src.training.training_argument import training_args
from src.training.my_trainer import get_trainer_class

import warnings
warnings.filterwarnings('ignore')

set_seed(42)

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
    default = 'noise_filtering', 
    help = "Save model path" 
)

parser.add_argument(
    '--trainer', 
    type = str,
    default = 'base', 
    help = "Trainer type" 
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
    default = 2e-5, 
    help = "Learning rate" 
)

parser.add_argument(
    '--label_smoothing', 
    type = float,
    default = 0.0, 
    help = "Label smoothing" 
)

parser.add_argument(
    '--gamma', 
    type = float,
    default = 1.1, 
    help = "Gamma param" 
)

parser.add_argument(
    '--delta', 
    type = float,
    default = 0.5, 
    help = "Delta param" 
)

parser.add_argument(
    '--num_classes', 
    type = int,
    default = 2, 
    help = "Number of class" 
)

parser.add_argument(
    '--max_len', 
    type = int,
    default = 256, 
    help = "Max length of sequence" 
)

parser.add_argument(
    '--alpha_loss', 
    type = float,
    default = 0.4, 
    help = "Intrust/Dice alpha param" 
)

parser.add_argument(
    '--device', 
    type = str,
    default = '0', 
    help = "Device" 
)

parser.add_argument(
    "--aug", 
    type=bool,
    default = False,
    help = 'Use data augment function')

args = parser.parse_args()

os.environ["CUDA_DEVICE_ORDER"]="PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"]=args.device
os.environ["CUDA_LAUNCH_BLOCKING"]="1"

class NoisyTraining:
    def __init__(self):
        self.pretrain = args.pretrain_model 
        self.max_length = args.max_len
        
        # init model 
        self.tokenizer, self.model, self.config = self._load_model()
        
    def _load_model(self): 
        tokenizer=AutoTokenizer.from_pretrained(self.pretrain, 
                                          max_length=self.max_length,
                                          padding='max_length',
                                          truncation=True)

        model=AutoModelForSequenceClassification.from_pretrained(self.pretrain, 
                                                                num_labels=len(noisy_label2id),
                                                                id2label=noisy_id2label, 
                                                                label2id=noisy_label2id, 
                                                                ignore_mismatched_sizes=True)

        config=AutoConfig.from_pretrained(self.pretrain)
        
        return tokenizer, model, config
    
    def fit_eval(self): 
        # prepare data 
        dataset = SeqLoader(tokenizer=self.tokenizer,
                            task = 'noise_filtering',
                            aug = args.aug).build_dataset()
        data_collator=DataCollator(tokenizer=self.tokenizer).collator()
        
        # calculate class_weight for focal_loss base
        if args.trainer in ('focal_loss', 'intrust_focal_loss'): 
            import pandas as pd 
            data = pd.read_csv('src/training/noise_filtering/dataset/train_dataset.csv')
            data['label'] = data['label'].apply(lambda x: noisy_label2id[x])
            data.sort_values(by = ['label'], inplace = True)
            values_count = data['label'].value_counts().to_dict()
            class_weight = {}

            for k, v in values_count.items(): 
                class_weight[k] = 1 / (v / data.shape[0])
            class_weight = list(class_weight.values())
        else:
            class_weight = None 
            
        # define trainer
        trainer = get_trainer_class(
                            trainer_type=args.trainer, 
                            gamma = args.gamma, 
                            alpha = class_weight,
                            smooth = args.label_smoothing,
                            delta = args.delta,
                            num_classes = args.num_classes,
                            intrust_alpha = args.alpha_loss, 
                            task = 'noisy'
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
                        compute_metrics=NoisyComputeMetrics 
                    )
        trainer.train() # training process
        if args.label_smoothing: 
            trainer.save_model("src/training/" + args.output_dir + '/best_models/' + args.trainer + '_smooth/')
        elif args.aug: 
            trainer.save_model("src/training/" + args.output_dir + '/best_models/' + args.trainer + '_aug/')
        else: 
            trainer.save_model("src/training/" + args.output_dir + '/best_models/' + args.trainer + '/')
        # evaluation
        print(trainer.evaluate(dataset["test"]))
        y_pred=trainer.predict(dataset["test"]).predictions.argmax(axis=1)
        y_true=dataset["test"]["label"]
        report=classification_report(y_true, y_pred, target_names=['normal', 'noisy'])
        print(report)
        
        cm = confusion_matrix(y_true = y_true,
                              y_pred = y_pred)
        
        all_labels = ['normal', 'noisy']
        
        plt.figure(figsize=(12, 9))
        sns.heatmap(cm, annot=True, fmt="d", xticklabels=all_labels, yticklabels=all_labels)
        plt.xlabel("Predicted")
        plt.ylabel("Actual")
        plt.title("Confusion Matrix")
        
        if args.label_smoothing: 
            file_path = f'src/training/noise_filtering/confusion_matrix/{args.trainer}_smooth.png'
        elif args.aug: 
            file_path = f'src/training/noise_filtering/confusion_matrix/{args.trainer}_aug.png'
        else:
            file_path = f'src/training/noise_filtering/confusion_matrix/{args.trainer}.png'
        plt.savefig(file_path)
        
        # Write the report to the file
        if args.label_smoothing: 
            file_path = f'src/training/noise_filtering/report/{args.trainer}_smooth.txt'
        elif args.aug: 
            file_path = f'src/training/noise_filtering/report/{args.trainer}_aug.txt'
        else:
            file_path = f'src/training/noise_filtering/report/{args.trainer}.txt'
            
        with open(file_path, 'w') as file:
            file.write(report)
            
if __name__ == "__main__": 
    NoisyTraining().fit_eval()