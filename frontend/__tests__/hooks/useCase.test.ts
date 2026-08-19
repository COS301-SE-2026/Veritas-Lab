import { renderHook } from '@testing-library/react';
import useCase from '../../src/lib/hooks/useCase';
import { addEvidence, closeCase, fetchCase, deleteEvidence } from '../../src/lib/api/case';

jest.mock('../../src/lib/api/case', () => ({
	fetchCase: jest.fn(),
	addEvidence: jest.fn(),
	closeCase: jest.fn(),
	deleteEvidence: jest.fn(), //hook tests for delete evidence 
}));

describe('useCase', () => {
	it('exposes case helpers', () => {
		const { result } = renderHook(() => useCase());
		expect(result.current.fetchCase).toBe(result.current.fetchCases);
		expect(typeof result.current.fetchCase).toBe('function');
		expect(typeof result.current.addEvidence).toBe('function');
		expect(typeof result.current.closeCase).toBe('function');
		expect(typeof result.current.deleteEvidence).toBe('function');
	});

	it('calls the case API helpers', async () => {
		const mockedFetchCase = fetchCase as jest.MockedFunction<typeof fetchCase>;
		const mockedAddEvidence = addEvidence as jest.MockedFunction<typeof addEvidence>;
		const mockedCloseCase = closeCase as jest.MockedFunction<typeof closeCase>;
		const mockedDeleteEvidence = deleteEvidence as jest.MockedFunction<typeof deleteEvidence>;
		const file = new File(['evidence'], 'evidence.pdf', { type: 'application/pdf' });

		mockedFetchCase.mockResolvedValue({
			status: 'success',
			case: {
				caseId: 'case-1',
				caseName: 'Example Case',
				caseCreator: 'investigator.one',
				caseReviews: null,
				caseDescription: null,
				caseClosed: false,
				caseCreationDate: '2026-05-01T09:00:00.000Z',
			},
			evidence: [],
		} as Awaited<ReturnType<typeof fetchCase>>);
		mockedCloseCase.mockResolvedValue({ status: 'success' });
		mockedDeleteEvidence.mockResolvedValue({ status: 'success' });
		const { result } = renderHook(() => useCase());
		await result.current.fetchCase('case-1');
		await result.current.addEvidence(file, 'case-1');
		await result.current.closeCase('case-1');
		await result.current.deleteEvidence('case-1', 'media-1');
		expect(mockedFetchCase).toHaveBeenCalledWith('case-1');
		expect(mockedAddEvidence).toHaveBeenCalledWith(file, 'case-1');
		expect(mockedCloseCase).toHaveBeenCalledWith('case-1');
		expect(mockedDeleteEvidence).toHaveBeenCalledWith('case-1', 'media-1');
	});
});