import { NextRequest, NextResponse } from 'next/server';

const AUTH_TOKEN_KEY = 'JWT_token';

function decodeJwtPayload(segment: string): Record<string, unknown> {
    let base64 = segment.replace(/-/g, '+').replace(/_/g, '/');
    while (base64.length % 4 !== 0) {
        base64 += '=';
    }
    return JSON.parse(atob(base64));
}
 
function isValidToken(token: string | undefined): boolean {
    if (!token) return false;
 
    const parts = token.split('.');
    if (parts.length !== 3) return false;
 
    try {
        const payload = decodeJwtPayload(parts[1]);
        const exp = payload.exp;
        if (typeof exp === 'number' && exp * 1000 < Date.now()) return false;
        return true;
    } catch {
        return false;
    }
}

export function proxy(request: NextRequest) {
    const { pathname } = request.nextUrl;
    const token = request.cookies.get(AUTH_TOKEN_KEY)?.value;
    const isAuthenticated = isValidToken(token);
    
    if (token && !isAuthenticated) {
        const response = isProtectedPath(pathname)
            ? NextResponse.redirect(new URL('/login', request.url))
            : NextResponse.next();
        response.cookies.delete(AUTH_TOKEN_KEY);
        return response;
    }

    if (pathname === '/') {
        return NextResponse.redirect(new URL(isAuthenticated ? '/dashboard' : '/login', request.url));
    }

    if (!isAuthenticated && isProtectedPath(pathname)) {
        return NextResponse.redirect(new URL('/login', request.url));
    }

    if (isAuthenticated && isAuthRoute(pathname)) {
        return NextResponse.redirect(new URL('/dashboard', request.url));
    }

    return NextResponse.next();
}

const protectedPrefixes = ['/dashboard', '/case-page'];
const authRoutes = ['/login', '/register'];

function isProtectedPath(pathname: string): boolean {
    return protectedPrefixes.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`));
}

function isAuthRoute(pathname: string): boolean {
    return authRoutes.some((route) => pathname === route || pathname.startsWith(`${route}/`));
}

export const config = {
    matcher: ['/', '/dashboard/:path*', '/case-page/:path*', '/login', '/register'],
};