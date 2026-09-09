import os
import json
import asyncio
import requests
import websockets

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

CONTRACT = "0xb095274743941e953c746f9c228da9c18bb6ec29".lower()

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
        response = requests.post(url, json=data, timeout=15)
        print("Telegram:", response.status_code, flush=True)
        print(response.text, flush=True)
    except Exception as e:
        print("Telegram error:", repr(e), flush=True)


async def watch():

    print("🚀 BOT STARTED", flush=True)
    print(f"Monitoring contract: {CONTRACT}", flush=True)
    print("Connecting to Base...", flush=True)

    telegram(
        "🟢 BASE WATCHER STARTED\n\n"
        f"Contract:\n{CONTRACT}\n\n"
        "Monitoring is active."
    )

    while True:
        try:
            print("Connecting WebSocket...", flush=True)

            async with websockets.connect(
                WS_URL,
                ping_interval=20,
                ping_timeout=20
            ) as ws:

                print("🟢 CONNECTED TO BASE", flush=True)

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

                response = await ws.recv()
                print("Subscription response:", response, flush=True)

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

                        print(f"🚨 CONTRACT ACTIVITY: {tx}", flush=True)

                        telegram(
                            "🚨 LAPTOP CONTRACT ACTIVITY\n\n"
                            f"Contract:\n{CONTRACT}\n\n"
                            f"TX:\n{tx}\n\n"
                            f"BaseScan:\n"
                            f"https://basescan.org/tx/{tx}"
                        )

        except Exception as e:

            print("🔴 CONNECTION ERROR:", repr(e), flush=True)

            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(watch())
