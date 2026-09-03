import { renderHook, act } from '@testing-library/react';
import useChangePasswordForm from '@/lib/hooks/useChangePasswordForm';
import { changePassword } from '@/lib/api/changePassword';
jest.mock('@/lib/api/changePassword', () => ({
    changePassword: jest.fn(),
}));
//change password hook tests :()
describe('useChangePasswordForm', () => {
    const makeEvent = () =>
        ({ preventDefault: jest.fn() } as unknown as React.SubmitEvent<HTMLFormElement>);
    const fillValidForm = (result: any) => {
        act(() => {
            result.current.updateField('currentPassword', 'OldPassword!123');
            result.current.updateField('newPassword', 'NewPassword!123');
            result.current.updateField('confirmNewPassword', 'NewPassword!123');
        });
    };
    beforeEach(() => {
        jest.clearAllMocks();
    });
    // form fields allow input
    it('updates form fields', () => {
        const { result } = renderHook(() => useChangePasswordForm());
        act(() => {
            result.current.updateField('currentPassword', 'OldPassword!123');
            result.current.updateField('newPassword', 'NewPassword!123');
            result.current.updateField('confirmNewPassword', 'NewPassword!123');
        });
        expect(result.current.formState).toEqual({
            currentPassword: 'OldPassword!123',
            newPassword: 'NewPassword!123',
            confirmNewPassword: 'NewPassword!123',
        });
    });

    //going to try out cool new way i found for testing multiple of the same entries for different data
    it.each([
        ['missing current password', '', 'NewPassword!123', 'NewPassword!123',
            'Please enter your current password.'],
        ['weak new password', 'OldPassword!123', 'weak', 'weak',
            'New password must be atleast 12 characters, have an upper and lower case character and a special character'],
        ['mismatched passwords', 'OldPassword!123', 'NewPassword!123', 'Different!123',
            'New passwords do not match.'],
        ['same password', 'SamePassword!123', 'SamePassword!123', 'SamePassword!123',
            'New password must be different from your current password.'],
    ])('rejects %s', async (_, current, newPassword, confirm, expected) => {
        const { result } = renderHook(() => useChangePasswordForm());
        act(() => {
            result.current.updateField('currentPassword', current);
            result.current.updateField('newPassword', newPassword);
            result.current.updateField('confirmNewPassword', confirm);
        });
        await act(async () => {
            await result.current.handleSubmit(makeEvent());
        });
        expect(result.current.status.error).toBe(expected);
        expect(changePassword).not.toHaveBeenCalled();
    });
    //sucess tests
    it('submits successfully and resets the form and calls onSuccess', async () => {
        const onSuccess = jest.fn();
        (changePassword as jest.Mock).mockResolvedValue({
            message: 'Password changed successfully',
        });
        const { result } = renderHook(() => useChangePasswordForm(onSuccess));
        fillValidForm(result);
        await act(async () => {
            await result.current.handleSubmit(makeEvent());
        });
        expect(changePassword).toHaveBeenCalledWith(
            'OldPassword!123',
            'NewPassword!123'
        );
        expect(result.current.status).toEqual({
            error: null,
            success: 'Password changed successfully',
            isSubmitting: false,
        });
        expect(result.current.formState).toEqual({
            currentPassword: '',
            newPassword: '',
            confirmNewPassword: '',
        });
        expect(onSuccess).toHaveBeenCalledTimes(1);
    });
    it('uses the default success message when the API does not provide one', async () => {
        (changePassword as jest.Mock).mockResolvedValue({});
        const { result } = renderHook(() => useChangePasswordForm());
        fillValidForm(result);
        await act(async () => {
            await result.current.handleSubmit(makeEvent());
        });
        expect(result.current.status.success).toBe(
            'Password changed successfully.'
        );
    });
    //errors handling
    it('handles an Error from the API', async () => {
        (changePassword as jest.Mock).mockRejectedValue(
            new Error('Current password is incorrect.')
        );
        const { result } = renderHook(() => useChangePasswordForm());
        fillValidForm(result);
        await act(async () => {
            await result.current.handleSubmit(makeEvent());
        });
        expect(result.current.status.error).toBe(
            'Current password is incorrect.'
        );
        expect(result.current.status.isSubmitting).toBe(false);
    });
    it('handles a non Error API failure', async () => {
        (changePassword as jest.Mock).mockRejectedValue('offline');
        const { result } = renderHook(() => useChangePasswordForm());
        fillValidForm(result);
        await act(async () => {
            await result.current.handleSubmit(makeEvent());
        });
        expect(result.current.status.error).toBe(
            'Unable to reach the server. Please try again later.'
        );
    });
});
//yay 100 percent coverage achieved