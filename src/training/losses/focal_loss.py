import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from torch import Tensor
from typing import Optional
import tensorflow as tf

class FocalLoss(nn.Module):
    """Focal Loss, as described in https://arxiv.org/abs/1708.02002.

    It is essentially an enhancement to cross entropy loss and is
    useful for classification tasks when there is a large class imbalance.
    x is expected to contain raw, unnormalized scores for each class.
    y is expected to contain class labels.

    Shape:
        - x: (batch_size, C) or (batch_size, C, d1, d2, ..., dK), K > 0.
        - y: (batch_size,) or (batch_size, d1, d2, ..., dK), K > 0.
    """

    def __init__(self, gamma=0.0, alpha=None, size_average=True):
        super(FocalLoss, self).__init__()
        try: 
            self.gamma=gamma[0] # fix tuple type
        except: 
            self.gamma = gamma # fix for use intrust focal loss case 
        self.alpha=alpha
        
        if isinstance(alpha, (float, int)):
            self.alpha=torch.Tensor([alpha, 1 - alpha])
        if isinstance(alpha, list):
            self.alpha=torch.Tensor(alpha)
        self.size_average=size_average

    def forward(self, input, target):

        if input.dim() > 2:
            input=input.view(input.size(0), input.size(1), -1)  # N,C,H,W => N,C,H*W
            input=input.transpose(1, 2)  # N,C,H*W => N,H*W,C
            input=input.contiguous().view(-1, input.size(2))  # N,H*W,C => N*H*W,C
        target=target.view(-1, 1)

        logpt=F.log_softmax(input)
        logpt=logpt.gather(1, target)
        logpt=logpt.view(-1)
        pt=Variable(logpt.data.exp())

        if self.alpha is not None:
            if self.alpha.type() !=input.data.type():
                self.alpha=self.alpha.type_as(input.data)
            at=self.alpha.gather(0, target.data.view(-1))
            logpt=logpt * Variable(at)
        
        loss=-1 * (1 - pt) ** self.gamma * logpt

        if self.size_average:
            return loss.mean()
        else:
            return loss.sum()

class NER_FocalLoss(nn.Module):
    """Focal Loss, as described in https://arxiv.org/abs/1708.02002.

    It is essentially an enhancement to cross entropy loss and is
    useful for classification tasks when there is a large class imbalance.
    x is expected to contain raw, unnormalized scores for each class.
    y is expected to contain class labels.

    Shape:
        - x: (batch_size, C) or (batch_size, C, d1, d2, ..., dK), K > 0.
        - y: (batch_size,) or (batch_size, d1, d2, ..., dK), K > 0.
    """

    def __init__(
        self,
        alpha: Optional[Tensor] = None,
        gamma: float = 0.0,
        reduction: str = "mean",
        ignore_index: int = -100,
    ):
        if reduction not in ("mean", "sum", "none"):
            raise ValueError('Reduction must be one of: "mean", "sum", "none".')

        super().__init__()
        self.alpha = torch.FloatTensor(alpha).to("cuda")
        self.gamma = gamma[0]
        self.ignore_index = ignore_index
        self.reduction = reduction

        self.nll_loss = nn.NLLLoss(weight=self.alpha, 
                                   reduction="none", 
                                   ignore_index=self.ignore_index)

    def __repr__(self):
        arg_keys = ["alpha", "gamma", "ignore_index", "reduction"]
        arg_vals = [self.__dict__[k] for k in arg_keys]
        arg_strs = [f"{k}={v!r}" for k, v in zip(arg_keys, arg_vals)]
        arg_str = ", ".join(arg_strs)
        return f"{type(self).__name__}({arg_str})"

    def forward(self, x: Tensor, y: Tensor) -> Tensor:
        if x.ndim > 2:
            c = x.shape[1]
            # x = x.permute(0, *range(2, x.ndim), 1).reshape(-1, c)
            y = y.view(-1)
            x = x.view([y.shape[0], 25])

        unignored_mask = y != self.ignore_index
        y = y[unignored_mask]
        
        if len(y) == 0:
            return torch.tensor(0.0)
        
        x = x[unignored_mask]
        log_p = F.log_softmax(x, dim=-1)
        ce = self.nll_loss(log_p, y)

        all_rows = torch.arange(len(x))
        log_pt = log_p[all_rows, y]

        pt = log_pt.exp()
        focal_term = (1 - pt) ** self.gamma

        loss = focal_term * ce

        if self.reduction == "mean":
            loss = loss.mean()
        elif self.reduction == "sum":
            loss = loss.sum()

        return loss
