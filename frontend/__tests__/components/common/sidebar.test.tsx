import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import Sidebar from '../../../src/components/common/sidebar';

const mockUsePathname = jest.fn();

jest.mock('next/navigation', () => ({
	usePathname: () => mockUsePathname()
}));
