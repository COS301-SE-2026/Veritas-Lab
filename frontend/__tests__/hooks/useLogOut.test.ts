import { renderHook, act } from '@testing-library/react';
import { useLogOut } from '@/lib/hooks/useLogOut';
import { deleteCookie } from '@/auth/cookie';
import { useRouter } from 'next/navigation';

jest.mock('@/auth/cookie', () => ({
    deleteCookie: jest.fn(),
}));

jest.mock('next/navigation', () => ({
    useRouter: jest.fn(),
}));

describe('useLogOut', () => {
    const mockReplace = jest.fn();
    const mockRefresh = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();

        (useRouter as jest.Mock).mockReturnValue({
            replace: mockReplace,
            refresh: mockRefresh,
        });

        (deleteCookie as jest.Mock).mockResolvedValue(undefined);
    });

    it('should return a logOut function', () => {
        const { result } = renderHook(() => useLogOut());
        expect(result.current.logOut).toBeDefined();
        expect(typeof result.current.logOut).toBe('function');
    });

    it('should call deleteCookie when logOut is called', async () => {
        const { result } = renderHook(() => useLogOut());

        await act(async () => {
            await result.current.logOut();
        });

        expect(deleteCookie).toHaveBeenCalledTimes(1);
    });

    it('should redirect to /login after logging out', async () => {
        const { result } = renderHook(() => useLogOut());

        await act(async () => {
            await result.current.logOut();
        });

        expect(mockReplace).toHaveBeenCalledTimes(1);
        expect(mockReplace).toHaveBeenCalledWith('/login');
    });

    it('should call router.refresh after redirecting', async () => {
        const { result } = renderHook(() => useLogOut());

        await act(async () => {
            await result.current.logOut();
        });

        expect(mockRefresh).toHaveBeenCalledTimes(1);
    });

    it('should call deleteCookie before redirecting', async () => {
        const callOrder: string[] = [];

        (deleteCookie as jest.Mock).mockImplementation(async () => {
            callOrder.push('deleteCookie');
        });

        mockReplace.mockImplementation(() => {
            callOrder.push('replace');
        });

        const { result } = renderHook(() => useLogOut());

        await act(async () => {
            await result.current.logOut();
        });

        expect(callOrder).toEqual(['deleteCookie', 'replace']);
    });

    it('should call replace before refresh', async () => {
        const callOrder: string[] = [];

        mockReplace.mockImplementation(() => {
            callOrder.push('replace');
        });

        mockRefresh.mockImplementation(() => {
            callOrder.push('refresh');
        });

        const { result } = renderHook(() => useLogOut());

        await act(async () => {
            await result.current.logOut();
        });

        expect(callOrder).toEqual(['replace', 'refresh']);
    });

    it('should propagate errors thrown by deleteCookie', async () => {
        (deleteCookie as jest.Mock).mockRejectedValue(new Error('Cookie deletion failed'));

        const { result } = renderHook(() => useLogOut());

        await expect(
            act(async () => {
                await result.current.logOut();
            })
        ).rejects.toThrow('Cookie deletion failed');

        expect(mockReplace).not.toHaveBeenCalled();
        expect(mockRefresh).not.toHaveBeenCalled();
    });
});