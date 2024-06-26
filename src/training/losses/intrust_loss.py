import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from torch import Tensor
from typing import Optional

class IntrustLoss(nn.Module):
    def __init__(self, alpha=0.4, delta=0.5, num_classes=2):
        super().__init__()
        self.alpha=alpha
        self.beta=1 - self.alpha
        self.num_classes=num_classes
        self.delta=delta
        self.cross_entropy=torch.nn.CrossEntropyLoss()
        # self.crf=CRF(num_tags=num_classes, batch_first=True)

    def forward(self, logits, labels):
        # loss_mask=labels.gt(0)
        # Loss CRF 

        ce=self.cross_entropy(logits, labels)
        # Loss In_trust
        active_logits=logits.view(-1, self.num_classes)
        active_labels=labels.view(-1)

        pred=F.softmax(active_logits, dim=1)
        pred=torch.clamp(pred, min=1e-7, max=1.0)
        label_one_hot=torch.nn.functional.one_hot(
            active_labels, self.num_classes
        ).float()
        label_one_hot=torch.clamp(label_one_hot, min=1e-4, max=1.0)
        dce=-1 * torch.sum(
            pred * torch.log(pred * self.delta + label_one_hot * (1 - self.delta)),
            dim=1,
        )

        # Loss

        loss=self.alpha * ce - self.beta * dce.mean()
        return loss