import { fireEvent, render, screen } from '@testing-library/react';
import AdminUserCard from '@/components/common/adminUserCard';
import type { AdminUser } from '@/types/api';

const sampleUser: AdminUser = {
    id: '123e4567-e89b-12d3-a456-426614174000',
    username: 'jane.doe',
    role: 'USER',
};
// jest testing for the admin user card: