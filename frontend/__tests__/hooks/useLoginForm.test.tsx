import { act, renderHook, waitFor } from '@testing-library/react';
import { AuthProvider } from '../../src/context/AuthContext';
import useLoginForm from '../../src/hooks/useLoginForm';
import { login } from '../../src/api/login';

const mockReplace = jest.fn();

jest.mock('../../src/api/login', () => ({
	login: jest.fn(),
}));

jest.mock('next/navigation', () => ({
	useRouter: () => ({
		replace: mockReplace,
	}),
}));

describe('useLoginForm', () => {
	afterEach(() => {
		jest.clearAllMocks();
		window.localStorage.clear();
	});

	it('starts with empty fields', () => {
		const { result } = renderHook(() => useLoginForm(), {
			wrapper: AuthProvider,
		});

		expect(result.current.formState.email).toBe('');
		expect(result.current.formState.password).toBe('');
		expect(result.current.status.isSubmitting).toBe(false);
	});

	it('submits successfully and stores the token', async () => {
		const mockedLogin = login as jest.MockedFunction<typeof login>;
		mockedLogin.mockResolvedValue({
			status: 'success',
			token: 'token-123',
			message: 'Login successful.',
		});

		const { result } = renderHook(() => useLoginForm(), {
			wrapper: AuthProvider,
		});

		act(() => {
			result.current.updateField('email', 'user@example.com');
			result.current.updateField('password', 'ValidPassword!1');
		});

		await act(async () => {
			await result.current.handleSubmit({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);
		});

		await waitFor(() => {
			expect(window.localStorage.getItem('authToken')).toBe('token-123');
		});
		expect(result.current.status.success).toBe('Login successful.');
		expect(result.current.formState.email).toBe('');
		expect(result.current.formState.password).toBe('');
		expect(mockReplace).toHaveBeenCalledWith('/dashboard');
	});

	it('shows an API error when login does not return success', async () => {
		const mockedLogin = login as jest.MockedFunction<typeof login>;
		mockedLogin.mockResolvedValue({
			status: 'error',
			token: '',
			message: 'Invalid credentials',
		});

		const { result } = renderHook(() => useLoginForm(), {
			wrapper: AuthProvider,
		});

		act(() => {
			result.current.updateField('email', 'user@example.com');
			result.current.updateField('password', 'ValidPassword!1');
		});

		await act(async () => {
			await result.current.handleSubmit({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);
		});

		expect(result.current.status.error).toBe('Invalid credentials');
		expect(mockReplace).not.toHaveBeenCalled();
	});

	it('shows a network error when the login request rejects', async () => {
		const mockedLogin = login as jest.MockedFunction<typeof login>;
		mockedLogin.mockRejectedValue(new Error('Unable to reach the server. Please try again later.'));

		const { result } = renderHook(() => useLoginForm(), {
			wrapper: AuthProvider,
		});

		act(() => {
			result.current.updateField('email', 'user@example.com');
			result.current.updateField('password', 'ValidPassword!1');
		});

		await act(async () => {
			await result.current.handleSubmit({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);
		});

		expect(result.current.status.error).toBe('Unable to reach the server. Please try again later.');
		expect(mockReplace).not.toHaveBeenCalled();
	});

	it('uses the fallback login error when the rejection is not an Error', async () => {
		const mockedLogin = login as jest.MockedFunction<typeof login>;
		mockedLogin.mockRejectedValue('offline');

		const { result } = renderHook(() => useLoginForm(), {
			wrapper: AuthProvider,
		});

		act(() => {
			result.current.updateField('email', 'user@example.com');
			result.current.updateField('password', 'ValidPassword!1');
		});

		await act(async () => {
			await result.current.handleSubmit({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);
		});

		expect(result.current.status.error).toBe('Unable to reach the server. Please try again later.');
	});
});