import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import LoginForm from '@/components/common/loginForm';
import RegisterForm from '@/components/common/registerForm';
import { login } from '@/lib/api/login';
import { register } from '@/lib/api/register';
import type { LoginResponse, RegisterResponse } from '@/types/api';
//mock the backend(api) and then we test all the actual frontend features integrating
jest.mock('@/lib/api/login', () => ({
    login: jest.fn(),
}));
jest.mock('@/lib/api/register', () => ({
    register: jest.fn(),
}));

const mockPush = jest.fn();
const mockReplace = jest.fn();
const mockRefresh = jest.fn();
jest.mock('next/navigation', () => ({
    useRouter: () => ({
        push: mockPush,
        replace: mockReplace,
        refresh: mockRefresh,
    }),
}));


describe('LoginForm (integration)', () => {
    const mockedLogin = login as jest.MockedFunction<typeof login>;

    beforeEach(() => {
        mockedLogin.mockReset();
        mockPush.mockClear();
        mockReplace.mockClear();
        mockRefresh.mockClear();
    });
    //test login functionality
    const fillAndSubmit = (email: string, password: string) => {
        fireEvent.change(screen.getByLabelText('Email'), { target: { value: email } });
        fireEvent.change(screen.getByLabelText('Password'), { target: { value: password } });
        fireEvent.click(screen.getByRole('button', { name: /login/i }));
    };
    //test button rendering
    it('renders the login form controls', () => {
        render(<LoginForm />);
        expect(screen.getByLabelText('Email')).toBeInTheDocument();
        expect(screen.getByLabelText('Password')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Login' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Create an account' })).toBeInTheDocument();
    });

    //invalid entry tests
    it('blocks submission and shows a validation error for invalid email', () => {
        render(<LoginForm />);
        fillAndSubmit('not-an-email', 'somepassword');
        expect(screen.getByRole('alert')).toHaveTextContent('Please enter a valid email.');//this will have to be reviewed after the error message changes
        expect(mockedLogin).not.toHaveBeenCalled();
    });
    it('blocks submission and shows a validation error for missing password', () => {
        render(<LoginForm />);
        fillAndSubmit('user@example.com', '   ');
        expect(screen.getByRole('alert')).toHaveTextContent('Please enter your password.');
        expect(mockedLogin).not.toHaveBeenCalled();
    });
    //
    it('logs in successfully shows success message and redirects to dashboard', async () => {
        mockedLogin.mockResolvedValue({ status: 'success', message: 'Login successful.' } as LoginResponse);
        render(<LoginForm />);
        fillAndSubmit('  user@example.com  ', 'correct-password');
        expect(mockedLogin).toHaveBeenCalledWith('user@example.com', 'correct-password');
        await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Login successful.'));
        await waitFor(() => expect(mockPush).toHaveBeenCalledWith('/dashboard'));
        expect(screen.getByLabelText('Email')).toHaveValue('');
        expect(screen.getByLabelText('Password')).toHaveValue('');
    });
    //error message tests (we will need to redo these after error message changes)
    it('shows the server provided error message when login fails without throwing', async () => {
        mockedLogin.mockResolvedValue({ status: 'error', message: 'Invalid credentials.' } as LoginResponse);
        render(<LoginForm />);
        fillAndSubmit('user@example.com', 'wrong-password');
        expect(await screen.findByRole('alert')).toHaveTextContent('Invalid credentials.');
        expect(mockPush).not.toHaveBeenCalled();
    });
    it('shows fallback error message when login rejects', async () => {
        mockedLogin.mockRejectedValue(new Error('Unable to reach the server. Please try again later.'));
        render(<LoginForm />);
        fillAndSubmit('user@example.com', 'correct-password');
        expect(await screen.findByRole('alert')).toHaveTextContent('Unable to reach the server. Please try again later.');
        expect(mockPush).not.toHaveBeenCalled();
    });
    //test loading
    it('disables the submit button and shows a loading label when submitting', async () => {
        let resolveLogin!: (value: LoginResponse) => void;
        const pendingLogin = new Promise<LoginResponse>((resolve) => {
            resolveLogin = resolve;
        });
        mockedLogin.mockReturnValue(pendingLogin);
        render(<LoginForm />);
        fillAndSubmit('user@example.com', 'correct-password');
        expect(await screen.findByRole('button', { name: 'Logging in...' })).toBeDisabled();
        await act(async () => {
            resolveLogin({ status: 'success', message: 'Login successful.' } as LoginResponse);
            await pendingLogin;
        });
    });
    //test register nav
    it('navigates to the register page from the create an account button', () => {
        render(<LoginForm />);
        fireEvent.click(screen.getByRole('button', { name: 'Create an account' }));
        expect(mockPush).toHaveBeenCalledWith('/register');
        expect(mockedLogin).not.toHaveBeenCalled();
    });
});

