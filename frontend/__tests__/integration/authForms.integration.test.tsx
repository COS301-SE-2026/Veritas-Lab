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