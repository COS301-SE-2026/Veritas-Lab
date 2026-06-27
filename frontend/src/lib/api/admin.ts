const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

import type { AdminUser } from '@/types/api';

type ApiResult = {
    status?: 'success' | 'error';
    message?: string;
};