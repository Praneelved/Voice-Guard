import numpy as np
from sklearn.metrics import roc_curve, auc, precision_recall_fscore_support, confusion_matrix
from typing import Dict, Any, List

def compute_eer(y_true: np.ndarray, y_scores: np.ndarray):
    """
    Computes the Equal Error Rate (EER) and the corresponding threshold.
    EER is the point on the ROC curve where False Positive Rate (FPR) == False Negative Rate (FNR).
    y_true: 1 for spoof (positive class), 0 for genuine (negative class)
    """
    fpr, tpr, thresholds = roc_curve(y_true, y_scores, pos_label=1)
    fnr = 1 - tpr
    
    # Find the point where FPR and FNR are closest
    eer_index = np.nanargmin(np.absolute((fnr - fpr)))
    eer = fpr[eer_index]
    eer_threshold = thresholds[eer_index]
    
    return float(eer), float(eer_threshold)

def compute_metrics_at_threshold(y_true: np.ndarray, y_scores: np.ndarray, threshold: float) -> Dict[str, float]:
    """
    Computes standard metrics at a specific operating threshold.
    """
    y_pred = (y_scores >= threshold).astype(int)
    
    # Handle edge case where no positive or negative samples exist
    if len(np.unique(y_true)) < 2:
        return {}

    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='binary', pos_label=1, zero_division=0)
    
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    
    return {
        "threshold": float(threshold),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "fpr": float(fpr),
        "fnr": float(fnr)
    }

def evaluate_predictions(y_true: List[int], y_scores: List[float], custom_thresholds: List[float] = None) -> Dict[str, Any]:
    """
    Generates a full evaluation report from arrays of true labels and predicted scores.
    """
    y_true_np = np.array(y_true)
    y_scores_np = np.array(y_scores)
    
    if len(np.unique(y_true_np)) < 2:
        return {"error": "Dataset must contain both genuine and spoof samples."}
        
    eer, eer_threshold = compute_eer(y_true_np, y_scores_np)
    
    fpr, tpr, _ = roc_curve(y_true_np, y_scores_np, pos_label=1)
    roc_auc = auc(fpr, tpr)
    
    results = {
        "overall": {
            "eer": eer,
            "eer_threshold": eer_threshold,
            "roc_auc": float(roc_auc)
        },
        "operating_points": []
    }
    
    # Evaluate at EER threshold
    results["operating_points"].append(compute_metrics_at_threshold(y_true_np, y_scores_np, eer_threshold))
    
    # Evaluate at custom thresholds
    if custom_thresholds:
        for t in custom_thresholds:
            metrics = compute_metrics_at_threshold(y_true_np, y_scores_np, t)
            results["operating_points"].append(metrics)
            
    return results
