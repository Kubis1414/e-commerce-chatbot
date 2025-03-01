import os
import json
import numpy as np
from typing import List, Dict
import faiss
from sentence_transformers import SentenceTransformer
import pickle

class VectorDBManager:
    def __init__(self, db_path="./data/vector_db"):
        self.db_path = db_path
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.index = None
        self.documents = []
        
        # Vytvoření adresáře pro databázi, pokud neexistuje
        os.makedirs(db_path, exist_ok=True)
        
        # Načtení indexu a dokumentů, pokud existují
        self._load_db()
        
        # Pokud databáze neexistuje, vytvořit ji
        if self.index is None:
            self._create_db()

    def _load_db(self):
        index_path = os.path.join(self.db_path, "faiss_index.bin")
        docs_path = os.path.join(self.db_path, "documents.pkl")
        
        if os.path.exists(index_path) and os.path.exists(docs_path):
            try:
                self.index = faiss.read_index(index_path)
                with open(docs_path, 'rb') as f:
                    self.documents = pickle.load(f)
                return True
            except Exception as e:
                print(f"Chyba při načítání databáze: {e}")
        
        return False

    def _create_db(self):
        # Načtení ukázkových dat
        data_path = os.path.join("data", "product_data.json")
        
        # Pokud ukázková data neexistují, vytvořit je
        if not os.path.exists(data_path):
            self._create_sample_data(data_path)
        
        # Načtení dat
        with open(data_path, 'r', encoding='utf-8') as f:
            products = json.load(f)
        
        # Příprava dokumentů pro indexování
        texts = []
        for product in products:
            text = f"{product['name']} {product['description']} {product['category']} {product.get('brand', '')}"
            texts.append(text)
            self.documents.append(product)
        
        # Vytvoření FAISS indexu
        embeddings = self.model.encode(texts)
        dimension = embeddings.shape[1]
        
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(np.array(embeddings).astype('float32'))
        
        # Uložení indexu a dokumentů
        self._save_db()

    def _save_db(self):
        index_path = os.path.join(self.db_path, "faiss_index.bin")
        docs_path = os.path.join(self.db_path, "documents.pkl")
        
        faiss.write_index(self.index, index_path)
        with open(docs_path, 'wb') as f:
            pickle.dump(self.documents, f)

    def _create_sample_data(self, data_path):
        # Vytvoření ukázkových dat pro produkty
        sample_products = [
            {
                "id": "p001",
                "name": "Smartphone Galaxy S21",
                "brand": "Samsung",
                "category": "Elektronika > Mobilní telefony",
                "description": "Vlajkový smartphone s 6,2palcovým displejem, 8GB RAM, 128GB úložištěm a 64Mpx fotoaparátem.",
                "price": 19990,
                "availability": "Skladem",
                "features": ["5G", "vodotěsný", "bezdrátové nabíjení"]
            },
            {
                "id": "p002",
                "name": "iPhone 13 Pro",
                "brand": "Apple",
                "category": "Elektronika > Mobilní telefony",
                "description": "Prémiový smartphone s A15 Bionic čipsetem, Super Retina XDR displejem a profesionálním fotoaparátem.",
                "price": 28990,
                "availability": "Na objednávku",
                "features": ["5G", "Face ID", "MagSafe"]
            },
            # Přidání dalších ukázkových produktů...
            {
                "id": "p003",
                "name": "ThinkPad X1 Carbon",
                "brand": "Lenovo",
                "category": "Elektronika > Notebooky",
                "description": "Ultratenký a lehký business notebook s procesorem Intel Core i7, 16GB RAM a 512GB SSD.",
                "price": 34990,
                "availability": "Skladem",
                "features": ["Podsvícená klávesnice", "Čtečka otisků prstů", "14 palců"]
            },
            {
                "id": "p004",
                "name": "Automatická pračka WW90T534DAW",
                "brand": "Samsung",
                "category": "Domácí spotřebiče > Pračky",
                "description": "Úsporná pračka s předním plněním, kapacitou 9 kg a funkcí parního praní.",
                "price": 12990,
                "availability": "Skladem",
                "features": ["A+++ energetická třída", "1400 ot/min", "Eco Bubble technologie"]
            },
            {
                "id": "p005",
                "name": "Herní sluchátka Kraken V3",
                "brand": "Razer",
                "category": "Elektronika > Příslušenství > Sluchátka",
                "description": "Pohodlná herní sluchátka s prostorovým zvukem 7.1 a RGB podsvícením.",
                "price": 2490,
                "availability": "Skladem",
                "features": ["Mikrofon s potlačením šumu", "50mm měniče", "THX prostorový zvuk"]
            }
        ]
        
        # Vytvoření adresáře, pokud neexistuje
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        
        # Uložení ukázkových dat
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(sample_products, f, ensure_ascii=False, indent=2)

    def search(self, query, top_k=50):
        """
        Vyhledání relevantních dokumentů podle dotazu
        """
        # Převod dotazu na vektor
        query_vector = self.model.encode([query])
        
        # Vyhledání nejbližších vektorů
        distances, indices = self.index.search(np.array(query_vector).astype('float32'), top_k)
        
        # Získání odpovídajících dokumentů
        results = []
        for idx in indices[0]:
            if idx < len(self.documents):
                results.append(self.documents[idx])
        
        return results

    def add_document(self, document):
        """
        Přidání nového dokumentu do vektorové databáze
        """
        # Příprava textu pro vektor
        text = f"{document['name']} {document['description']} {document['category']} {document.get('brand', '')}"
        
        # Převod na vektor
        embedding = self.model.encode([text])
        
        # Přidání do indexu
        self.index.add(np.array(embedding).astype('float32'))
        
        # Přidání dokumentu do seznamu
        self.documents.append(document)
        
        # Uložení aktualizované databáze
        self._save_db()
