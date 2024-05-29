import torch
from torch import Tensor, nn
from torch.nn import functional as F
from typing import Optional

from src.training.losses.focal_loss import FocalLoss

class IntrustFocalLoss(nn.Module):
    def __init__(
        self,
        alpha=0.6,
        delta=0.5,
        num_classes=21,
        class_weight: Optional[Tensor] = None,
        gamma: float = 0.0,
    ):
        super().__init__()
        self.alpha = alpha
        self.beta = 1 - self.alpha
        self.num_classes = num_classes
        self.delta = delta
        self.cross_entropy = torch.nn.CrossEntropyLoss()

        self.class_weight = class_weight
        self.gamma = gamma

        self.focal = FocalLoss(alpha=class_weight, gamma=gamma)

    def forward(self, logits, labels):
        # loss_mask = labels.gt(0)
        # Loss CRF
        # ce = self.cross_entropy(logits,labels)
        ce = self.focal(logits, labels)
        # Loss In_trust
        active_logits = logits.view(-1, self.num_classes)
        active_labels = labels.view(-1)

        pred = F.softmax(active_logits, dim=1)
        pred = torch.clamp(pred, min=1e-7, max=1.0)
        label_one_hot = torch.nn.functional.one_hot(active_labels, self.num_classes).float()
        label_one_hot = torch.clamp(label_one_hot, min=1e-4, max=1.0)
        dce = -1 * torch.sum(
            pred * torch.log(pred * self.delta + label_one_hot * (1 - self.delta)),
            dim=1,
        )

        # Loss

        loss = self.alpha * ce - self.beta * dce.mean()
        return loss