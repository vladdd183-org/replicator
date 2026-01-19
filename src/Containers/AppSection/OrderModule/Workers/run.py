"""Run OrderModule Temporal Worker.

Entry point for running the Order Worker as a standalone process.

Usage:
    python -m src.Containers.AppSection.OrderModule.Workers.run

    # Or directly
    python src/Containers/AppSection/OrderModule/Workers/run.py

The worker will:
1. Connect to Temporal server (configured via environment)
2. Register CreateOrderWorkflow and all activities
3. Poll "orders" task queue for work
4. Execute workflows and activities
5. Handle graceful shutdown on SIGTERM/SIGINT
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.Containers.AppSection.OrderModule.Workers.OrderWorker import run_order_worker

if __name__ == "__main__":
    print("🚀 Starting OrderModule Temporal Worker...")
    print("   Task Queue: orders")
    print("   Press Ctrl+C to stop")
    print()

    try:
        asyncio.run(run_order_worker())
    except KeyboardInterrupt:
        print("\n👋 Worker stopped")
