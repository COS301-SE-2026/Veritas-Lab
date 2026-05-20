import Modal from "../ui/modal";
import Button from "../ui/button";
import Label from "../ui/label";
import Input from "../ui/input";
type DashboardModalProps = {
    isOpen: boolean;
    onClose: () => void;
};
export default function DashboardModal({ isOpen, onClose }: DashboardModalProps) {
    return (
        <Modal isOpen={isOpen} onClose={onClose}>
            <form>
                <div className="text-[24px] font-bold text-[#231F20] mb-4">Create New Case</div>
                <Label text="Case Title" htmlFor="caseTitle" className="mb-2 text-[16px] text-[#231F20]" />
                <Input id="caseTitle" type="text" placeholder="Enter case title" className="border border-gray-300 rounded-lg py-2 px-4 focus:outline-none focus:ring-2 focus:ring-[#3DBF79] mb-4 w-full text-[16px] text-[#231F20]" required />
                <Label text="Case Description" htmlFor="caseDescription" className="mb-2 text-[16px] text-[#231F20]" />
                <Input id="caseDescription" type="text" placeholder="Enter case description" className="border border-gray-300 rounded-lg py-10 px-4 focus:outline-none focus:ring-2 focus:ring-[#3DBF79] mb-4 w-full text-[16px] text-[#231F20]" required />
                <div className="flex justify-end">
                    <Button variant="sadSack" onClick={onClose} className="mr-2">
                        <div className="text-[16px] font-bold">Cancel</div>
                    </Button>  
                    <Button variant="submit" type="submit" onClick={onClose}>
                        <div className="text-[16px] font-bold">Create Case</div>
                    </Button>
                </div>
            </form>
        </Modal>
    );
}