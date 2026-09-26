import { ClassificationResult, ModelConfig } from '@/lib/ai';

export default function PlugAndPlayReport({ results, modelName, fileName, config, date }: { results: ClassificationResult, modelName: string, fileName: string, config: ModelConfig, date: string }) {
    const probability = results.aiProbability;
    const percentage = (probability * 100).toFixed(2);
    const certainty = () => {
        if (probability >= 0.8) {
            return 3
        } else if (probability >= 0.6) {
            return 2;
        } else {
            return 1;
        }
    }

    function getFindings() {
        switch (certainty()) {
            case 1:
                return {
                    report: `The AI model ${modelName} has analyzed the file ${fileName} ` +
                        `and determined that it is ${results.classification} with a probability of ${percentage}%. ` +
                        `The ai has low confidence in this result.`
                };
            case 2:
                return {
                    report: `The AI model ${modelName} has analyzed the file ${fileName} ` +
                        `and determined that it is ${results.classification} with a probability of ${percentage}%. ` +
                        `The ai has moderate confidence in this result.`
                };
            case 3:
                return {
                    report: `The AI model ${modelName} has analyzed the file ${fileName} ` +
                        `and determined that it is ${results.classification} with a probability of ${percentage}%. ` +
                        `The ai has high confidence in this result.`
                };
        }
    }

    return (
        <>
           
        </>
    )

}