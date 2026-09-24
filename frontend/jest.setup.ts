import '@testing-library/jest-dom'

class ResizeObserverMock implements ResizeObserver {
    observe = jest.fn();
    unobserve = jest.fn();
    disconnect = jest.fn();
}

if (!('ResizeObserver' in globalThis)) {
    globalThis.ResizeObserver = ResizeObserverMock as unknown as typeof ResizeObserver;
}