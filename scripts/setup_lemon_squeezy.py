#!/usr/bin/env python3
"""
🍋 TRADO — Lemon Squeezy Auto Setup
ينشئ المنتجات والباقات تلقائياً بعد إنشاء الحساب

استخدام:
    export LEMONSQUEEZY_API_KEY="eyJ..."
    export LEMONSQUEEZY_STORE_ID="12345"
    python3 scripts/setup_lemon_squeezy.py
"""
import os
import asyncio
import json
import httpx

API_KEY  = os.getenv("LEMONSQUEEZY_API_KEY", "")
STORE_ID = os.getenv("LEMONSQUEEZY_STORE_ID", "")
BASE_URL = "https://api.lemonsqueezy.com/v1"

HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/vnd.api+json",
    "Authorization": f"Bearer {API_KEY}",
}

# ════════════════════════════════════════════════
# الباقات الثمانية مع الأسعار
# ════════════════════════════════════════════════
TIERS = [
    {"name": "Micro",           "slug": "micro",         "monthly": 29,    "annual": 290},
    {"name": "Starter",         "slug": "starter",       "monthly": 59,    "annual": 590},
    {"name": "Pro",             "slug": "pro",           "monthly": 99,    "annual": 990},
    {"name": "Elite",           "slug": "elite",         "monthly": 199,   "annual": 1990},
    {"name": "Whale",           "slug": "whale",         "monthly": 499,   "annual": 4990},
    {"name": "Institutional",   "slug": "institutional", "monthly": 1499,  "annual": 14990},
    {"name": "Founder",         "slug": "founder",       "monthly": 2999,  "annual": None},
]

async def create_product(client: httpx.AsyncClient, tier: dict) -> str:
    """إنشاء منتج"""
    payload = {
        "data": {
            "type": "products",
            "attributes": {
                "name": f"TradoAI {tier['name']}",
                "description": f"TradoAI {tier['name']} — 87 AI agents, Arabic-first trading platform",
                "slug": f"tradoai-{tier['slug']}",
                "status": "published",
            },
            "relationships": {
                "store": {"data": {"type": "stores", "id": STORE_ID}}
            }
        }
    }
    r = await client.post(f"{BASE_URL}/products", json=payload, headers=HEADERS)
    data = r.json()
    if r.status_code not in (200, 201):
        print(f"  ❌ Product error: {data}")
        return None
    product_id = data["data"]["id"]
    print(f"  ✅ Product created: {tier['name']} (ID: {product_id})")
    return product_id


async def create_variant(client: httpx.AsyncClient, product_id: str, tier: dict,
                          billing: str, price_usd: float) -> str:
    """إنشاء variant (شهري أو سنوي)"""
    interval = "month" if billing == "monthly" else "year"
    payload = {
        "data": {
            "type": "variants",
            "attributes": {
                "name": f"TradoAI {tier['name']} — {billing.capitalize()}",
                "price": int(price_usd * 100),    # cents
                "is_subscription": True,
                "interval": interval,
                "interval_count": 1,
                "has_free_trial": billing == "monthly",
                "trial_interval": "day",
                "trial_interval_count": 7 if billing == "monthly" else 0,
                "status": "published",
            },
            "relationships": {
                "product": {"data": {"type": "products", "id": product_id}}
            }
        }
    }
    r = await client.post(f"{BASE_URL}/variants", json=payload, headers=HEADERS)
    data = r.json()
    if r.status_code not in (200, 201):
        print(f"  ❌ Variant error ({billing}): {data}")
        return None
    variant_id = data["data"]["id"]
    print(f"  ✅ Variant: {tier['name']} {billing} = ${price_usd} (ID: {variant_id})")
    return variant_id


async def main():
    if not API_KEY or not STORE_ID:
        print("❌ يجب تعيين LEMONSQUEEZY_API_KEY و LEMONSQUEEZY_STORE_ID")
        print("\nمثال:")
        print('  export LEMONSQUEEZY_API_KEY="eyJ..."')
        print('  export LEMONSQUEEZY_STORE_ID="12345"')
        return

    print("🍋 بدء إعداد Lemon Squeezy لـ TradoAI")
    print("=" * 60)

    env_vars = {}

    async with httpx.AsyncClient(timeout=30) as client:
        for tier in TIERS:
            print(f"\n📦 باقة: {tier['name']}")
            print("-" * 40)

            # إنشاء المنتج
            product_id = await create_product(client, tier)
            if not product_id:
                continue

            # Variant شهري
            monthly_id = await create_variant(client, product_id, tier, "monthly", tier["monthly"])
            if monthly_id:
                env_vars[f"LS_{tier['slug'].upper()}_MONTHLY_VARIANT"] = monthly_id

            # Variant سنوي (إذا موجود)
            if tier.get("annual"):
                annual_id = await create_variant(client, product_id, tier, "annual", tier["annual"])
                if annual_id:
                    env_vars[f"LS_{tier['slug'].upper()}_ANNUAL_VARIANT"] = annual_id

            await asyncio.sleep(0.5)    # Rate limiting

    # طباعة الـ environment variables
    print("\n" + "=" * 60)
    print("✅ تم الإعداد! أضف هذه المتغيرات لـ Fly.io:")
    print("=" * 60)
    print()

    fly_cmd = "flyctl secrets set \\\n"
    for key, val in env_vars.items():
        fly_cmd += f'  {key}="{val}" \\\n'
    fly_cmd += "  -a trado-bot"

    print(fly_cmd)
    print()

    # احفظ في ملف
    with open(".env.lemonsqueezy", "w") as f:
        for key, val in env_vars.items():
            f.write(f'{key}="{val}"\n')

    print("💾 تم الحفظ في: .env.lemonsqueezy")
    print()
    print("الخطوة التالية:")
    print("  انسخ الأوامر أعلاه وشغّلها في Terminal")


if __name__ == "__main__":
    asyncio.run(main())
