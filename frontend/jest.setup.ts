import '@testing-library/jest-dom'

class MockObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
    takeRecords() { return []; }
}

if (!global.ResizeObserver) {
    global.ResizeObserver = MockObserver as unknown as typeof ResizeObserver;
}

if (!global.IntersectionObserver) {
    global.IntersectionObserver = MockObserver as unknown as typeof IntersectionObserver;
}