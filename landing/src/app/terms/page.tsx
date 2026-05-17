"use client";
export default function TermsPage() {
  return (
    <div style={{maxWidth:760,margin:"0 auto",padding:"80px 24px",color:"#f1f5f9",fontFamily:"'Inter',system-ui,sans-serif",lineHeight:1.8}}>
      <h1 style={{fontSize:32,fontWeight:700,marginBottom:8}}>Terms of Service</h1>
      <p style={{color:"rgba(255,255,255,0.4)",marginBottom:48}}>Last updated: {new Date().toLocaleDateString("en-US",{year:"numeric",month:"long",day:"numeric"})}</p>

      {[
        {title:"1. Acceptance of Terms",body:"By accessing or using TradoAI ('the Service'), you agree to be bound by these Terms of Service. If you do not agree, please do not use the Service."},
        {title:"2. Description of Service",body:"TradoAI provides AI-powered crypto trading signals, market analysis tools, and portfolio management features. The Service is for informational purposes only and does not constitute financial advice."},
        {title:"3. Risk Disclosure",body:"Cryptocurrency trading involves substantial risk of loss. TradoAI signals and tools are provided for informational purposes only. Past performance does not guarantee future results. You are solely responsible for your trading decisions and any financial losses incurred."},
        {title:"4. Account Registration",body:"You must provide accurate and complete information when creating an account. You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account."},
        {title:"5. Subscription & Billing",body:"TradoAI offers paid subscription plans billed monthly or annually. Subscriptions automatically renew unless cancelled before the renewal date. Refunds are available within 14 days of payment if less than 50% of signals have been used."},
        {title:"6. Cancellation Policy",body:"You may cancel your subscription at any time. Upon cancellation, you will retain access to the Service until the end of your current billing period. No partial refunds are issued for unused periods beyond the 14-day refund window."},
        {title:"7. API & Exchange Connections",body:"When connecting exchange APIs, TradoAI requests only read and trade permissions. We never request withdrawal permissions. Your funds remain on your exchange at all times and are never held by TradoAI."},
        {title:"8. Prohibited Uses",body:"You may not use the Service for any unlawful purpose, to manipulate markets, to engage in fraudulent activity, or to violate any applicable laws or regulations."},
        {title:"9. Intellectual Property",body:"All content, features, and functionality of TradoAI are owned by TradoAI and are protected by international copyright, trademark, and other intellectual property laws."},
        {title:"10. Limitation of Liability",body:"TradoAI shall not be liable for any indirect, incidental, special, or consequential damages arising from your use of the Service, including but not limited to trading losses."},
        {title:"11. Modifications",body:"We reserve the right to modify these Terms at any time. We will notify users of material changes via email or in-app notification. Continued use of the Service after changes constitutes acceptance."},
        {title:"12. Governing Law",body:"These Terms shall be governed by applicable laws. Any disputes shall be resolved through binding arbitration."},
        {title:"13. Contact",body:"For questions about these Terms, contact us at: legal@tradoai.net"},
      ].map(s=>(
        <div key={s.title} style={{marginBottom:32}}>
          <h2 style={{fontSize:18,fontWeight:600,marginBottom:8,color:"#f1f5f9"}}>{s.title}</h2>
          <p style={{color:"rgba(255,255,255,0.6)",fontSize:15}}>{s.body}</p>
        </div>
      ))}
    </div>
  );
}
