"use client";
export default function RefundPage() {
  return (
    <div style={{maxWidth:760,margin:"0 auto",padding:"80px 24px",color:"#f1f5f9",fontFamily:"'Inter',system-ui,sans-serif",lineHeight:1.8}}>
      <h1 style={{fontSize:32,fontWeight:700,marginBottom:8}}>Refund Policy</h1>
      <p style={{color:"rgba(255,255,255,0.4)",marginBottom:48}}>Last updated: {new Date().toLocaleDateString("en-US",{year:"numeric",month:"long",day:"numeric"})}</p>

      {[
        {title:"14-Day Money Back Guarantee",body:"We offer a full refund within 14 days of your initial payment, provided you have used less than 50% of your monthly signal allocation. This applies to all paid plans."},
        {title:"How to Request a Refund",body:"To request a refund, email billing@tradoai.net with your account email and reason for the refund. We process all refund requests within 3-5 business days."},
        {title:"Conditions for Refund",body:"Refunds are available if: (1) the request is within 14 days of payment, (2) less than 50% of signals have been used, and (3) the account has not been flagged for abuse or violation of Terms of Service."},
        {title:"Non-Refundable Cases",body:"Refunds are not available after the 14-day window, for annual plans after the first 14 days, if more than 50% of signals have been used, or for API access fees."},
        {title:"Subscription Cancellations",body:"Cancelling your subscription stops future charges but does not trigger an automatic refund. You retain access until the end of your current billing period."},
        {title:"Processing Time",body:"Approved refunds are returned to your original payment method within 5-10 business days, depending on your bank or card issuer."},
        {title:"Contact",body:"Billing questions: billing@tradoai.net"},
      ].map(s=>(
        <div key={s.title} style={{marginBottom:32}}>
          <h2 style={{fontSize:18,fontWeight:600,marginBottom:8,color:"#f1f5f9"}}>{s.title}</h2>
          <p style={{color:"rgba(255,255,255,0.6)",fontSize:15}}>{s.body}</p>
        </div>
      ))}
    </div>
  );
}
