import json
import os

def combine_anystyle_output():
    raw_output_dir = "info/raw_anystyle_output"
    combined_output_file = "info/anystyle-report-full.json"
    
    all_refs = []
    for filename in os.listdir(raw_output_dir):
        if filename.endswith(".json"):
            filepath = os.path.join(raw_output_dir, filename)
            if os.path.getsize(filepath) > 0:
                with open(filepath, 'r') as f:
                    try:
                        data = json.load(f)
                        all_refs.extend(data)
                    except json.JSONDecodeError:
                        print(f"Warning: Could not decode JSON from {filepath}")
            
    with open(combined_output_file, 'w') as f:
        json.dump(all_refs, f, indent=2)

if __name__ == "__main__":
    combine_anystyle_output()
