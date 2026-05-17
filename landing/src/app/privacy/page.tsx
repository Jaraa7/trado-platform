"use client";
export default function PrivacyPage() {
  return (
    <div style={{maxWidth:760,margin:"0 auto",padding:"80px 24px",color:"#f1f5f9",fontFamily:"'Inter',system-ui,sans-serif",lineHeight:1.8}}>
      <h1 style={{fontSize:32,fontWeight:700,marginBottom:8}}>Privacy Policy</h1>
      <p style={{color:"rgba(255,255,255,0.4)",marginBottom:48}}>Last updated: {new Date().toLocaleDateString("en-US",{year:"numeric",month:"long",day:"numeric"})}</p>

      {[
        {title:"1. Information We Collect",body:"We collect information you provide directly (name, email, payment info), information from connected exchanges (read-only API data), and usage data (features used, signals viewed). We never collect private keys, withdrawal permissions, or wallet seed phrases."},
        {title:"2. How We Use Your Information",body:"We use your information to provide and improve the Service, process payments, send notifications and signals, provide customer support, and comply with legal obligations."},
        {title:"3. Exchange API Data",body:"When you connect an exchange API, we only store read-only market data and trade history necessary to provide our Service. We never store or transmit withdrawal API keys. You can revoke API access at any time from your exchange settings."},
        {title:"4. Data Sharing",body:"We do not sell your personal information. We may share data with: payment processors (for billing), cloud infrastructure providers (for hosting), and analytics services (anonymized usage data). All third parties are bound by confidentiality agreements."},
        {title:"5. Data Security",body:"We implement industry-standard security measures including encryption at rest and in transit, regular security audits, and access controls. However, no system is 100% secure and we cannot guarantee absolute security."},
        {title:"6. Data Retention",body:"We retain your account data for as long as your account is active or as needed to provide services. Upon account deletion, personal data is removed within 30 days, except where retention is required by law."},
        {title:"7. Cookies",body:"We use essential cookies for authentication and session management, and analytics cookies (with your consent) to improve the Service. You can control cookie preferences in your browser settings."},
        {title:"8. Your Rights",body:"You have the right to access, correct, or delete your personal data. You may also request data portability or object to processing. To exercise these rights, contact privacy@tradoai.net."},
        {title:"9. Children's Privacy",body:"TradoAI is not intended for users under 18 years of age. We do not knowingly collect data from minors."},
        {title:"10. International Transfers",body:"Your data may be processed in countries outside your jurisdiction. We ensure appropriate safeguards are in place for any international transfers."},
        {title:"11. Changes to This Policy",body:"We may update this Privacy Policy periodically. We will notify you of significant changes via email or in-app notification. The date at the top of this page indicates the last revision."},
        {title:"12. Contact Us",body:"For privacy-related inquiries: privacy@tradoai.net"},
      ].map(s=>(
        <div key={s.title} style={{marginBottom:32}}>
          <h2 style={{fontSize:18,fontWeight:600,marginBottom:8,color:"#f1f5f9"}}>{s.title}</h2>
          <p style={{color:"rgba(255,255,255,0.6)",fontSize:15}}>{s.body}</p>
        </div>
      ))}
    </div>
  );
}
