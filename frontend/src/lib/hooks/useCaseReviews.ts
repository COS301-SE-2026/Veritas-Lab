'use client'; //hook for case comments
import { useEffect, useState } from 'react';
import { addComment } from '@/lib/api/case';
import type { CaseComment } from '@/types/api';

type UseCaseReviewsOptions = {
    caseId: string;
    initialComments: CaseComment[];
};