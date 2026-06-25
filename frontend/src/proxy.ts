import { NextRequest, NextResponse } from 'next/server';

const AUTH_TOKEN_KEY = 'JWT_token';

function isValidToken(token: string | undefined): boolean {
    if (!token) return false;
    const parts = token.split('.');
    if (parts.length !== 3) return false;
    try {
        const payload = JSON.parse(atob(parts[1]));
        if (payload.exp && payload.exp * 1000 < Date.now()) return false;
        return true;
    } catch {
        return false;
    }
}

export function proxy(request: NextRequest) {
    const { pathname } = request.nextUrl;
    const token = request.cookies.get(AUTH_TOKEN_KEY)?.value;
    const isAuthenticated = isValidToken(token);

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