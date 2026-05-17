import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import RegisterForm from '../../../src/components/common/registerForm';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
	useRouter: () => ({
		push: mockPush
	})
}));
