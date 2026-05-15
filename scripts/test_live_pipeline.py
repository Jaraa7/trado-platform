"""
🧪 TRADO — Live Bybit Testnet Integration
سكريبت اختبار كامل للـ pipeline على Bybit testnet

تشغيل:
    pip install -r requirements.txt
    cp .env.example .env  (وأضف مفاتيحك)
    python scripts/test_live_pipeline.py
"""
import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# إضافة المشروع للـ path
sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()


async def test_step_1_connection():
    """الخطوة 1: التحقق من الاتصال"""
    print("\n" + "═" * 70)
    print("  🧪 الخطوة 1: اختبار الاتصال بـ Bybit Testnet")
    print("═" * 70)

    import ccxt.async_support as ccxt

    exchange = ccxt.bybit({
        "apiKey": os.getenv("BYBIT_API_KEY"),
        "secret": os.getenv("BYBIT_SECRET"),
        "enableRateLimit": True,
    })
    exchange.set_sandbox_mode(True)

    try:
        # رصيد الحساب
        balance = await exchange.fetch_balance()
        usdt = balance.get("USDT", {})
        print(f"  ✅ الاتصال نجح!")
        print(f"  💰 رصيد USDT متاح: ${usdt.get('free', 0):,.2f}")
        print(f"  💰 إجمالي USDT:    ${usdt.get('total', 0):,.2f}")

        await exchange.close()
        return True, usdt.get("free", 0)
    except Exception as e:
        await exchange.close()
        print(f"  ❌ خطأ: {e}")
        return False, 0


async def test_step_2_market_data():
    """الخطوة 2: جلب بيانات السوق"""
    print("\n" + "═" * 70)
    print("  📊 الخطوة 2: جلب بيانات السوق")
    print("═" * 70)

    import ccxt.async_support as ccxt

    exchange = ccxt.bybit({
        "apiKey": os.getenv("BYBIT_API_KEY"),
        "secret": os.getenv("BYBIT_SECRET"),
    })
    exchange.set_sandbox_mode(True)

    try:
        # السعر الحالي
        ticker = await exchange.fetch_ticker("BTC/USDT")
        price = ticker["last"]
        print(f"  💰 BTC/USDT: ${price:,.2f}")
        print(f"  📊 تغيير 24h: {ticker.get('percentage', 0):+.2f}%")

        # البيانات التاريخية
        ohlcv = await exchange.fetch_ohlcv("BTC/USDT", "1h", limit=24)
        avg_volume = sum(c[5] for c in ohlcv[:-1]) / 23
        current_vol = ohlcv[-1][5]
        vol_ratio = current_vol / avg_volume if avg_volume > 0 else 1

        print(f"  📈 نسبة الحجم: {vol_ratio:.2f}x المتوسط")
        print(f"  📊 آخر 24 ساعة: {len(ohlcv)} شمعة")

        await exchange.close()
        return True, price, vol_ratio, ohlcv
    except Exception as e:
        await exchange.close()
        print(f"  ❌ خطأ: {e}")
        return False, 0, 0, []


async def test_step_3_ai_analysis(price, vol_ratio):
    """الخطوة 3: تحليل AI من Analyst Master"""
    print("\n" + "═" * 70)
    print("  🤖 الخطوة 3: تحليل AI (Analyst Master)")
    print("═" * 70)

    from agents.trading.analyst.agent import AnalystMaster

    analyst = AnalystMaster(user_id="founder")
    market_data = {
        "price": price,
        "volume_ratio": vol_ratio,
        "volume_24h_above_avg": vol_ratio > 1.5,
    }

    response = await analyst.analyze("BTC/USDT", market_data, user_id="founder")

    if response.success:
        print(f"  ✅ التحليل نجح!")
        print(f"  💰 التكلفة: ${response.cost_usd:.6f}")
        print(f"  ⏱️  الوقت: {response.processing_time_ms:.0f}ms")
        print()
        print("  📝 ملخص التحليل (أول 500 حرف):")
        print("  " + "─" * 60)
        for line in response.content[:500].split("\n"):
            print(f"  {line}")
        print("  " + "─" * 60)
        return True, response.content
    else:
        print(f"  ❌ فشل: {response.content}")
        return False, ""


