export type CertaintyMeta = {
    label: string;
    description: string;
    colorVar: string;
};

const certValue: Record<number, CertaintyMeta> = {
    0: {
        label: 'Unknown',
        description: 'The risk of this evidence is not known as its type is not supported for analysis yet.',
        colorVar: '#e0a92e',
    },
    1: {
        label: 'Low Risk',
        description: 'No significant signs of tampering or manipulation were found.',
        colorVar: '#3dbf79',
    },
    2: {
        label: 'Medium Risk',
        description: 'Some signs of editing or processing were found.',
        colorVar: '#d97706',
    },
    3: {
        label: 'High Risk',
        description: 'Strong evidence this media has been manipulated or generated.',
        colorVar: '#e53e3e',
    },
};

const defValue: CertaintyMeta = {
    label: 'Not Analysed',
    description: 'This piece of evidence has not been analysed yet.',
    colorVar: '#2b6cb0',
};

export function getCertaintyMeta(certainty: number | null | undefined): CertaintyMeta {
    if (certainty === null || certainty === undefined) {
        return defValue;
    }
    return certValue[certainty] ?? defValue;
}