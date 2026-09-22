import argparse
import os
import json
import logging
from typing import Dict, Any

from evaluation.dataset import load_dataset, EvaluationDataset
from evaluation.transforms import simulate_telephony, simulate_noisy_telephony
from evaluation.metrics import evaluate_predictions
from services.audio.preprocessing import AudioPreprocessor
from services.risk.models.antispoof import AntispoofModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def evaluate_condition(dataset: EvaluationDataset, condition_name: str, model: AntispoofModel) -> Dict[str, Any]:
    logger.info(f"--- Evaluating Condition: {condition_name.upper()} ---")
    
    y_true = []
    y_scores = []
    
    preprocessor = AudioPreprocessor(target_sr=16000)
    
    for idx, item in enumerate(dataset.data):
        filepath = item["filepath"]
        if not os.path.exists(filepath):
            logger.warning(f"File missing: {filepath}")
            continue
            
        try:
            # 1. Load Audio
            audio_array = preprocessor.load_audio(filepath)
            
            # 2. Apply transformations based on condition
            if condition_name == "telephony":
                audio_array = simulate_telephony(audio_array)
            elif condition_name == "noisy_telephony":
                audio_array = simulate_noisy_telephony(audio_array)
                
            # 3. Model Inference
            # AASIST requires 64000 samples (4 seconds at 16kHz)
            if len(audio_array) > 64000:
                audio_array = audio_array[:64000]
            elif len(audio_array) < 64000:
                import numpy as np
                audio_array = np.pad(audio_array, (0, 64000 - len(audio_array)))
                
            score = model.predict(audio_array)
            
            y_true.append(item["is_spoof"])
            y_scores.append(float(score))
            
            if (idx + 1) % 100 == 0:
                logger.info(f"Processed {idx + 1}/{len(dataset.data)} samples...")
                
        except Exception as e:
            logger.error(f"Error processing {filepath}: {e}")
            
    # Calculate metrics
    # Let's test standard operational thresholds: 0.5 (balanced), 0.75 (high confidence), 0.9 (extreme)
    metrics = evaluate_predictions(y_true, y_scores, custom_thresholds=[0.5, 0.75, 0.9])
    
    return metrics


def run_evaluation(metadata_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("Initializing Evaluation Framework...")
    dataset = load_dataset(metadata_path)
    
    logger.info(f"Loaded {len(dataset)} total samples.")
    
    # 1. Strict evaluation separation
    test_set = dataset.filter_by_split("test")
    logger.info(f"Filtered down to {len(test_set)} 'test' split samples.")
    
    if len(test_set) == 0:
        logger.error("No 'test' samples found. Aborting.")
        return
        
    # Initialize Model (Loads AASIST or specific implementation)
    model = AntispoofModel()
    
    results = {
        "metadata_source": metadata_path,
        "total_test_samples": len(test_set),
        "conditions": {}
    }
    
    conditions = ["clean", "telephony", "noisy_telephony"]
    
    for condition in conditions:
        cond_metrics = evaluate_condition(test_set, condition, model)
        results["conditions"][condition] = cond_metrics
        logger.info(f"Condition {condition} EER: {cond_metrics.get('overall', {}).get('eer', 'N/A')}")
        
    # Analyze by language/accent if available
    languages = test_set.get_groups("language")
    if len(languages) > 1:
        results["demographics"] = {"language": {}}
        logger.info("Evaluating across language categories...")
        for lang, lang_dataset in languages.items():
            if len(lang_dataset) > 10: # ensure minimum sample size
                lang_metrics = evaluate_condition(lang_dataset, "telephony", model)
                results["demographics"]["language"][lang] = lang_metrics
                
    # Save results
    output_path = os.path.join(output_dir, "results.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=4)
        
    logger.info(f"Evaluation complete. Results saved to {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="VoiceGuard AntiSpoof Evaluation Harness")
    parser.add_argument("--metadata", required=True, help="Path to dataset metadata CSV/JSONL")
    parser.add_argument("--out", default="evaluation/results", help="Output directory for results")
    
    args = parser.parse_args()
    
    run_evaluation(args.metadata, args.out)
