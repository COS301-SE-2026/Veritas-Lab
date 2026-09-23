'use client';
import { useState } from 'react';
import { UserPlus, UserMinus } from 'lucide-react';
import Modal from '@/components/ui/modal';
import Button from '@/components/ui/button';
import { assignCase, unassignCase } from '@/lib/api/dashboard';
import type { CaseAssignButtonProps } from '@/types/components';
import Label from '../ui/label';
//button component with simialt styling