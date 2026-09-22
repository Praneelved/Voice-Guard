import csv
import json
import os
from typing import List, Dict, Any

class EvaluationDataset:
    def __init__(self, data: List[Dict[str, Any]]):
        self.data = data
        
    def __len__(self):
        return len(self.data)
        
    def filter_by_split(self, split: str):
        """
        Filters dataset by split (e.g., 'train', 'dev', 'test').
        Enforces strict evaluation boundaries.
        """
        filtered = [item for item in self.data if item.get("split", "test") == split]
        return EvaluationDataset(filtered)
        
    def filter_by_language(self, language: str):
        filtered = [item for item in self.data if item.get("language") == language]
        return EvaluationDataset(filtered)
        
    def get_groups(self, key: str) -> Dict[str, 'EvaluationDataset']:
        """Groups dataset by a specific metadata key (e.g. 'language')."""
        groups = {}
        for item in self.data:
            val = item.get(key, "unknown")
            if val not in groups:
                groups[val] = []
            groups[val].append(item)
            
        return {k: EvaluationDataset(v) for k, v in groups.items()}

def load_dataset(metadata_path: str) -> EvaluationDataset:
    """
    Loads dataset metadata.
    Supported formats: CSV, JSONL
    
    Expected minimum schema:
    - filepath: path to audio file
    - label: "spoof" or "genuine"
    - split: "train", "dev", or "test" (default "test")
    """
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
        
    data = []
    ext = os.path.splitext(metadata_path)[1].lower()
    
    if ext == ".csv":
        with open(metadata_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append(row)
    elif ext in [".jsonl", ".json"]:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
    else:
        raise ValueError(f"Unsupported metadata format: {ext}. Use .csv or .jsonl")
        
    # Validate minimum schema
    for idx, item in enumerate(data):
        if "filepath" not in item:
            raise ValueError(f"Missing 'filepath' in row {idx}")
        if "label" not in item:
            raise ValueError(f"Missing 'label' in row {idx}")
            
        # Normalize labels
        lbl = item["label"].lower().strip()
        if lbl in ["1", "spoof", "fake", "synthetic"]:
            item["is_spoof"] = 1
        elif lbl in ["0", "genuine", "real", "human", "bonafide"]:
            item["is_spoof"] = 0
        else:
            raise ValueError(f"Unknown label format: {lbl} in row {idx}")
            
    return EvaluationDataset(data)
