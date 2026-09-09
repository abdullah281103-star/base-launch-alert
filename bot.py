import os
import json
import time
import requests
import asyncio
import websockets

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CONTRACT = "0xb095274743941e953c746f9c228da9c18bb6ec29".lower()

# Base Flashblocks WebSocket
WS_URL = "wss://mainnet-preconf.base.org"

seen = set()


def telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    data = {
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    }

    try:
        requests.post(url, json=data, timeout=15)
    except Exception as e:
        print("Telegram error:", e)


async def watch():

    while True:

        try:

            async with websockets.connect(
                WS_URL,
                ping_interval=20,
                ping_timeout=20
            ) as ws:

                # Subscribe to transactions containing logs
                request = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_subscribe",
                    "params": [
                        "newFlashblockTransactions",
                        True
                    ]
                }

                await ws.send(json.dumps(request))

                print("Connected to Base Flashblocks")

                telegram(
                    "🟢 BASE WATCHER ONLINE\n\n"
                    "Monitoring contract:\n"
                    f"{CONTRACT}\n\n"
                    "Real-time monitoring started."
                )

                while True:

                    raw = await ws.recv()
                    data = json.loads(raw)

                    result = data.get("params", {}).get("result")

                    if not result:
                        continue

                    logs = result.get("logs", [])

                    for log in logs:

                        address = log.get("address", "").lower()

                        if address != CONTRACT:
                            continue

                        tx = log.get("transactionHash")

                        if not tx:
                            continue

                        if tx in seen:
                            continue

                        seen.add(tx)

                        message = (
                            "🚨 CONTRACT ACTIVITY\n\n"
                            f"Contract:\n{CONTRACT}\n\n"
                            f"TX:\n{tx}\n\n"
                            f"BaseScan:\n"
                            f"https://basescan.org/tx/{tx}"
                        )

                        telegram(message)

        except Exception as e:

            print("Connection error:", e)

            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(watch())
