"""
🔬 Debug: طباعة الرد الخام من Bybit
"""
import asyncio
import os
import json
from dotenv import load_dotenv

load_dotenv()


async def main():
    import ccxt.async_support as ccxt

    print("🔬 Debug Mode — الرد الخام من Bybit")
    print("=" * 70)

    exchange = ccxt.bybit({
        "apiKey": os.getenv("BYBIT_API_KEY"),
        "secret": os.getenv("BYBIT_SECRET"),
        "enableRateLimit": True,
    })
    exchange.set_sandbox_mode(True)

    # 1. Wallet balance — UNIFIED
    print("\n📊 1. /v5/account/wallet-balance?accountType=UNIFIED")
    print("-" * 70)
    try:
        result = await exchange.private_get_v5_account_wallet_balance({
            "accountType": "UNIFIED"
        })
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ {e}")

    # 2. Account info
    print("\n📊 2. /v5/account/info")
    print("-" * 70)
    try:
        result = await exchange.private_get_v5_account_info({})
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ {e}")

    # 3. All coins balance via asset endpoint
    print("\n📊 3. /v5/asset/transfer/query-account-coins-balance")
    print("-" * 70)
    for acc_type in ["UNIFIED", "FUND", "CONTRACT", "SPOT"]:
        try:
            result = await exchange.private_get_v5_asset_transfer_query_account_coin_balance({
                "accountType": acc_type,
                "coin": "USDT"
            })
            print(f"\n  {acc_type}:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"  ❌ {acc_type}: {str(e)[:200]}")

    # 4. Universal endpoint
    print("\n📊 4. /v5/asset/coin/query-info?coin=USDT")
    print("-" * 70)
    try:
        result = await exchange.private_get_v5_asset_coin_query_info({"coin": "USDT"})
        print(json.dumps(result, indent=2, ensure_ascii=False)[:1500])
    except Exception as e:
        print(f"❌ {str(e)[:200]}")

    await exchange.close()
    print("\n" + "=" * 70)
    print("✅ اكتمل")


if __name__ == "__main__":
    asyncio.run(main())
