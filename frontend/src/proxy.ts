import { NextRequest, NextResponse } from "next/server";

const TOKEN_KEY = "receipt_scanner_token";

// Routes that don't require authentication
const PUBLIC_ROUTES = ["/login", "/register"];

// Routes to exclude from middleware (API routes, static files, etc.)
const EXCLUDED_ROUTES = ["/api", "/_next", "/favicon.ico"];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Skip middleware for excluded routes
  if (EXCLUDED_ROUTES.some((route) => pathname.startsWith(route))) {
    return NextResponse.next();
  }

  // Skip middleware for public routes
  if (PUBLIC_ROUTES.includes(pathname)) {
    return NextResponse.next();
  }

  // Check for authentication token in cookies
  const token = request.cookies.get(TOKEN_KEY)?.value;

  // If no token, redirect to login
  if (!token) {
    const loginUrl = new URL("/login", request.url);
    // Add redirect query param to return to original page after login
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Token exists, allow the request
  return NextResponse.next();
}

// Configure which routes the middleware runs on
export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!api|_next/static|_next/image|favicon.ico).*)",
  ],
};
