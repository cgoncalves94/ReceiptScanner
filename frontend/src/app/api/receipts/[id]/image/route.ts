import type { NextRequest } from "next/server";
import { cookies } from "next/headers";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_COOKIE_KEY = "receipt_scanner_token";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const cookieStore = await cookies();
  const token = cookieStore.get(TOKEN_COOKIE_KEY)?.value;

  if (!token) {
    return new Response("Unauthorized", { status: 401 });
  }

  const { id } = await params;
  const url = `${API_BASE_URL}/api/v1/receipts/${id}/image`;
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    const text = await response.text();
    return new Response(text || response.statusText, { status: response.status });
  }

  const contentType =
    response.headers.get("content-type") || "application/octet-stream";

  return new Response(response.body, {
    status: response.status,
    headers: { "Content-Type": contentType },
  });
}
