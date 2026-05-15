"""
🔍 فحص شامل لـ Bybit Testnet
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def main():
    import ccxt.async_support as ccxt

    print("🔍 فحص شامل لـ Bybit Testnet")
    print("=" * 60)

    exchange = ccxt.bybit({
        "apiKey": os.getenv("BYBIT_API_KEY"),
        "secret": os.getenv("BYBIT_SECRET"),
        "enableRateLimit": True,
    })
    exchange.set_sandbox_mode(True)

    # ───────────────────────────────────────────────────────────
    # 1. الـ UNIFIED account (الرئيسي)
    # ───────────────────────────────────────────────────────────
    print("\n📊 1️⃣ UNIFIED Account (التداول الموحد)")
    print("-" * 60)
    try:
        result = await exchange.private_get_v5_account_wallet_balance({
            "accountType": "UNIFIED"
        })
        if result.get("retCode") == 0:
            for account in result["result"].get("list", []):
                print(f"   accountType:            {account.get('accountType')}")
                print(f"   totalEquity:            ${account.get('totalEquity', '0')}")
                print(f"   totalWalletBalance:     ${account.get('totalWalletBalance', '0')}")
                print(f"   totalAvailableBalance:  ${account.get('totalAvailableBalance', '0')}")
                print()
                coins = account.get("coin", [])
                if coins:
                    print(f"   📦 العملات ({len(coins)}):")
                    for coin in coins:
                        wb = float(coin.get("walletBalance", 0) or 0)
                        if wb > 0:
                            print(f"      ✅ {coin['coin']}: {wb}")
                else:
                    print("   📦 لا توجد عملات")
    except Exception as e:
        print(f"   ❌ {str(e)[:150]}")

    # ───────────────────────────────────────────────────────────
    # 2. فحص جميع الحسابات عبر Asset endpoint
    # ───────────────────────────────────────────────────────────
    print("\n🔍 2️⃣ فحص كل الحسابات (Asset endpoint)")
    print("-" * 60)
    for acc_type in ["UNIFIED", "FUND", "CONTRACT", "SPOT"]:
        try:
            result = await exchange.private_get_v5_asset_transfer_query_account_coins_balance({
                "accountType": acc_type
            })
            if result.get("retCode") == 0:
                balances = result["result"].get("balance", [])
                non_zero = [b for b in balances if float(b.get("walletBalance", 0) or 0) > 0]
                if non_zero:
                    print(f"   ✅ {acc_type}:")
                    for b in non_zero:
                        print(f"      • {b['coin']}: {b.get('walletBalance', 0)}  (transfer: {b.get('transferBalance', 0)})")
                else:
                    print(f"   ⚪ {acc_type}: فارغ")
            else:
                print(f"   ⚠️  {acc_type}: {result.get('retMsg', 'unknown')[:50]}")
        except Exception as e:
            err = str(e)[:80]
            print(f"   ❌ {acc_type}: {err}")

    await exchange.close()

    print("\n" + "=" * 60)
    print("📝 الخلاصة:")
    print("   • لو وجدت USDT في FUND → نحتاج تحويلها إلى UNIFIED")
    print("   • لو لم تجد USDT في أي مكان → الطلب لم ينفّذ بعد")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