//ok now we attempt register :( (i hate testing)
describe('RegisterForm (integration)', () => {
    const mockedRegister = register as jest.MockedFunction<typeof register>;
    const validPassword = 'StrongPass1!';

    beforeEach(() => {
        mockedRegister.mockReset();
        mockPush.mockClear();
        mockReplace.mockClear();
        mockRefresh.mockClear();
    });
    //test register functionality
    const fillFields = ({
        username = 'adam.g',
        email = 'adam@example.com',
        password = validPassword,
        confirmPassword = validPassword,
    }: Partial<Record<'username' | 'email' | 'password' | 'confirmPassword', string>> = {}) => {
        fireEvent.change(screen.getByLabelText('Username'), { target: { value: username } });
        fireEvent.change(screen.getByLabelText('Work Email'), { target: { value: email } });
        fireEvent.change(screen.getByLabelText('Password'), { target: { value: password } });
        fireEvent.change(screen.getByLabelText('Confirm Password'), { target: { value: confirmPassword } });
    };
    const submit = () => fireEvent.click(screen.getByRole('button', { name: /create account/i }));
    //test rendering
    it('renders the register form controls', () => {
        render(<RegisterForm />);
        expect(screen.getByLabelText('Username')).toBeInTheDocument();
        expect(screen.getByLabelText('Work Email')).toBeInTheDocument();
        expect(screen.getByLabelText('Password')).toBeInTheDocument();
        expect(screen.getByLabelText('Confirm Password')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Create Account' })).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Sign In' })).toBeInTheDocument();
    });
    //test validation in form
    it('shows an inline hint as soon as the confirmation password differs', () => {
        render(<RegisterForm />);
        fillFields({ confirmPassword: `${validPassword}x` });
        expect(screen.getByText("Passwords don't match.")).toBeInTheDocument();
    });
    it('blocks submission when the username is missing', () => {
        render(<RegisterForm />);
        fillFields({ username: '   ' });
        submit();
        expect(screen.getByRole('alert')).toHaveTextContent('Please enter a username.');
        expect(mockedRegister).not.toHaveBeenCalled();
    });
    it('blocks submission for an invalid email', () => {
        render(<RegisterForm />);
        fillFields({ email: 'not-an-email' });
        submit();
        expect(screen.getByRole('alert')).toHaveTextContent('Please enter a valid work email.');
        expect(mockedRegister).not.toHaveBeenCalled();
    });
    it('blocks submission for a password that fails the strength requirements', () => {
        render(<RegisterForm />);
        fillFields({ password: 'weakpassword', confirmPassword: 'weakpassword' });
        submit();
        expect(screen.getByRole('alert')).toHaveTextContent(
            'Password must be atleast 12 characters, have an upper and lower case character and a special character'
        );
        expect(mockedRegister).not.toHaveBeenCalled();
    });
    it('blocks submission when passwords do not match', () => {
        render(<RegisterForm />);
        fillFields({ confirmPassword: `${validPassword}x` });
        submit();
        expect(screen.getByRole('alert')).toHaveTextContent('Passwords do not match.');
        expect(mockedRegister).not.toHaveBeenCalled();
    });
    //success test
    it('registers successfully shows success message and redirects to dashboard', async () => {
        mockedRegister.mockResolvedValue({ status: 'success', message: 'Account created successfully.' } as RegisterResponse);
        render(<RegisterForm />);
        fillFields();
        submit();
        expect(mockedRegister).toHaveBeenCalledWith('adam.g', 'adam@example.com', validPassword);
        await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Account created successfully.'));
        await waitFor(() => expect(mockReplace).toHaveBeenCalledWith('/dashboard'));
        expect(screen.getByLabelText('Username')).toHaveValue('');
    });
    //error tests
    it('shows server provided error message when registration fails without throwing', async () => {
        mockedRegister.mockResolvedValue({ status: 'error', message: 'Email already in use.' } as RegisterResponse);
        render(<RegisterForm />);
        fillFields();
        submit();
        expect(await screen.findByRole('alert')).toHaveTextContent('Email already in use.');
        expect(mockReplace).not.toHaveBeenCalled();
    });
    it('shows fallback error message when registration rejects', async () => {
        mockedRegister.mockRejectedValue(new Error('Unable to reach the server. Please try again later.'));
        render(<RegisterForm />);
        fillFields();
        submit();
        expect(await screen.findByRole('alert')).toHaveTextContent('Unable to reach the server. Please try again later.');
        expect(mockReplace).not.toHaveBeenCalled();
    });
    //loading test
    it('disables the submit button and shows loading label when submitting', async () => {
        let resolveRegister!: (value: RegisterResponse) => void;
        const pendingRegister = new Promise<RegisterResponse>((resolve) => {
            resolveRegister = resolve;
        });
        mockedRegister.mockReturnValue(pendingRegister);
        render(<RegisterForm />);
        fillFields();
        submit();
        expect(await screen.findByRole('button', { name: 'Creating Account...' })).toBeDisabled();
        await act(async () => {
            resolveRegister({ status: 'success', message: 'Account created successfully.' } as RegisterResponse);
            await pendingRegister;
        });
    });
    //test nav to login
    it('navigates to the login page from the sign in button', () => {
        render(<RegisterForm />);
        fireEvent.click(screen.getByRole('button', { name: 'Sign In' }));
        expect(mockPush).toHaveBeenCalledWith('/login');
        expect(mockedRegister).not.toHaveBeenCalled();
    });
});