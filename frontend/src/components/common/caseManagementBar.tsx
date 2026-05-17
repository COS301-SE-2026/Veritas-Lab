'use client';
import Input from '../ui/input';
import Dropdown from '../ui/dropdown';
export default function CaseManagementBar() {
    return (
        <>
        <div className='grid grid-cols-3 gap-4 rounded-full bg-[#3DBF79] border-2 p-4 mt-4'>
            <div>
                <Input placeholder="Search cases..." />
            </div>
            <div>
                <Dropdown options={[
                    {'label': 'All Cases', 'value': 'all'}, 
                    {'label': 'Open Cases', 'value': 'open'}, 
                    {'label': 'Closed Cases', 'value': 'closed'}]} />
            </div>
            <div>
                <Dropdown options={[
                    {'label': 'Date Created', 'value': 'date_created'}, 
                    {'label': 'Last Updated', 'value': 'last_updated'}, 
                    {'label': 'Priority', 'value': 'priority'}]} />
            </div>
        </div>
        </>
    );
}