import { refreshSession } from "@/lib/api/refresh"
import { useSessionKeepAlive } from "@/lib/hooks/useSessionKeepAlive";
import { renderHook } from "@testing-library/react";


jest.mock('@/lib/api/refresh', () => ({
    refreshSession: jest.fn()
}));

describe('useSessionKeepAlive', () => {
    const time = 1000000;

    beforeEach(() => {
        jest.clearAllMocks();
        jest.useFakeTimers();
        jest.setSystemTime(time);
    })

    afterEach(() => {
        jest.useRealTimers();
    });

    test('trigger refreshSession on window events', () => {
        renderHook(() => useSessionKeepAlive());

        window.dispatchEvent(new Event('click'));
        expect(refreshSession).toHaveBeenCalledTimes(1);
        window.dispatchEvent(new Event('keydown'));
        expect(refreshSession).toHaveBeenCalledTimes(1);
        window.dispatchEvent(new Event('scroll'));
        expect(refreshSession).toHaveBeenCalledTimes(1);
        window.dispatchEvent(new Event('mousemove'));
        expect(refreshSession).toHaveBeenCalledTimes(1);
    })
})

