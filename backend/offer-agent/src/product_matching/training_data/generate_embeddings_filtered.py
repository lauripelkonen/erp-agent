#!/usr/bin/env python3
"""
Generate OpenAI embeddings for products CSV file with comprehensive field support.

This script creates embeddings for product CSV files using OpenAI's
text-embedding-3-large model (as configured in config.py). It processes multiple
Finnish product catalog fields including product name, specifications, measurements,
and other metadata to create comprehensive embeddings for semantic search.

Supported fields:
- Tuotekoodi (Product code)
- Laatu (Quality/Grade)
- Määrittely (Specification)
- Tuotenimi (Product name)
- Paksuus (Thickness)
- Tuoteryhmä (Product group)
- Lisänimi (Additional name)
- Halkaisija (Diameter)
- Seinämä (Wall thickness)
- Muu mitta (Other measurement)
- Pinta (Surface)
- Yksikkö paino (Unit weight)
- Paineluokka (Pressure class)
- Lisätiedot (Additional information)
- Toleranssi (Tolerance)
- Sisähalkaisija (Inner diameter)
- Leveys (Width)
- Korkeus/pituus (Height/length)
- Eräkoko (Batch size)

Usage:
    python generate_embeddings_filtered.py

The script will:
1. Load products CSV file (semicolon-separated)
2. Combine all available product fields into comprehensive text representations
3. Generate embeddings using OpenAI API
4. Save embeddings as .npy file for semantic search
5. Display progress and statistics
"""

import os
import sys
import logging
import time
from typing import List
import pandas as pd
import numpy as np
from openai import OpenAI

