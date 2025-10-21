"""
Script de teste para processamento AI com Cost Tracking Visual.
Processa apenas poucos incentivos para validar o sistema com custos mínimos.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import SessionLocal
from app.db.models import Incentive, IncentiveMetadata
from app.services.ai_processor import AIProcessor


def main():
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not set!")
        print("   Add it to your .env file")
        return
    
    # Check if running in auto mode (no confirmation)
    auto_mode = "--auto" in sys.argv or os.getenv("AUTO_RUN") == "true"
    
    # Create session
    session = SessionLocal()
    
    try:
        # Get ALL pending incentives (não limita a 3, processa todos)
        print("🔍 Searching for pending incentives...")
        
        pending = session.query(Incentive).join(IncentiveMetadata).filter(
            IncentiveMetadata.ai_processing_status == "pending"
        ).all()  # Remove .limit(3) - processa TODOS os pending
        
        if not pending:
            print("✅ No pending incentives found!")
            print("   All incentives have been processed.")
            return
        
        print(f"📊 Found {len(pending)} pending incentives")
        print()
        
        # Ask for confirmation only if NOT in auto mode
        if not auto_mode:
            print("⚠️  This will make real OpenAI API calls!")
            print(f"   Estimated cost: ~${len(pending) * 0.0005:.6f} (worst case)")
            print()
            response = input("Continue? (y/n): ")
            
            if response.lower() != 'y':
                print("❌ Aborted by user")
                return
        else:
            print(f"🤖 AUTO MODE: Processing {len(pending)} incentives...")
            print(f"   Estimated cost: ~${len(pending) * 0.0005:.6f}")
            print()
        
        # Create AI processor
        ai_processor = AIProcessor(api_key, session)
        
        # Get incentive IDs
        incentive_ids = [str(inc.incentive_id) for inc in pending]
        
        # Process with visual tracking
        result = ai_processor.process_batch_with_visual_tracking(session, incentive_ids)
        
        print()
        print("✅ Processing complete!")
        print(f"   Success: {result['success']}")
        print(f"   Failed: {result['failed']}")
        print()
        
        # Show how to check results
        print("📋 To check results in database:")
        print("   docker compose run --rm api python -c \"")
        print("   from app.db.database import SessionLocal")
        print("   from app.db.models import Incentive")
        print("   session = SessionLocal()")
        print("   incentive = session.query(Incentive).first()")
        print("   print(incentive.ai_description)")
        print("   \"")
        
    finally:
        session.close()


if __name__ == "__main__":
    main()

