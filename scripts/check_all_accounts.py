"""
🔍 فحص جميع حسابات Bybit Testnet
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()


async def check_all_accounts():
    import ccxt.async_support as ccxt

    print("🔍 فحص جميع حسابات Bybit Testnet")
    print("=" * 60)

    exchange = ccxt.bybit({
        "apiKey": os.getenv("BYBIT_API_KEY"),
        "secret": os.getenv("BYBIT_SECRET"),
        "enableRateLimit": True,
    })
    exchange.set_sandbox_mode(True)

    account_types = ["UNIFIED", "CONTRACT", "SPOT", "FUND", "OPTION"]

    for acc_type in account_types:
        print(f"\n📊 الحساب: {acc_type}")
        print("-" * 60)
        try:
            result = await exchange.private_get_v5_account_wallet_balance({
                "accountType": acc_type
            })

            if result.get("retCode") == 0:
                lists = result["result"].get("list", [])
                if not lists:
                    print("   (فارغ)")
                    continue

                for account in lists:
                    coins = account.get("coin", [])
                    found = False
                    for coin in coins:
                        wallet_bal = float(coin.get("walletBalance", 0) or 0)
                        if wallet_bal > 0:
                            print(f"   ✅ {coin['coin']}: {wallet_bal:,.4f}")
                            usd_val = float(coin.get("usdValue", 0) or 0)
                            if usd_val > 0:
                                print(f"      قيمة بالدولار: ${usd_val:,.2f}")
                            found = True

                    total = account.get("totalEquity", "0")
                    if total and float(total) > 0:
                        print(f"   💰 إجمالي الحساب: ${float(total):,.2f}")
                        found = True

                    if not found:
                        print("   (فارغ)")
            else:
                print(f"   ⚠️  {result.get('retMsg')}")
        except Exception as e:
            err = str(e)[:100]
            print(f"   ❌ خطأ: {err}")

    # محاولة عبر CCXT العادية
    print("\n\n📊 عبر CCXT (Spot default):")
    print("-" * 60)
    try:
        bal = await exchange.fetch_balance()
        non_zero = {k: v for k, v in bal.get("total", {}).items() if v and v > 0}
        if non_zero:
            for coin, amt in non_zero.items():
                print(f"   ✅ {coin}: {amt:,.4f}")
        else:
            print("   (فارغ)")
    except Exception as e:
        print(f"   ❌ {str(e)[:100]}")

    await exchange.close()
    print("\n" + "=" * 60)
    print("✅ اكتمل الفحص")


if __name__ == "__main__":
    asyncio.run(check_all_accounts())
