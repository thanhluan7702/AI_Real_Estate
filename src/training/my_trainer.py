from transformers import Trainer
from src.training.losses.focal_loss import FocalLoss, NER_FocalLoss
from src.training.losses.dice_loss import DiceLoss
from src.training.losses.intrust_loss import IntrustLoss
from src.training.losses.intrust_focal_loss import IntrustFocalLoss

### define a custom trainer for each loss function

def get_focal_loss_trainer(task, **kwargs):
    gamma=kwargs.get('gamma', 1.1),
    alpha=kwargs.get('alpha', [0.8, 2.2])
    class FocalLossTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False):
            labels=inputs.pop("labels")
            outputs=model(**inputs)
            logits=outputs[0]
            if task == 'noisy':
                loss=FocalLoss(gamma=gamma,
                               alpha=alpha)(logits, labels)
            else: 
                loss=NER_FocalLoss(gamma = gamma, 
                                   alpha = alpha)(logits, labels)
                
            return (loss, outputs) if return_outputs else loss
    return FocalLossTrainer

def get_dice_loss_trainer(task, **kwargs): 
    alpha=kwargs.get('intrust_alpha', 0.0)
    smooth=kwargs.get('smooth', 1e-4)
    if smooth == 0.0: 
        smooth = 1e-4
        
    class DiceLossTrainer(Trainer): 
        def compute_loss(self, model, inputs, return_outputs=False): 
            labels=inputs.pop("labels")
            outputs=model(**inputs)
            logits=outputs[0]   
            loss=DiceLoss(alpha=alpha,
                        smooth=smooth)(logits, labels)
            return (loss, outputs) if return_outputs else loss
    return DiceLossTrainer

def get_intrust_loss_trainer(task, **kwargs): 
    num_classes=kwargs.pop('num_classes', 2)
    alpha=kwargs.pop('intrust_alpha', 0.4)
    delta = kwargs.pop('delta', 0.5)
    class IntrustLossTrainer(Trainer): 
        def compute_loss(self, model, inputs, return_outputs=False): 
            labels=inputs.pop("labels")
            outputs=model(**inputs)
            logits=outputs[0]
            loss=IntrustLoss(num_classes=num_classes,
                               alpha=alpha,
                               delta = delta)(logits, labels)
            return (loss, outputs) if return_outputs else loss
    return IntrustLossTrainer

def get_intrust_focal_loss_trainer(task, **kwargs): 
    num_classes=kwargs.pop('num_classes', 2)
    alpha=kwargs.pop('intrust_alpha', 0.4)
    delta = kwargs.pop('delta', 0.5)
    class_weight = kwargs.pop('alpha', [0.8, 2.2])
    
    class IntrustFocalLossTrainer(Trainer): 
        def compute_loss(self, model, inputs, return_outputs=False): 
            labels=inputs.pop("labels")
            outputs=model(**inputs)
            logits=outputs[0]
            loss=IntrustFocalLoss(num_classes=num_classes,
                               alpha=alpha,
                               delta = delta,
                               class_weight = class_weight)(logits, labels)
            return (loss, outputs) if return_outputs else loss
    return IntrustFocalLossTrainer

### get trainer with demand
def get_trainer_class(trainer_type=None, task = None, **kwargs):
    if trainer_type == "focal_loss":
        return get_focal_loss_trainer(task, **kwargs)
    elif trainer_type == 'dice_loss': 
        return get_dice_loss_trainer(task, **kwargs)
    elif trainer_type == 'intrust_loss': 
        return get_intrust_loss_trainer(task, **kwargs)
    elif trainer_type == 'intrust_focal_loss': 
        return get_intrust_focal_loss_trainer(task, **kwargs)
    # add more trainer class here
    return Trainer