import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import CheckBox from '../../../src/components/ui/checkbox';

const mockOnChange = jest.fn();
