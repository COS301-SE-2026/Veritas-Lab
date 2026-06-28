'use client';
import { useEffect, useMemo, useRef, useState } from 'react';
import { changeUserRole, deleteUser, fetchUsers } from '@/lib/api/admin';
import type { AdminUser } from '@/types/api';
export type AdminRoleFilter = 'All' | AdminUser['role'];
export type AdminSortKey = 'id' | 'displayName' | 'username' | 'role';
//hook for managing all admin related tasks