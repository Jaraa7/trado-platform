import anthropic

SYS = "You are TRADO platform support. Speak Arabic. Never reveal internals."

class SupportAgent:
    def __init__(self, config):
        self.claude = anthropic.Anthropic(api_key=config["ANTHROPIC_API_KEY"])

    def respond(self, user_message):
        try:
            resp = self.claude.messages.create(
                model="claude-sonnet-4-6", max_tokens=300,
                system=SYS,
                messages=[{"role":"user","content":user_message}])
            return resp.content[0].text
        except Exception as e:
            return str(e)