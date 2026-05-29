import { renderHook, act } from '@testing-library/react';
import { useLogOut } from '@/lib/hooks/useLogOut';

const mockReplace = jest.fn();
const mockRefresh = jest.fn();

jest.mock('next/navigation', () => ({
	useRouter: () => ({
		replace: mockReplace,
		refresh: mockRefresh,
	}),
}));

describe('useLogOut', () => {
	afterEach(() => {
		jest.clearAllMocks();
		window.localStorage.clear();
	});

	it('removes the auth token and redirects to login', () => {
		window.localStorage.setItem('authToken', 'token-123');
		const { result } = renderHook(() => useLogOut());

		act(() => {
			result.current.logOut();
		});

		expect(window.localStorage.getItem('authToken')).toBeNull();
		expect(mockReplace).toHaveBeenCalledWith('/login');
		expect(mockRefresh).toHaveBeenCalled();
	});

	it('skips localStorage removal when window is unavailable', () => {
		const originalWindow = globalThis.window;
		(globalThis as unknown as { window: Window | undefined }).window = undefined;
		const { result } = renderHook(() => useLogOut());

		act(() => {
			result.current.logOut();
		});

		expect(mockReplace).toHaveBeenCalledWith('/login');
		expect(mockRefresh).toHaveBeenCalled();
		(globalThis as unknown as { window: Window | undefined }).window = originalWindow;
	});
});