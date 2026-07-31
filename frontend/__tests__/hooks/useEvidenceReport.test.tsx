import { renderHook, act } from '@testing-library/react';
import useReportModal from '@/lib/hooks/useEvidenceReport';
//hook tests will be for the isOpen or closed for the modal
describe('useReportModal', () => {
    it('starts with the report closed', () => {
        const { result } = renderHook(() => useReportModal());
        expect(result.current.isReportOpen).toBe(false);
    });

    it('opens the report when openReport is called', () => {
        const { result } = renderHook(() => useReportModal());
        act(() => {
            result.current.openReport();
        });
        expect(result.current.isReportOpen).toBe(true);
    });

    it('closes the report when closeReport is called', () => {
        const { result } = renderHook(() => useReportModal());
        act(() => {
            result.current.openReport();
        });
        act(() => {
            result.current.closeReport();
        });
        expect(result.current.isReportOpen).toBe(false);
    });

    it('stays closed if closeReport is called before opening', () => {
        const { result } = renderHook(() => useReportModal());
        act(() => {
            result.current.closeReport();
        });
        expect(result.current.isReportOpen).toBe(false);
    });
});