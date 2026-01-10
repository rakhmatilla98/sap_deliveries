# worker/main.py

import asyncio
from worker.hana_sync import hana_sync_loop
from worker.bp_sync import bp_sync_loop
from worker.sap_sl_sync import sap_sl_sync_loop


async def main():
    await asyncio.gather(
        hana_sync_loop(period=3600),      # deliveries from SAP
        #sap_sl_sync_loop(period=300),     # approvals to SAP
        bp_sync_loop(period=3600),    # BP sync every 6h - 3600 * 6
    )


if __name__ == "__main__":
    asyncio.run(main())