# Add project root to Python path to enable imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import existing configuration
from src.product_matching.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate embeddings for product data using OpenAI API."""
    
    def __init__(self, csv_path: str):
        self.csv_path = csv_path
        self.output_path = f"{os.path.splitext(csv_path)[0]}.openai_embeddings.npy"
        
        # Initialize OpenAI client (force real OpenAI, not Gemini proxy)
        self.openai_client = OpenAI(
            api_key=Config.OPENAI_API_KEY,
            base_url="https://api.openai.com/v1"  # Force real OpenAI endpoint
        )
        # Use actual OpenAI embedding model, not Gemini
        self.embedding_model = "text-embedding-3-large"  # Real OpenAI model
        
        # Rate limiting tracking
        self.api_calls_made = 0
        self.api_errors = 0
        self.daily_calls = 0
        self.minute_calls = 0
        self.last_minute_reset = time.time()
        
        logger.info(f"🚀 Initialized embedding generator")
        logger.info(f"📁 Input file: {self.csv_path}")
        logger.info(f"💾 Output file: {self.output_path}")
        logger.info(f"🤖 Model: {self.embedding_model}")
        
    def _check_rate_limits(self):
        """Check and enforce OpenAI rate limits."""
        current_time = time.time()
        
        # Reset minute counter if needed
        if current_time - self.last_minute_reset >= 60:
            self.minute_calls = 0
            self.last_minute_reset = current_time
        
        # Check minute limit
        if self.minute_calls >= Config.OPENAI_RATE_LIMIT_PER_MINUTE:
            wait_time = 60 - (current_time - self.last_minute_reset)
            if wait_time > 0:
                logger.info(f"⏱️ Rate limit reached, waiting {wait_time:.1f} seconds...")
                time.sleep(wait_time)
                self.minute_calls = 0
                self.last_minute_reset = time.time()
        
        # Check daily limit
        if self.daily_calls >= Config.OPENAI_RATE_LIMIT_PER_DAY:
            logger.error(f"❌ Daily rate limit reached ({Config.OPENAI_RATE_LIMIT_PER_DAY} calls)")
            raise RuntimeError("Daily API rate limit exceeded")

    def _get_openai_embedding(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings from OpenAI with rate limiting."""
        self._check_rate_limits()
        
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=texts,
                encoding_format="float"
            )
            
            # Update rate limiting counters
            self.daily_calls += 1
            self.minute_calls += 1
            self.api_calls_made += 1
            
            # Extract embeddings
            embeddings = [data.embedding for data in response.data]
            return embeddings
            
        except Exception as e:
            self.api_errors += 1
            logger.error(f"❌ OpenAI embedding API error: {e}")
            raise

    def load_products(self) -> pd.DataFrame:
        """Load and validate the products CSV file."""
        if not os.path.exists(self.csv_path):
            raise FileNotFoundError(f"Products CSV not found: {self.csv_path}")

        logger.info(f"📂 Loading products from {self.csv_path}")
        df = pd.read_csv(self.csv_path, encoding="utf-8", sep=';')

        # Expected columns from Finnish product catalog
        expected_columns = [
            'Tuotekoodi', 'Laatu', 'Määrittely', 'Tuotenimi', 'Paksuus',
            'Tuoteryhmä', 'Lisänimi', 'Halkaisija', 'Seinämä', 'Muu mitta',
            'Pinta', 'Yksikkö paino', 'Paineluokka', 'Lisätiedot', 'Toleranssi',
            'Sisähalkaisija', 'Leveys', 'Korkeus/pituus', 'Eräkoko'
        ]

        # Check which expected columns are present
        present_columns = [col for col in expected_columns if col in df.columns]
        missing_columns = [col for col in expected_columns if col not in df.columns]

        if missing_columns:
            logger.warning(f"⚠️ Missing columns: {missing_columns}")

        logger.info(f"✅ Found {len(present_columns)} expected columns: {present_columns}")

        # Create combined text representation for embeddings
        df['embedding_text'] = df.apply(lambda row: self._create_embedding_text(row, present_columns), axis=1)

        # Filter out rows with empty embedding text
        df = df[df['embedding_text'].str.strip() != '']

        logger.info(f"✅ Loaded {len(df)} valid products")
        logger.info(f"📊 All columns: {list(df.columns)}")

        return df

    def _create_embedding_text(self, row: pd.Series, columns: List[str]) -> str:
        """Create a comprehensive text representation from all available fields."""
        parts = []

        # Priority order for fields (most important first)
        priority_fields = [
            'Tuotenimi',      # Product name
            'Tuotekoodi',     # Product code
            'Tuoteryhmä',     # Product group
            'Määrittely',     # Specification
            'Laatu',          # Quality/Grade
        ]

        # Measurement fields
        measurement_fields = [
            'Paksuus',        # Thickness
            'Halkaisija',     # Diameter
            'Sisähalkaisija', # Inner diameter
            'Seinämä',        # Wall thickness
            'Leveys',         # Width
            'Korkeus/pituus', # Height/length
            'Muu mitta',      # Other measurement
        ]

        # Additional descriptive fields
        additional_fields = [
            'Lisänimi',       # Additional name
            'Pinta',          # Surface
            'Paineluokka',    # Pressure class
            'Yksikkö paino',  # Unit weight
            'Toleranssi',     # Tolerance
            'Eräkoko',        # Batch size
            'Lisätiedot',     # Additional information
        ]

        # Add priority fields
        for field in priority_fields:
            if field in columns and pd.notna(row.get(field)):
                value = str(row[field]).strip()
                if value:
                    parts.append(f"{field}: {value}")

        # Add measurement fields
        measurements = []
        for field in measurement_fields:
            if field in columns and pd.notna(row.get(field)):
                value = str(row[field]).strip()
                if value:
                    measurements.append(f"{field}: {value}")
        if measurements:
            parts.append("Mitat: " + ", ".join(measurements))

        # Add additional fields
        for field in additional_fields:
            if field in columns and pd.notna(row.get(field)):
                value = str(row[field]).strip()
                if value:
                    parts.append(f"{field}: {value}")

        return " | ".join(parts)

    def generate_embeddings(self) -> np.ndarray:
        """Generate embeddings for all products."""
        # Check if embeddings already exist
        if os.path.exists(self.output_path):
            user_input = input(f"⚠️ Embeddings file already exists: {self.output_path}\nOverwrite? (y/N): ")
            if user_input.lower() != 'y':
                logger.info("❌ Cancelled by user")
                return None

        # Load products
        df = self.load_products()
        embedding_texts = df['embedding_text'].tolist()
        total_products = len(embedding_texts)
        
        # Optional limit for testing
        max_products = Config.MAX_EMBEDDING_PRODUCTS
        if max_products > 0 and total_products > max_products:
            logger.warning(f"⚠️ Limiting to first {max_products} products (out of {total_products})")
            logger.warning(f"💡 Set MAX_EMBEDDING_PRODUCTS=0 in config.py to process all products")
            embedding_texts = embedding_texts[:max_products]
        else:
            logger.info(f"🚀 Processing ALL {total_products} products")

        # Calculate batching
        batch_size = Config.EMBEDDING_BATCH_SIZE
        total_batches = (len(embedding_texts) + batch_size - 1) // batch_size
        estimated_time_minutes = max(total_batches / Config.OPENAI_RATE_LIMIT_PER_MINUTE, 1.0)

        logger.info(f"📊 Processing {len(embedding_texts)} products in {total_batches} batches")
        logger.info(f"📊 Batch size: {batch_size} products per batch")
        logger.info(f"⏱️ Estimated completion time: {estimated_time_minutes:.1f} minutes")
        logger.info(f"🔄 Rate limits: {Config.OPENAI_RATE_LIMIT_PER_MINUTE}/min, {Config.OPENAI_RATE_LIMIT_PER_DAY}/day")

        # Generate embeddings
        vectors = []
        start_time = time.time()

        for batch_idx in range(total_batches):
            start_idx = batch_idx * batch_size
            end_idx = min(start_idx + batch_size, len(embedding_texts))
            batch_texts = embedding_texts[start_idx:end_idx]

            logger.info(f"📦 Batch {batch_idx + 1}/{total_batches}: {len(batch_texts)} products "
                       f"(API calls: {self.daily_calls}/{Config.OPENAI_RATE_LIMIT_PER_DAY})")

            try:
                batch_embeddings = self._get_openai_embedding(batch_texts)
                vectors.extend(batch_embeddings)

                # Progress info
                elapsed_time = time.time() - start_time
                progress = (batch_idx + 1) / total_batches
                estimated_total_time = elapsed_time / progress if progress > 0 else 0
                remaining_time = estimated_total_time - elapsed_time

                logger.info(f"✅ Batch {batch_idx + 1} completed: {len(batch_embeddings)} embeddings "
                           f"(~{remaining_time/60:.1f} min remaining)")

            except Exception as e:
                logger.error(f"❌ Batch {batch_idx + 1} failed: {e}")
                # Add zero vectors for failed batch to maintain alignment
                embedding_dim = 3072  # text-embedding-3-large dimension
                for _ in batch_texts:
                    vectors.append([0.0] * embedding_dim)
        
        if len(vectors) == 0:
            logger.error("❌ No embeddings generated")
            return None
        
        # Convert to numpy array
        embeddings_array = np.asarray(vectors, dtype="float32")
        total_time = time.time() - start_time
        
        logger.info(f"✅ Generated {len(vectors)} embeddings (shape: {embeddings_array.shape})")
        logger.info(f"⏱️ Total time: {total_time/60:.1f} minutes")
        logger.info(f"📊 API calls made: {self.api_calls_made}, Errors: {self.api_errors}")
        
        return embeddings_array

    def save_embeddings(self, embeddings: np.ndarray) -> bool:
        """Save embeddings to disk."""
        try:
            np.save(self.output_path, embeddings)
            file_size_mb = os.path.getsize(self.output_path) / (1024 * 1024)
            logger.info(f"💾 Saved embeddings to {self.output_path} ({file_size_mb:.1f} MB)")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to save embeddings: {e}")
            return False

    def verify_embeddings(self) -> bool:
        """Verify the saved embeddings file."""
        try:
            loaded_embeddings = np.load(self.output_path)
            logger.info(f"✅ Verification successful: {loaded_embeddings.shape}")
            
            # Basic sanity checks
            if len(loaded_embeddings.shape) != 2:
                logger.error("❌ Invalid embeddings shape")
                return False
            
            if loaded_embeddings.shape[1] not in [1536, 3072]:  # Common OpenAI embedding dimensions
                logger.warning(f"⚠️ Unexpected embedding dimension: {loaded_embeddings.shape[1]}")
            
            # Check for all-zero vectors (indicates failures)
            zero_vectors = np.sum(np.all(loaded_embeddings == 0, axis=1))
            if zero_vectors > 0:
                logger.warning(f"⚠️ Found {zero_vectors} zero vectors (failed embeddings)")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Verification failed: {e}")
            return False


def main():
    """Main function to generate embeddings."""
    csv_path = "products.csv"
    
    if not os.path.exists(csv_path):
        logger.error(f"❌ CSV file not found: {csv_path}")
        sys.exit(1)
    
    # Check OpenAI API key
    if not Config.OPENAI_API_KEY:
        logger.error("❌ OPENAI_API_KEY not configured in config.py")
        sys.exit(1)
    
    try:
        generator = EmbeddingGenerator(csv_path)
        
        # Generate embeddings
        embeddings = generator.generate_embeddings()
        if embeddings is None:
            logger.error("❌ Embedding generation failed or cancelled")
            sys.exit(1)
        
        # Save embeddings
        if not generator.save_embeddings(embeddings):
            logger.error("❌ Failed to save embeddings")
            sys.exit(1)
        
        # Verify embeddings
        if not generator.verify_embeddings():
            logger.error("❌ Embedding verification failed")
            sys.exit(1)
        
        logger.info("🎉 Embedding generation completed successfully!")
        logger.info(f"📁 Output file: {generator.output_path}")
        logger.info("💡 You can now use this embeddings file for semantic search")
        
    except KeyboardInterrupt:
        logger.info("❌ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 