async def test_step_4_risk_check(price, balance):
    """الخطوة 4: فحص Risk Guardian"""
    print("\n" + "═" * 70)
    print("  🛡️ الخطوة 4: فحص Risk Guardian")
    print("═" * 70)

    from agents.trading.risk_guardian.agent import RiskGuardian, TradeProposal

    guardian = RiskGuardian(user_id="founder")
    proposal = TradeProposal(
        symbol="BTC/USDT",
        direction="long",
        entry_price=price,
        stop_loss=price * 0.97,    # -3%
        take_profit=price * 1.06,  # +6%
        account_balance=balance,
        leverage=1
    )

    decision = guardian.calculate_position_size(proposal)

    print(f"  📊 الاقتراح:")
    print(f"     Entry: ${proposal.entry_price:,.2f}")
    print(f"     SL:    ${proposal.stop_loss:,.2f} (-3%)")
    print(f"     TP:    ${proposal.take_profit:,.2f} (+6%)")
    print()
    print(f"  🔍 القرار: {'✅ APPROVED' if decision.approved else '❌ REJECTED'}")
    print(f"     💵 الحجم: ${decision.recommended_size:,.2f}")
    print(f"     📊 % من رأس المال: {(decision.recommended_size/balance)*100:.1f}%")
    print(f"     📉 الخسارة المحتملة: {decision.risk_percentage}%")
    print(f"     🎯 R:R: {decision.risk_reward}")
    print(f"     💬 السبب: {decision.reason}")

    return decision


async def test_step_5_execute_paper_trade(price, decision):
    """الخطوة 5: تنفيذ صفقة testnet حقيقية"""
    print("\n" + "═" * 70)
    print("  ⚡ الخطوة 5: تنفيذ صفقة testnet")
    print("═" * 70)

    if not decision.approved:
        print("  ⏭️  تخطّي — Risk Guardian رفض الصفقة")
        return None

    import ccxt.async_support as ccxt

    exchange = ccxt.bybit({
        "apiKey": os.getenv("BYBIT_API_KEY"),
        "secret": os.getenv("BYBIT_SECRET"),
    })
    exchange.set_sandbox_mode(True)

    try:
        # حساب كمية BTC (ليس USDT)
        btc_amount = decision.recommended_size / price
        btc_amount = round(btc_amount, 5)  # دقة Bybit

        print(f"  📋 تفاصيل الصفقة:")
        print(f"     السعر:    ${price:,.2f}")
        print(f"     الكمية:   {btc_amount:.5f} BTC")
        print(f"     القيمة:   ${decision.recommended_size:,.2f}")
        print()
        print(f"  ⚡ جاري التنفيذ...")

        order = await exchange.create_order(
            symbol="BTC/USDT",
            type="market",
            side="buy",
            amount=btc_amount,
        )

        print(f"  ✅ الصفقة نُفّذت!")
        print(f"     Order ID: {order.get('id')}")
        print(f"     السعر الفعلي: ${order.get('average') or order.get('price', 0):,.2f}")
        print(f"     الحالة: {order.get('status')}")

        await exchange.close()
        return order
    except Exception as e:
        await exchange.close()
        print(f"  ❌ فشل التنفيذ: {e}")
        return None


async def test_step_6_check_position():
    """الخطوة 6: التحقق من الصفقة المفتوحة"""
    print("\n" + "═" * 70)
    print("  📊 الخطوة 6: الموقف الحالي")
    print("═" * 70)

    import ccxt.async_support as ccxt

    exchange = ccxt.bybit({
        "apiKey": os.getenv("BYBIT_API_KEY"),
        "secret": os.getenv("BYBIT_SECRET"),
    })
    exchange.set_sandbox_mode(True)

    try:
        balance = await exchange.fetch_balance()
        btc = balance.get("BTC", {})
        usdt = balance.get("USDT", {})

        print(f"  💼 الرصيد بعد الصفقة:")
        print(f"     USDT:  ${usdt.get('total', 0):,.2f}")
        print(f"     BTC:   {btc.get('total', 0):.5f}")

        if btc.get("total", 0) > 0:
            ticker = await exchange.fetch_ticker("BTC/USDT")
            current_value = btc.get("total", 0) * ticker["last"]
            print(f"     قيمة BTC الحالية: ${current_value:,.2f}")

        await exchange.close()
    except Exception as e:
        await exchange.close()
        print(f"  ❌ خطأ: {e}")


async def main():
    """تشغيل الـ pipeline الكامل"""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + "  🚀 TRADO Platform — Live Testnet Pipeline".ljust(67) + "║")
    print("║" + f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}".ljust(67) + "║")
    print("╚" + "═" * 68 + "╝")

    # الخطوات
    ok, balance = await test_step_1_connection()
    if not ok:
        return

    ok, price, vol_ratio, ohlcv = await test_step_2_market_data()
    if not ok:
        return

    ok, analysis = await test_step_3_ai_analysis(price, vol_ratio)
    if not ok:
        return

    decision = await test_step_4_risk_check(price, balance)

    # سؤال قبل التنفيذ
    print()
    print("  ⚠️  هل تريد تنفيذ صفقة testnet حقيقية؟")
    answer = input("  اكتب 'yes' للتنفيذ (testnet فقط - أموال وهمية): ").strip().lower()

    if answer == "yes":
        order = await test_step_5_execute_paper_trade(price, decision)
        if order:
            await asyncio.sleep(2)
            await test_step_6_check_position()

    # الخلاصة
    print("\n" + "═" * 70)
    print("  ✅ Pipeline اكتمل بنجاح!")
    print("═" * 70)


if __name__ == "__main__":
    asyncio.run(main())
