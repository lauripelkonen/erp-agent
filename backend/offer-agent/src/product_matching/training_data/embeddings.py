"""
OpenAI embedding service for product vectorization and similarity search.
Handles embedding generation, caching, and optimization for product matching.
"""

import asyncio
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import time

import openai
import redis
import numpy as np

from src.config.settings import get_settings
from src.utils.logger import get_logger
from src.utils.exceptions import ExternalServiceError
from src.utils.retry import retry_on_exception, OPENAI_RETRY_CONFIG


class EmbeddingCache:
    """Redis-based caching for embeddings to reduce API calls."""
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        try:
            self.redis_client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                db=0,
                decode_responses=False  # Keep binary for numpy arrays
            )
            # Test connection
            self.redis_client.ping()
            self.cache_enabled = True
        except Exception as e:
            self.logger.warning(f"Redis cache unavailable: {e}")
            self.redis_client = None
            self.cache_enabled = False
        
        # Cache settings
        self.cache_ttl = 86400 * 7  # 7 days
        self.cache_prefix = "embedding:"
    
    def _get_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text and model combination."""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"{self.cache_prefix}{model}:{text_hash}"
    
    async def get_embedding(self, text: str, model: str) -> Optional[np.ndarray]:
        """Get cached embedding if available."""
        if not self.cache_enabled:
            return None
        
        try:
            cache_key = self._get_cache_key(text, model)
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                embedding_dict = json.loads(cached_data)
                embedding_array = np.array(embedding_dict['embedding'])
                
                self.logger.debug(f"Cache hit for text: {text[:50]}...")
                return embedding_array
                
        except Exception as e:
            self.logger.warning(f"Cache retrieval failed: {e}")
        
        return None
    
    async def store_embedding(self, text: str, model: str, embedding: np.ndarray):
        """Store embedding in cache."""
        if not self.cache_enabled:
            return
        
        try:
            cache_key = self._get_cache_key(text, model)
            
            embedding_dict = {
                'embedding': embedding.tolist(),
                'created_at': datetime.utcnow().isoformat(),
                'model': model
            }
            
            cached_data = json.dumps(embedding_dict)
            self.redis_client.setex(cache_key, self.cache_ttl, cached_data)
            
            self.logger.debug(f"Cached embedding for text: {text[:50]}...")
            
        except Exception as e:
            self.logger.warning(f"Cache storage failed: {e}")


class ProductEmbeddingService:
    """
    Service for generating and managing product embeddings using OpenAI API.
    Includes caching, batch processing, and rate limiting.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.logger = get_logger(__name__)
        
        # Initialize OpenAI client with Gemini API
        self.client = openai.AsyncOpenAI(
            api_key=self.settings.gemini_api_key,
            base_url=self.settings.openai_base_url
        )
        
        # Model configuration
        self.embedding_model = self.settings.openai_embedding_model  # Use from settings
        self.embedding_dimensions = 768  # Gemini text-embedding-004 dimension
        
        # Rate limiting
        self.max_requests_per_minute = 1500  # Gemini rate limit
        self.request_timestamps = []
        
        # Batch processing
        self.max_batch_size = 100
        
        # Initialize cache
        self.cache = EmbeddingCache()
        
        if not self.settings.gemini_api_key:
            raise ValueError("Gemini API key not configured")
    
    async def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        # Check cache first
        cached_embedding = await self.cache.get_embedding(text, self.embedding_model)
        if cached_embedding is not None:
            return cached_embedding
        
        # Generate new embedding
        embeddings = await self.generate_embeddings([text])
        return embeddings[0]
    
    @retry_on_exception(config=OPENAI_RETRY_CONFIG)
    async def generate_embeddings(self, texts: List[str]) -> List[np.ndarray]:
        """
        Generate embeddings for multiple texts with batching and rate limiting.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors as numpy arrays
        """
        if not texts:
            return []
        
        # Remove empty texts and normalize
        processed_texts = []
        text_indices = []
        
        for i, text in enumerate(texts):
            cleaned_text = text.strip()
            if cleaned_text:
                processed_texts.append(cleaned_text)
                text_indices.append(i)
        
        if not processed_texts:
            return [np.zeros(self.embedding_dimensions) for _ in texts]
        
        try:
            # Check cache for all texts
            cache_results = {}
            uncached_texts = []
            uncached_indices = []
            
            for i, text in enumerate(processed_texts):
                cached_embedding = await self.cache.get_embedding(text, self.embedding_model)
                if cached_embedding is not None:
                    cache_results[i] = cached_embedding
                else:
                    uncached_texts.append(text)
                    uncached_indices.append(i)
            
            # Generate embeddings for uncached texts
            if uncached_texts:
                self.logger.info(f"Generating embeddings for {len(uncached_texts)} texts")
                
                # Process in batches to respect rate limits
                new_embeddings = {}
                
                for batch_start in range(0, len(uncached_texts), self.max_batch_size):
                    batch_end = min(batch_start + self.max_batch_size, len(uncached_texts))
                    batch_texts = uncached_texts[batch_start:batch_end]
                    batch_indices = uncached_indices[batch_start:batch_end]
                    
                    # Rate limiting
                    await self._enforce_rate_limit()
                    
                    # Generate embeddings for batch
                    self.logger.debug(f"Processing batch {batch_start//self.max_batch_size + 1}")
                    
                    response = await self.client.embeddings.create(
                        model=self.embedding_model,
                        input=batch_texts
                    )
                    
                    # Record timestamp for rate limiting
                    self.request_timestamps.append(time.time())
                    
                    # Process response
                    for i, embedding_data in enumerate(response.data):
                        embedding_vector = np.array(embedding_data.embedding)
                        original_index = batch_indices[i]
                        new_embeddings[original_index] = embedding_vector
                        
                        # Cache the embedding
                        await self.cache.store_embedding(
                            batch_texts[i], 
                            self.embedding_model, 
                            embedding_vector
                        )
            
            # Combine cached and new embeddings
            all_embeddings = {}
            all_embeddings.update(cache_results)
            all_embeddings.update(new_embeddings)
            
            # Create result array maintaining original order
            result_embeddings = []
            for i in range(len(texts)):
                if i in text_indices:
                    processed_index = text_indices.index(i)
                    if processed_index in all_embeddings:
                        result_embeddings.append(all_embeddings[processed_index])
                    else:
                        # Fallback for any missing embeddings
                        result_embeddings.append(np.zeros(self.embedding_dimensions))
                else:
                    # Empty text
                    result_embeddings.append(np.zeros(self.embedding_dimensions))
            
            self.logger.info(f"Generated embeddings for {len(texts)} texts")
            return result_embeddings
            
        except Exception as e:
            self.logger.error(f"Embedding generation failed: {e}")
            raise ExternalServiceError(
                f"Failed to generate embeddings: {str(e)}",
                service="gemini",
                context={
                    'texts_count': len(texts),
                    'model': self.embedding_model
                }
            )
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting to stay within API limits."""
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self.request_timestamps = [
            ts for ts in self.request_timestamps 
            if current_time - ts < 60
        ]
        
        # Check if we're approaching the rate limit
        if len(self.request_timestamps) >= self.max_requests_per_minute:
            # Calculate wait time
            oldest_timestamp = min(self.request_timestamps)
            wait_time = 60 - (current_time - oldest_timestamp)
            
            if wait_time > 0:
                self.logger.info(f"Rate limiting: waiting {wait_time:.2f} seconds")
                await asyncio.sleep(wait_time)
    
    async def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between 0 and 1
        """
        try:
            # Normalize vectors
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            # Compute cosine similarity
            similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
            
            # Convert to 0-1 range (cosine similarity is -1 to 1)
            normalized_similarity = (similarity + 1) / 2
            
            return float(np.clip(normalized_similarity, 0.0, 1.0))
            
        except Exception as e:
            self.logger.error(f"Similarity computation failed: {e}")
            return 0.0
    
    async def find_most_similar(
        self, 
        query_embedding: np.ndarray, 
        candidate_embeddings: List[np.ndarray],
        threshold: float = 0.5
    ) -> List[Tuple[int, float]]:
        """
        Find most similar embeddings to a query embedding.
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of candidate embedding vectors
            threshold: Minimum similarity threshold
            
        Returns:
            List of (index, similarity_score) tuples sorted by similarity
        """
        similarities = []
        
        for i, candidate in enumerate(candidate_embeddings):
            similarity = await self.compute_similarity(query_embedding, candidate)
            if similarity >= threshold:
                similarities.append((i, similarity))
        
        # Sort by similarity score (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        return similarities
    
    def get_embedding_stats(self) -> Dict[str, Any]:
        """Get statistics about embedding generation."""
        recent_requests = [
            ts for ts in self.request_timestamps 
            if time.time() - ts < 3600  # Last hour
        ]
        
        return {
            'model': self.embedding_model,
            'dimensions': self.embedding_dimensions,
            'requests_last_minute': len([
                ts for ts in self.request_timestamps 
                if time.time() - ts < 60
            ]),
            'requests_last_hour': len(recent_requests),
            'cache_enabled': self.cache.cache_enabled,
            'max_batch_size': self.max_batch_size
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the embedding service."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        try:
            # Test embedding generation with a simple text
            test_embedding = await self.generate_embedding("test")
            
            if test_embedding is not None and len(test_embedding) == self.embedding_dimensions:
                health_status['openai_api'] = 'healthy'
                health_status['embedding_dimensions'] = len(test_embedding)
            else:
                health_status['openai_api'] = 'unhealthy'
                health_status['status'] = 'degraded'
                
        except Exception as e:
            health_status['openai_api'] = f'unhealthy: {str(e)}'
            health_status['status'] = 'degraded'
        
        # Check cache status
        health_status['cache_enabled'] = self.cache.cache_enabled
        if self.cache.cache_enabled:
            try:
                self.cache.redis_client.ping()
                health_status['cache_status'] = 'healthy'
            except Exception as e:
                health_status['cache_status'] = f'unhealthy: {str(e)}'
        
        # Add stats
        health_status['stats'] = self.get_embedding_stats()
        
        return health_status 