import evaluate
import numpy as np 

# noisy classification
clf_metrics=evaluate.combine(["accuracy", "f1", "precision", "recall"])

def NoisyComputeMetrics(eval_pred):
    predictions, labels=eval_pred
    predictions=np.argmax(predictions, axis=1)

    y_true=labels.tolist()
    y_pred=predictions.tolist()
    y_true=[['B-' + str(label)] for label in y_true]
    y_pred=[['B-' + str(label)] for label in y_pred]

    return clf_metrics.compute(predictions=predictions, references=labels)

################################################################################################

# token classification
seqeval = evaluate.load("seqeval")
from src.training.labels import ner_id2label, ner_label2id

def NerComputeMetrics(p):
    step_eval = 0
    predictions, labels = p
    predictions = np.argmax(predictions, axis=2)
    true_predictions = [
        [ner_id2label[p] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    true_labels = [
        [ner_id2label[l] for (p, l) in zip(prediction, label) if l != -100]
        for prediction, label in zip(predictions, labels)
    ]

    results = seqeval.compute(predictions=true_predictions, 
                              references=true_labels, 
                              zero_division=0.0)
    return {
        "precision": results["overall_precision"],
        "recall": results["overall_recall"],
        "f1": results["overall_f1"],
        "accuracy": results["overall_accuracy"],
    }