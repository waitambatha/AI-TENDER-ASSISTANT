from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class QuestionSimilarity:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Free, lightweight model
    
    def get_similarity(self, question1, question2, threshold=0.8):
        embeddings = self.model.encode([question1, question2])
        similarity = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
        return similarity >= threshold, similarity
    
    def find_similar_question(self, new_question, stored_questions, threshold=0.8):
        if not stored_questions:
            return None, 0
        
        new_embedding = self.model.encode([new_question])
        stored_embeddings = self.model.encode(stored_questions)
        
        similarities = cosine_similarity(new_embedding, stored_embeddings)[0]
        max_similarity = np.max(similarities)
        
        if max_similarity >= threshold:
            best_match_idx = np.argmax(similarities)
            return best_match_idx, max_similarity
        
        return None, max_similarity
