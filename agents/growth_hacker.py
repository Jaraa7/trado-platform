import anthropic

class GrowthHacker:
    CRYPTO_INFLUENCERS_AR = [
        "@cryptoarab", "@trading_gulf", "@bitcoin_ksa",
        "@defi_arabic", "@altcoin_kuwait"
    ]

    def __init__(self, config):
        self.claude = anthropic.Anthropic(api_key=config["ANTHROPIC_API_KEY"])

    def analyze_viral_potential(self, post_text, platform="telegram"):
        prompt = (f"Analyze this {platform} crypto post for viral potential.\n"
                  f"Post: {post_text}\n"
                  "Rate 1-10 and suggest improvements. Respond JSON: {score:int, improvements:[str]}")
        try:
            resp = self.claude.messages.create(
                model="claude-sonnet-4-6", max_tokens=300,
                messages=[{"role":"user","content":prompt}])
            import json
            return json.loads(resp.content[0].text.strip())
        except Exception:
            return {"score": 5, "improvements": []}

    def draft_partnership_message(self, influencer_name, follower_count):
        return (",".join([
            f"مرحبا {influencer_name},",
            "نحن فريق TRADO - منصة تداول ذكاء اصطناعي للسوق العربي.",
            f"لديك {follower_count:,} متابع - نود التعاون معك.",
            "شراكة مدفوعة + عمولة 15% على كل اشتراك.",
            "trado.app/partners"
        ]))