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

    it('trigger refreshSession on window events', () => {
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

    it('refreshSession is not called again within the threshold', () => {
        renderHook(() => useSessionKeepAlive());
        
        window.dispatchEvent(new Event('keydown'));
        expect(refreshSession).toHaveBeenCalledTimes(1);
        // 4 min in, so below the 5 min threshold therefore refreshSession should still be called a total of 1 times
        jest.setSystemTime(time + (4*60*1000))
        window.dispatchEvent(new Event('keydown'));
        expect(refreshSession).toHaveBeenCalledTimes(1);

        // Past 5 min so it should make the call
        jest.setSystemTime(time + (5*60*1001))
        window.dispatchEvent(new Event('keydown'));
        expect(refreshSession).toHaveBeenCalledTimes(2);

    })
})

