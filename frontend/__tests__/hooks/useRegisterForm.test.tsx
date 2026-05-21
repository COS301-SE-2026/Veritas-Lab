import { act, renderHook, waitFor } from '@testing-library/react';
import useRegisterForm from '../../src/hooks/useRegisterForm';
import { register } from '../../src/api/register';

const mockReplace = jest.fn();

jest.mock('../../src/api/register', () => ({
	register: jest.fn(),
}));

jest.mock('next/navigation', () => ({
	useRouter: () => ({
		replace: mockReplace,
	}),
}));

describe('useRegisterForm', () => {
	afterEach(() => {
		jest.clearAllMocks();
	});

	it('starts with empty fields', () => {
		const { result } = renderHook(() => useRegisterForm());

		expect(result.current.formState.username).toBe('');
		expect(result.current.formState.email).toBe('');
		expect(result.current.formState.password).toBe('');
		expect(result.current.formState.confirmPassword).toBe('');
	});

	it('shows validation errors for invalid input', async () => {
		const { result } = renderHook(() => useRegisterForm());

		act(() => {
			result.current.updateField('username', '');
			result.current.updateField('email', 'invalid');
			result.current.updateField('password', 'weak');
			result.current.updateField('confirmPassword', 'weak');
		});

		await act(async () => {
			await result.current.handleSubmit({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);
		});

		expect(result.current.status.error).toBe('Please enter a username.');
		expect(register).not.toHaveBeenCalled();
	});

	it('submits successfully and resets the form', async () => {
		const mockedRegister = register as jest.MockedFunction<typeof register>;
		mockedRegister.mockResolvedValue({
			status: 'success',
			message: 'Account created successfully.',
		});

		const { result } = renderHook(() => useRegisterForm());

		act(() => {
			result.current.updateField('username', 'jane.doe');
			result.current.updateField('email', 'jane@veritaslab.com');
			result.current.updateField('password', 'ValidPassword!1');
			result.current.updateField('confirmPassword', 'ValidPassword!1');
		});

		await act(async () => {
			await result.current.handleSubmit({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);
		});

		await waitFor(() => {
			expect(mockedRegister).toHaveBeenCalledWith('jane.doe', 'jane@veritaslab.com', 'ValidPassword!1');
		});
		expect(result.current.status.success).toBe('Account created successfully.');
		expect(result.current.formState.username).toBe('');
		expect(result.current.formState.email).toBe('');
		expect(mockReplace).toHaveBeenCalledWith('/login');
	});

	it('shows an API error when registration does not succeed', async () => {
		const mockedRegister = register as jest.MockedFunction<typeof register>;
		mockedRegister.mockResolvedValue({
			status: 'error',
			message: 'Registration failed. Please try again.',
		});

		const { result } = renderHook(() => useRegisterForm());

		act(() => {
			result.current.updateField('username', 'jane.doe');
			result.current.updateField('email', 'jane@veritaslab.com');
			result.current.updateField('password', 'ValidPassword!1');
			result.current.updateField('confirmPassword', 'ValidPassword!1');
		});

		await act(async () => {
			await result.current.handleSubmit({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);
		});

		expect(result.current.status.error).toBe('Registration failed. Please try again.');
		expect(mockReplace).not.toHaveBeenCalled();
	});

	it('shows a network error when registration rejects', async () => {
		const mockedRegister = register as jest.MockedFunction<typeof register>;
		mockedRegister.mockRejectedValue(new Error('Unable to reach the server. Please try again later.'));

		const { result } = renderHook(() => useRegisterForm());

		act(() => {
			result.current.updateField('username', 'jane.doe');
			result.current.updateField('email', 'jane@veritaslab.com');
			result.current.updateField('password', 'ValidPassword!1');
			result.current.updateField('confirmPassword', 'ValidPassword!1');
		});

		await act(async () => {
			await result.current.handleSubmit({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);
		});

		expect(result.current.status.error).toBe('Unable to reach the server. Please try again later.');
		expect(mockReplace).not.toHaveBeenCalled();
	});

	it('uses the fallback registration error when the rejection is not an Error', async () => {
		const mockedRegister = register as jest.MockedFunction<typeof register>;
		mockedRegister.mockRejectedValue('offline');

		const { result } = renderHook(() => useRegisterForm());

		act(() => {
			result.current.updateField('username', 'jane.doe');
			result.current.updateField('email', 'jane@veritaslab.com');
			result.current.updateField('password', 'ValidPassword!1');
			result.current.updateField('confirmPassword', 'ValidPassword!1');
		});

		await act(async () => {
			await result.current.handleSubmit({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);
		});

		expect(result.current.status.error).toBe('Unable to reach the server. Please try again later.');
	});
});