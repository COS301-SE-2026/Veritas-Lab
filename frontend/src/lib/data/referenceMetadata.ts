export type ExampleMediaKind = 'image' | 'pdf'; //add more when we support more file types
export const badExampleData: Record<ExampleMediaKind, Record<string, string>> = {
    image: {
        'JUMBF:ActionsSoftwareAgentName': 'gpt-image',
        'JUMBF:Claim_Generator_InfoName': 'OpenAI Media Service API',
        'JUMBF:ActionsSoftwareAgentVersion': 'pre-2.0',
        'JUMBF:Claim_Generator_InfoIconUrl': 'self#jumbf=c2pa.assertions/c2pa.icon',
        'JUMBF:Claim_Generator_InfoIconHash': '(Binary data 32 bytes)',
        'JUMBF:Claim_Generator_InfoSpecVersion': '2.2.0',
        'JUMBF:Claim_Generator_InfoOrgContentauthC2Pa_Rs': '0.79.2',
        'PNG:Filter': '0',
        'SourceFile': '/tmp/tmpt5ewpcac/2756df74-e60a-46db-94b5-0c0ba6838ca7.png',
        'PNG:BitDepth': '8',
        'PNG:ColorType': '2',
        'PNG:Interlace': '0',
        'PNG:Compression': '0',
        'PNG:ImageWidth': '1536',
        'PNG:ImageHeight': '1024',
        'Composite:ImageSize': '1536 1024',
        'Composite:Megapixels': '1.572864',
        'File:FileName': '2756df74-e60a-46db-94b5-0c0ba6838ca7.png',
        'File:FileSize': '2570521',
        'File:FileType': 'PNG',
        'File:MIMEType': 'image/png',
        'File:Directory': '/tmp/tmpt5ewpcac',
        'File:FileAccessDate': '2026:07:29 12:33:01+00:00',
        'File:FileModifyDate': '2026:07:29 12:33:01+00:00',
        'File:FilePermissions': '100644',
    },
    pdf: {
        'PDF:Producer': 'PDFman123',
        'PDF:Creator': 'windows',
        'PDF:ModifyDate': '2025:11:02 14:12:03',
        'PDF:CreateDate': '',
        'PDF:Author': 'unknown',
    },
};
 
export const exampleLabels: Record<ExampleMediaKind, string> = {
    image: 'Known bad example (image)',
    pdf: 'Known bad example (PDF)',
};