import os
import json
import pandas as pd
from typing import List, Dict, Any

class DataProcessor:
    def __init__(self, data_dir="./data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
    
    def process_product_data(self, data_source: str) -> List[Dict[str, Any]]:
        """
        Zpracuje surová produktová data do formátu vhodného pro indexaci
        
        Args:
            data_source: Cesta k souboru s produktovými daty (CSV, JSON, Excel)
            
        Returns:
            List dokumentů připravených pro vektorovou databázi
        """
        _, ext = os.path.splitext(data_source)
        
        if ext.lower() == '.json':
            return self._process_json(data_source)
        elif ext.lower() == '.csv':
            return self._process_csv(data_source)
        elif ext.lower() in ['.xlsx', '.xls']:
            return self._process_excel(data_source)
        else:
            raise ValueError(f"Nepodporovaný formát souboru: {ext}")
    
    def _process_json(self, file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return self._standardize_data(data)
    
    def _process_csv(self, file_path: str) -> List[Dict[str, Any]]:
        df = pd.read_csv(file_path)
        return self._standardize_data(df.to_dict('records'))
    
    def _process_excel(self, file_path: str) -> List[Dict[str, Any]]:
        df = pd.read_excel(file_path)
        return self._standardize_data(df.to_dict('records'))
    
    def _standardize_data(self, raw_data: List[Dict]) -> List[Dict[str, Any]]:
        """
        Standardizuje formát dat, aby byly konzistentní pro vektorovou databázi
        """
        standardized_data = []
        
        required_fields = ['id', 'name', 'description', 'category']
        
        for item in raw_data:
            # Kontrola požadovaných polí
            for field in required_fields:
                if field not in item:
                    print(f"Varování: Položka chybí povinné pole '{field}', přeskakuji.")
                    continue
            
            # Standardizace dokumentu
            doc = {
                'id': str(item['id']),
                'name': str(item['name']),
                'description': str(item['description']),
                'category': str(item['category']),
                'price': float(item.get('price', 0)),
                'brand': str(item.get('brand', '')),
                'availability': str(item.get('availability', 'Neznámá')),
                'features': item.get('features', [])
            }
            
            standardized_data.append(doc)
        
        return standardized_data
    
    def save_processed_data(self, data: List[Dict[str, Any]], output_file: str):
        """
        Uloží zpracovaná data do výstupního souboru
        """
        output_path = os.path.join(self.data_dir, output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Data byla úspěšně uložena do {output_path}")
