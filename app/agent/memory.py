import json
import os

class PreferenceManager:
    def __init__(self, file_path="data/preferences.json"):
        self.file_path = file_path
        
        # Ensure the data directory exists
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        
        # Create default preferences file if it doesn't exist
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                json.dump({"global_rules": []}, f, indent=4)
                
    def get_rules(self) -> list:
        try:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
                return data.get("global_rules", [])
        except Exception:
            return []
            
    def add_rule(self, rule: str):
        rules = self.get_rules()
        if rule not in rules:
            rules.append(rule)
            with open(self.file_path, 'w') as f:
                json.dump({"global_rules": rules}, f, indent=4)
