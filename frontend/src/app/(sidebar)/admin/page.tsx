'use client';
import { useEffect, useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useUserRole } from '@/context/UserRoleContext';
import AdminUserSearchBar from '@/components/common/adminUserSearchBar';
import AdminUsersPanel from '@/components/common/adminUsersPanel';
import AdminDeleteModal from '@/components/common/adminDeleteModal';
import useAdminUsers from '@/lib/hooks/useAdminUsers';
import type { AdminUser } from '@/types/api';
