const APIURL = process.env.APIURL;

export default function useCase() {
    const fetchCases = async (caseID: string) => {
        try {
            const res = await fetch(`${APIURL}/cases/${caseID}`);
            if (!res.ok) {
                throw new Error(`Failed to fetch case with ID ${caseID}`);
            }
            const data = await res.json();
            return data;
        } catch (error) {
            console.error(`Error fetching case with ID ${caseID}:`, error);
            throw error;
        }
    }
    const addEvidence = async (evidence: File) => {
        // All this will be moved to the API folder and called here later

        // For now I assume we'll need an upload link since we are using minio 
        let link: string;
        try {

            const uploadLink = await fetch(`${APIURL}/evidence/upload-link`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(evidence)
            });
            link = await uploadLink.json();
        } catch (error) {
            console.error('Error generating evidence upload link:', error);
            throw error;
        }
        // Upload the evidence to the provided link
        try {
            const res = await fetch(link, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/octet-stream'
                },
                body: evidence
            });
            if (!res.ok) {
                throw new Error('Failed to add evidence');
            }
        } catch (error) {
            console.error('Error adding evidence file to Minio:', error);
            throw error;
        }
        // After successfully uploading the evidence, we need to add its metadata to the database including the link to the file in minio
        try {
            const res = await fetch(`${APIURL}/evidence`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ ...evidence, bucket: link , extension: evidence.type, name: evidence.name })
            });
            if (!res.ok) {
                throw new Error('Failed to add evidence metadata');
            }
        } catch (error) {
            console.error('Error adding evidence:', error);
            throw error;
        }
        return;
    }
    return {
        fetchCases,
        addEvidence
    }
}