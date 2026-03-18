"""
Test database queries to see if that's the issue
"""
from database import get_db, engine
from models import InfrastructureUpload
from sqlalchemy.orm import Session

print("=== Testing Database Connection ===")

# Get a database session
db = next(get_db())

print("\n=== Querying Uploads ===")
try:
    uploads = db.query(InfrastructureUpload).all()
    print(f"Found {len(uploads)} uploads")
    
    if uploads:
        latest = uploads[-1]
        print(f"\nLatest upload:")
        print(f"  ID: {latest.id}")
        print(f"  Filename: {latest.filename}")
        print(f"  Storage URL: {latest.storage_url}")
        print(f"  Parse Status: {latest.parse_status}")
        print(f"  Created: {latest.created_at}")
        
        # Test the URL split
        print(f"\n=== Testing URL Split ===")
        try:
            import os
            SPACES_BUCKET = os.getenv("SPACES_BUCKET", "1donsspaces")
            SPACES_REGION = os.getenv("SPACES_REGION", "nyc3")
            
            print(f"  Bucket: {SPACES_BUCKET}")
            print(f"  Region: {SPACES_REGION}")
            print(f"  Storage URL: {latest.storage_url}")
            
            s3_key = latest.storage_url.split(f"{SPACES_BUCKET}.{SPACES_REGION}.digitaloceanspaces.com/")[1]
            print(f"  Extracted S3 Key: {s3_key}")
            print("  ✅ URL split works!")
            
        except Exception as e:
            print(f"  ❌ URL split failed: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n✅ Database query test passed!")
    
except Exception as e:
    print(f"\n❌ Database query failed!")
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
finally:
    db.close()
