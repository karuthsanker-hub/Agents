"""
Environment Validation Tests
============================
Tests to validate all environment configurations:
- OpenAI API connection
- PostgreSQL database
- Redis cache
- ChromaDB vector store
- Pinecone vector database
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color codes for terminal output
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{Colors.RESET}\n")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")


def print_warning(message: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.RESET}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.RESET}")


# ============================================================
# Test 1: Hello World Agent Test (OpenAI)
# ============================================================
def test_openai_hello_world() -> bool:
    """Test OpenAI API connection with a simple hello world."""
    print_header("Test 1: OpenAI Hello World Agent")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print_error("OPENAI_API_KEY not found in environment")
        return False
    
    print_info(f"API Key found: {api_key[:20]}...{api_key[-4:]}")
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        print_info(f"Testing with model: {model}")
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Respond concisely."},
                {"role": "user", "content": "Say 'Hello World! Agent is ready.' and nothing else."}
            ],
            max_completion_tokens=50,
            temperature=0
        )
        
        result = response.choices[0].message.content
        print_success(f"Agent Response: {result}")
        print_info(f"Tokens used: {response.usage.total_tokens}")
        return True
        
    except Exception as e:
        print_error(f"OpenAI test failed: {e}")
        return False


# ============================================================
# Test 2: PostgreSQL Database Test
# ============================================================
def test_postgresql() -> bool:
    """Test PostgreSQL database connection."""
    print_header("Test 2: PostgreSQL Database")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print_warning("DATABASE_URL not set - skipping PostgreSQL test")
        print_info("Set DATABASE_URL=postgresql://user:pass@localhost:5432/dbname")
        return None  # Skipped
    
    print_info(f"DATABASE_URL: {database_url.split('@')[0].rsplit(':', 1)[0]}:***@{database_url.split('@')[-1]}")
    
    try:
        import psycopg2
        
        # Parse connection string or use directly
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print_success(f"PostgreSQL connected!")
        print_info(f"Version: {version[:50]}...")
        
        # Create test table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_test (
                id SERIAL PRIMARY KEY,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Insert test data
        cursor.execute("INSERT INTO agent_test (message) VALUES ('Hello from Agent!') RETURNING id;")
        test_id = cursor.fetchone()[0]
        print_success(f"Test record inserted with ID: {test_id}")
        
        # Clean up
        cursor.execute("DELETE FROM agent_test WHERE id = %s;", (test_id,))
        conn.commit()
        print_success("Test record cleaned up")
        
        cursor.close()
        conn.close()
        return True
        
    except ImportError:
        print_error("psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print_error(f"PostgreSQL test failed: {e}")
        return False


# ============================================================
# Test 3: Redis Cache Test
# ============================================================
def test_redis() -> bool:
    """Test Redis connection."""
    print_header("Test 3: Redis Cache")
    
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        print_warning("REDIS_URL not set - skipping Redis test")
        print_info("Set REDIS_URL=redis://localhost:6379/0")
        return None  # Skipped
    
    print_info(f"REDIS_URL: {redis_url}")
    
    try:
        import redis
        
        # Connect to Redis
        r = redis.from_url(redis_url)
        
        # Test ping
        if r.ping():
            print_success("Redis connected!")
        
        # Test set/get
        test_key = "agent_test_key"
        test_value = "Hello from Agent!"
        
        r.set(test_key, test_value, ex=60)  # Expires in 60 seconds
        retrieved = r.get(test_key)
        
        if retrieved and retrieved.decode() == test_value:
            print_success(f"Set/Get test passed: '{test_value}'")
        
        # Get server info
        info = r.info()
        print_info(f"Redis version: {info.get('redis_version', 'unknown')}")
        print_info(f"Connected clients: {info.get('connected_clients', 'unknown')}")
        
        # Clean up
        r.delete(test_key)
        print_success("Test key cleaned up")
        
        return True
        
    except ImportError:
        print_error("redis not installed. Run: pip install redis")
        return False
    except Exception as e:
        print_error(f"Redis test failed: {e}")
        return False


# ============================================================
# Test 4: ChromaDB Vector Store Test
# ============================================================
def test_chromadb() -> bool:
    """Test ChromaDB local vector store."""
    print_header("Test 4: ChromaDB Vector Store")
    
    persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    print_info(f"CHROMA_PERSIST_DIR: {persist_dir}")
    
    try:
        import chromadb
        
        # Create persistent client using new API
        client = chromadb.PersistentClient(path=persist_dir)
        print_success("ChromaDB client created!")
        
        # Create or get collection
        collection = client.get_or_create_collection(
            name="agent_test_collection",
            metadata={"description": "Test collection for agent memory"}
        )
        print_success(f"Collection 'agent_test_collection' ready")
        
        # Add test documents
        collection.add(
            documents=["Hello World from Agent!", "This is a test memory."],
            metadatas=[{"type": "greeting"}, {"type": "test"}],
            ids=["test_1", "test_2"]
        )
        print_success("Test documents added")
        
        # Query test
        results = collection.query(
            query_texts=["Hello"],
            n_results=1
        )
        print_success(f"Query test passed: Found '{results['documents'][0][0]}'")
        
        # Get collection count
        count = collection.count()
        print_info(f"Collection document count: {count}")
        
        # Clean up test documents
        collection.delete(ids=["test_1", "test_2"])
        print_success("Test documents cleaned up")
        
        return True
        
    except ImportError:
        print_error("chromadb not installed. Run: pip install chromadb")
        return False
    except Exception as e:
        print_error(f"ChromaDB test failed: {e}")
        return False


# ============================================================
# Test 5: Pinecone Vector Database Test
# ============================================================
def test_pinecone() -> bool:
    """Test Pinecone cloud vector database."""
    print_header("Test 5: Pinecone Vector Database")
    
    api_key = os.getenv("PINECONE_API_KEY")
    environment = os.getenv("PINECONE_ENVIRONMENT")
    
    if not api_key:
        print_warning("PINECONE_API_KEY not set - skipping Pinecone test")
        print_info("Set PINECONE_API_KEY=your-api-key")
        return None  # Skipped
    
    print_info(f"PINECONE_API_KEY: {api_key[:8]}...{api_key[-4:]}")
    print_info(f"PINECONE_ENVIRONMENT: {environment or 'not set (using default)'}")
    
    try:
        from pinecone import Pinecone, ServerlessSpec
        
        # Initialize Pinecone
        pc = Pinecone(api_key=api_key)
        print_success("Pinecone client initialized!")
        
        # List indexes
        indexes = pc.list_indexes()
        print_info(f"Available indexes: {[idx.name for idx in indexes]}")
        
        # Check if we can access the API
        print_success("Pinecone API connection verified!")
        
        return True
        
    except ImportError:
        print_error("pinecone-client not installed. Run: pip install pinecone-client")
        return False
    except Exception as e:
        print_error(f"Pinecone test failed: {e}")
        return False


# ============================================================
# Main Test Runner
# ============================================================
def run_all_tests():
    """Run all environment tests."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        🤖 FIRST AGENT - ENVIRONMENT VALIDATION 🤖         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(Colors.RESET)
    
    results = {}
    
    # Run all tests
    results["OpenAI"] = test_openai_hello_world()
    results["PostgreSQL"] = test_postgresql()
    results["Redis"] = test_redis()
    results["ChromaDB"] = test_chromadb()
    results["Pinecone"] = test_pinecone()
    
    # Print summary
    print_header("Test Summary")
    
    passed = 0
    failed = 0
    skipped = 0
    
    for name, result in results.items():
        if result is True:
            print_success(f"{name}: PASSED")
            passed += 1
        elif result is False:
            print_error(f"{name}: FAILED")
            failed += 1
        else:
            print_warning(f"{name}: SKIPPED (not configured)")
            skipped += 1
    
    print(f"\n{Colors.BOLD}Total: {passed} passed, {failed} failed, {skipped} skipped{Colors.RESET}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All configured services are working!{Colors.RESET}\n")
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  Some tests failed. Check the errors above.{Colors.RESET}\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

