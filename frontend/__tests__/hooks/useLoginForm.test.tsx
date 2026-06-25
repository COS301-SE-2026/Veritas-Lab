import { renderHook, act } from '@testing-library/react';
import useLoginForm from '@/lib/hooks/useLoginForm';
import { login } from '@/lib/api/login';
import { useRouter } from 'next/navigation';

jest.mock('@/lib/api/login', () => ({
    login: jest.fn(),
}));

jest.mock('next/navigation', () => ({
    useRouter: jest.fn(),
}));

describe('useLoginForm', () => {
    const mockPush = jest.fn();

    beforeEach(() => {
        jest.clearAllMocks();

        (useRouter as jest.Mock).mockReturnValue({
            push: mockPush,
        });
    });

    describe('initial state', () => {
        it('should return empty form state', () => {
            const { result } = renderHook(() => useLoginForm());
            expect(result.current.formState).toEqual({ email: '', password: '' });
        });

        it('should return idle status', () => {
            const { result } = renderHook(() => useLoginForm());
            expect(result.current.status).toEqual({
                error: null,
                success: null,
                isSubmitting: false,
            });
        });
    });

    describe('updateField', () => {
        it('should update the email field', () => {
            const { result } = renderHook(() => useLoginForm());

            act(() => {
                result.current.updateField('email', 'test@example.com');
            });

            expect(result.current.formState.email).toBe('test@example.com');
        });

        it('should update the password field', () => {
            const { result } = renderHook(() => useLoginForm());

            act(() => {
                result.current.updateField('password', 'secret123');
            });

            expect(result.current.formState.password).toBe('secret123');
        });

        it('should not overwrite other fields when updating one', () => {
            const { result } = renderHook(() => useLoginForm());

            act(() => {
                result.current.updateField('email', 'test@example.com');
                result.current.updateField('password', 'secret123');
            });

            expect(result.current.formState).toEqual({
                email: 'test@example.com',
                password: 'secret123',
            });
        });
    });

    describe('validation', () => {
        const makeEvent = () =>
            ({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);

        it('should set error if email is empty', async () => {
            const { result } = renderHook(() => useLoginForm());

            await act(async () => {
                await result.current.handleSubmit(makeEvent());
            });

            expect(result.current.status.error).toBe('Please enter a valid email.');
            expect(result.current.status.isSubmitting).toBe(false);
        });

        it('should set error if email is invalid', async () => {
            const { result } = renderHook(() => useLoginForm());

            act(() => {
                result.current.updateField('email', 'not-an-email');
            });

            await act(async () => {
                await result.current.handleSubmit(makeEvent());
            });

            expect(result.current.status.error).toBe('Please enter a valid email.');
        });

        it('should set error if password is empty', async () => {
            const { result } = renderHook(() => useLoginForm());

            act(() => {
                result.current.updateField('email', 'test@example.com');
            });

            await act(async () => {
                await result.current.handleSubmit(makeEvent());
            });

            expect(result.current.status.error).toBe('Please enter your password.');
        });

        it('should set error if password is only whitespace', async () => {
            const { result } = renderHook(() => useLoginForm());

            act(() => {
                result.current.updateField('email', 'test@example.com');
                result.current.updateField('password', '   ');
            });

            await act(async () => {
                await result.current.handleSubmit(makeEvent());
            });

            expect(result.current.status.error).toBe('Please enter your password.');
        });

        it('should not call login if validation fails', async () => {
            const { result } = renderHook(() => useLoginForm());

            await act(async () => {
                await result.current.handleSubmit(makeEvent());
            });

            expect(login).not.toHaveBeenCalled();
        });
    });

    describe('handleSubmit - success', () => {
        const makeEvent = () =>
            ({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);

        beforeEach(() => {
            (login as jest.Mock).mockResolvedValue({ status: 'success', message: 'OK' });
        });

        it('should set isSubmitting true while request is in flight', async () => {
            let submittingDuringCall = false;

            (login as jest.Mock).mockImplementation(async () => {
                submittingDuringCall = true;
                return { status: 'success' };
            });

            const { result } = renderHook(() => useLoginForm());

            act(() => {
                result.current.updateField('email', 'test@example.com');
                result.current.updateField('password', 'secret123');
            });

            await act(async () => {
                await result.current.handleSubmit(makeEvent());
            });

            expect(submittingDuringCall).toBe(true);
        });

        it('should set success status on successful login', async () => {
            const { result } = renderHook(() => useLoginForm());

            act(() => {
                result.current.updateField('email', 'test@example.com');
                result.current.updateField('password', 'secret123');
            });

            await act(async () => {
                await result.current.handleSubmit(makeEvent());
            });

            expect(result.current.status).toEqual({
                error: null,
                success: 'Login successful.',
                isSubmitting: false,
            });
        });

        it('should reset form state on successful login', async () => {
            const { result } = renderHook(() => useLoginForm());

            act(() => {
                result.current.updateField('email', 'test@example.com');
                result.current.updateField('password', 'secret123');
            });

            await act(async () => {
                await result.current.handleSubmit(makeEvent());
            });

            expect(result.current.formState).toEqual({ email: '', password: '' });
        });

        it('should redirect to /dashboard on successful login', async () => {
            const { result } = renderHook(() => useLoginForm());

            act(() => {
                result.current.updateField('email', 'test@example.com');
                result.current.updateField('password', 'secret123');
            });

            await act(async () => {
                await result.current.handleSubmit(makeEvent());
            });

            expect(mockPush).toHaveBeenCalledWith('/dashboard');
        });
    });
});