'use client';
import Input from '../ui/input';
import Dropdown from '../ui/dropdown';
import SliderBar from '../ui/sliderBar';
export default function CaseManagementBar() {
    return (
        <>
        <div className='grid grid-cols-3 gap-4 rounded-full font-semibold text-[var(--color-text)] p-4 mt-4'>
            <div>
                <Input placeholder="Search cases..." className='shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] pl-5 w-full py-2.5 rounded-full'/>
            </div>
            <div>
                <SliderBar filters={['All', 'Open', 'Closed']}  />
            </div>
            <div>
                <Dropdown options={[
                    {'label': 'Date Created', 'value': 'date_created'}, 
                    {'label': 'Last Updated', 'value': 'last_updated'}, 
                    {'label': 'Priority', 'value': 'priority'}]} className='shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] pl-5 ml-3 w-full py-3.5 rounded-full' optionClassName='shadow-[inset_0_0_8px_rgba(0,0,0,0.1)] rounded-full'/>
            </div>
        </div>
        </>
    );
}