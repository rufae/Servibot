"""
Script to reindex all files in uploads directory
Run this after backend starts to ensure all files are indexed
"""
import requests
import os
import time

API_URL = "http://127.0.0.1:8000"
UPLOADS_DIR = "./data/uploads"

def reindex_all():
    """Reindex all files in uploads directory"""
    if not os.path.exists(UPLOADS_DIR):
        print(f"❌ Directory not found: {UPLOADS_DIR}")
        return
    
    files = [f for f in os.listdir(UPLOADS_DIR) if os.path.isfile(os.path.join(UPLOADS_DIR, f))]
    
    if not files:
        print("📂 No files found in uploads directory")
        return
    
    print(f"📁 Found {len(files)} files to index")
    
    for filename in files:
        try:
            print(f"\n🔄 Indexing: {filename}")
            response = requests.post(f"{API_URL}/api/upload/reindex/{filename}")
            
            if response.status_code == 200:
                print(f"✅ Started indexing: {filename}")
                
                # Wait for indexing to complete
                time.sleep(3)
                
                # Check status
                status_resp = requests.get(f"{API_URL}/api/upload/status/{filename}")
                if status_resp.status_code == 200:
                    status_data = status_resp.json()
                    if status_data.get("status") == "indexed":
                        chunks = status_data.get("debug", {}).get("indexed", "?")
                        print(f"✓ Indexed: {chunks} chunks")
                    else:
                        print(f"⚠️ Status: {status_data.get('status')} - {status_data.get('message')}")
            else:
                print(f"❌ Failed: {response.status_code} - {response.text}")
        
        except Exception as e:
            print(f"❌ Error indexing {filename}: {e}")
    
    print("\n✅ Reindexing complete!")

if __name__ == "__main__":
    print("🚀 ServiBot - Reindex All Files")
    print("=" * 50)
    reindex_all()
