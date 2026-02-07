# worker/main.py

import asyncio
from worker.hana_sync import hana_sync_loop
from worker.bp_sync import bp_sync_loop
from worker.sap_sl_sync import sap_sl_sync_loop
from worker.item_sync import item_sync_loop
from worker.order_sync import order_sync_loop


async def main():
    await asyncio.gather(
        #hana_sync_loop(period=3600),      # deliveries from SAP
        #sap_sl_sync_loop(period=3600),     # approvals to SAP
        #bp_sync_loop(period=3600*6),    # BP sync every 6h - 3600 * 6
        item_sync_loop(period=3600),    # Item sync every 1h
        #order_sync_loop(period=60),     # Order sync every 1 min (or faster/slower)
    )


if __name__ == "__main__":
    asyncio.run(main())
