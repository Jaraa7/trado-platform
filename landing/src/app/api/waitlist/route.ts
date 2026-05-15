import { NextRequest, NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "https://trado-bot.fly.dev";

export async function POST(req: NextRequest) {
  try {
    const { email, name, country } = await req.json();

    if (!email || !email.includes("@")) {
      return NextResponse.json(
        { error: "Email is required" },
        { status: 400 }
      );
    }

    // Forward to backend
    const res = await fetch(`${API_URL}/waitlist`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, name, country }),
    });

    if (!res.ok) {
      console.error("Backend error:", await res.text());
    }

    return NextResponse.json({ success: true });
  } catch (e) {
    console.error("Waitlist error:", e);
    return NextResponse.json(
      { error: "Failed to add to waitlist" },
      { status: 500 }
    );
  }
}
