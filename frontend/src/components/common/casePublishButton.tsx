'use client';
import { useState } from 'react';
import { Send } from 'lucide-react';
import Modal from '@/components/ui/modal';
import Button from '@/components/ui/button';
import useCase from '@/lib/hooks/useCase';
import type { CasePublishButtonProps } from '@/types/components';
import Label from '../ui/label';