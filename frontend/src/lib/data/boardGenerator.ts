import type { Node, Edge } from '@xyflow/react';
import type { CaseEvidence } from '@/types/api';
import type { EvidenceNodeData } from '@/components/common/evidenceNode';
import { formatDistanceStrict } from 'date-fns';

export const evidenceNodeId = (mediaId: string) => `evidence-${mediaId}`;

export const toEvidenceNode = (evidence: CaseEvidence, position: { x: number; y: number}) : Node<EvidenceNodeData> => ({
    id: evidenceNodeId(evidence.mediaId),
    type: 'evidence',
    position,
    data: {
        mediaId: evidence.mediaId,
        mediaName: evidence.mediaName,
        mediaUrl: evidence.mediaUrl,
        mediaExtension: evidence.mediaExtension,
        reportCertainty: evidence.reportCertainty,
        annotationCount: evidence.annotations?.length ?? 0,
    }
});

const colWidth = 440
const rowHeight = 400
const perRow = 6
//make the nodes and edges of the timestamped evidence
export function generateBoard(evidenceList: CaseEvidence[], capturedAt: (number | null)[]) {
    const dated = evidenceList
        .map((evidence, i) => ({ evidence, time: capturedAt[i] }))
        .filter((date): date is { evidence: CaseEvidence; time: number } => date.time != null)
        .sort((a, b) => a.time - b.time);

    const nodes = dated.map(({ evidence }, i) => toEvidenceNode(evidence, { x: (i % perRow) * colWidth, y: Math.floor(i / perRow) * rowHeight }))

    const edges: Edge[] = dated.slice(1).map(({ evidence, time }, i) => ({
        id: `timeline:${dated[i].evidence.mediaId}:${evidence.mediaId}`,
        source: evidenceNodeId(dated[i].evidence.mediaId),
        target: evidenceNodeId(evidence.mediaId),
        type: 'custom-edge',
        data: { variant: 'timeline', label: `+${formatDistanceStrict(dated[i].time, time)}` },
    }))

    return { nodes, edges }
}