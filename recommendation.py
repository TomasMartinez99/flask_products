# En un nuevo archivo recommendation.py
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ProductRecommender:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self.products = None
        self.product_indices = {}
    
    def fit(self, products):
        """Entrena el recomendador con los productos disponibles"""
        self.products = products
        
        # Crear un corpus combinando nombre y descripción
        corpus = []
        for i, product in enumerate(products):
            # Guardar índice para búsquedas rápidas
            self.product_indices[product.id] = i
            
            text = product.name
            if product.description:
                text += " " + product.description
            corpus.append(text)
        
        # Crear matriz TF-IDF
        self.tfidf_matrix = self.vectorizer.fit_transform(corpus)
        return self
    
    def get_recommendations(self, product_id, num_recommendations=3):
        """Obtiene productos similares basados en contenido textual"""
        # Verificar si el producto existe
        if product_id not in self.product_indices:
            return []
        
        # Obtener índice del producto
        idx = self.product_indices[product_id]
        
        # Calcular similitud del coseno
        sim_scores = cosine_similarity(
            self.tfidf_matrix[idx:idx+1], 
            self.tfidf_matrix
        ).flatten()
        
        # Obtener los índices de los productos más similares (excluyendo el mismo producto)
        sim_scores[idx] = 0  # Excluir el mismo producto
        top_indices = sim_scores.argsort()[-num_recommendations:][::-1]
        
        # Devolver los productos recomendados
        return [self.products[i] for i in top_indices if sim_scores[i] > 0]