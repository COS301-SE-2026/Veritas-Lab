import type { Node, Edge } from '@xyflow/react';
import type { CaseEvidence } from '@/types/api';
import type { EvidenceNodeData } from '@/components/common/evidenceNode';
import type { NoteNodeData } from '@/components/common/noteNode';
import type { CaseEdgeData } from '@/components/common/customEdge';
import { format, formatDistanceStrict } from 'date-fns';
import {
    getEvidenceFacts,
    hasBoardFacts,
    distanceKm,
    formatKm,
    formatCoordinates,
    describeLocation,
    type EvidenceFacts,
    type GeoPoint,
} from '@/lib/data/evidenceMetadata';

export const evidenceNodeId = (mediaId: string) => `evidence-${mediaId}`;

export const toEvidenceNode = (
    evidence: CaseEvidence,
    position: { x: number; y: number },
    facts: EvidenceFacts = getEvidenceFacts(evidence.reportArtifacts),
): Node<EvidenceNodeData> => {
    const location = describeLocation(facts);
    return {
        id: evidenceNodeId(evidence.mediaId),
        type: 'evidence',
        position,
        data: {
            mediaId: evidence.mediaId,
            mediaName: evidence.casePerspective,
            mediaUrl: evidence.mediaUrl,
            mediaExtension: evidence.mediaExtension,
            reportCertainty: evidence.reportCertainty,
            annotationCount: evidence.annotations?.length ?? 0,
            capturedAt: facts.capturedAt,
            device: facts.device,
            location: location?.label ?? null,
            locationTitle: location?.title ?? null,
            editNote: facts.editNote,
        },
    };
};

const colWidth = 440;
const rowHeight = 420;
const perRow = 6;
const laneGap = 140;
const laneLabelX = -320;

const SAME_PLACE_KM = 0.2;
const MIN_CONFLICT_KM = 1;
const MAX_PLAUSIBLE_KMH = 250;

type Item = { evidence: CaseEvidence; facts: EvidenceFacts };
type Lane = { items: Item[]; centre: GeoPoint | null };

const byTime = (a: Item, b: Item) => {
    const ta = a.facts.capturedAt;
    const tb = b.facts.capturedAt;
    if (ta == null && tb == null) return 0;
    if (ta == null) return 1;
    if (tb == null) return -1;
    return ta - tb;
};

// Group evidence into lanes by where it was captured. Items arrive in time order,
// so lanes end up ordered by when each place first appears.
function groupByLocation(items: Item[]): Lane[] {
    const lanes: Lane[] = [];
    const unknown: Lane = { items: [], centre: null };

    for (const item of items) {
        const point = item.facts.location;
        if (!point) {
            unknown.items.push(item);
            continue;
        }
        const lane = lanes.find((l) => l.centre && distanceKm(l.centre, point) <= SAME_PLACE_KM);
        if (lane && lane.centre) {
            const n = lane.items.length;
            lane.centre = {
                lat: (lane.centre.lat * n + point.lat) / (n + 1),
                lon: (lane.centre.lon * n + point.lon) / (n + 1),
            };
            lane.items.push(item);
        } else {
            lanes.push({ items: [item], centre: { lat: point.lat, lon: point.lon } });
        }
    }
    return unknown.items.length ? [...lanes, unknown] : lanes;
}

function laneLabel(lane: Lane, index: number): string {
    const count = `${lane.items.length} item${lane.items.length === 1 ? '' : 's'}`;
    if (!lane.centre) return `No location data\n${count}`;

    const place = lane.items.map((i) => i.facts.place).find(Boolean);
    const times = lane.items.map((i) => i.facts.capturedAt).filter((t): t is number => t != null);
    let span = '';
    if (times.length) {
        const first = Math.min(...times);
        const last = Math.max(...times);
        span = first === last
            ? format(first, 'd MMM yyyy, HH:mm')
            : format(first, 'yyyy-MM-dd') === format(last, 'yyyy-MM-dd')
                ? `${format(first, 'd MMM yyyy, HH:mm')} - ${format(last, 'HH:mm')}`
                : `${format(first, 'd MMM, HH:mm')} - ${format(last, 'd MMM yyyy, HH:mm')}`;
    }

    return [
        `Location ${String.fromCharCode(65 + (index % 26))}${place ? ` - ${place}` : ''}`,
        formatCoordinates(lane.centre),
        count,
        span,
    ].filter(Boolean).join('\n');
}

// Build the board from evidence metadata
export function generateBoard(evidenceList: CaseEvidence[], facts?: EvidenceFacts[]) {
    const items: Item[] = evidenceList
        .map((evidence, i) => ({ evidence, facts: facts?.[i] ?? getEvidenceFacts(evidence.reportArtifacts) }))
        .filter((item) => hasBoardFacts(item.facts))
        .sort(byTime);

    const lanes = groupByLocation(items);
    const showLaneLabels = lanes.some((lane) => lane.centre);

    const nodes: Node[] = [];
    let laneTop = 0;
    lanes.forEach((lane, laneIndex) => {
        if (showLaneLabels) {
            nodes.push({
                id: `note-lane-${laneIndex}`,
                type: 'note',
                position: { x: laneLabelX, y: laneTop },
                data: { text: laneLabel(lane, laneIndex), author: 'Board generator' } satisfies NoteNodeData,
            });
        }
        lane.items.forEach(({ evidence, facts: itemFacts }, i) => {
            nodes.push(toEvidenceNode(
                evidence,
                { x: (i % perRow) * colWidth, y: laneTop + Math.floor(i / perRow) * rowHeight },
                itemFacts,
            ));
        });
        laneTop += Math.ceil(lane.items.length / perRow) * rowHeight + laneGap;
    });

    const edges: Edge<CaseEdgeData>[] = [];
    const linked = new Set<string>();
    const pairKey = (a: string, b: string) => [a, b].sort().join('|');

    const dated = items.filter((item) => item.facts.capturedAt != null);
    for (let k = 1; k < dated.length; k++) {
        const prev = dated[k - 1];
        const next = dated[k];
        const t0 = prev.facts.capturedAt!;
        const t1 = next.facts.capturedAt!;
        const parts = [`+${formatDistanceStrict(t0, t1)}`];
        let variant: CaseEdgeData['variant'] = 'timeline';

        if (prev.facts.location && next.facts.location) {
            const km = distanceKm(prev.facts.location, next.facts.location);
            if (km >= 0.05) parts.push(formatKm(km));
            const hours = (t1 - t0) / 3_600_000;
            if (km >= MIN_CONFLICT_KM && (hours <= 0 || km / hours > MAX_PLAUSIBLE_KMH)) {
                variant = 'conflict';
                parts.unshift('Implausible travel');
            }
        }

        edges.push({
            id: `timeline:${prev.evidence.mediaId}:${next.evidence.mediaId}`,
            source: evidenceNodeId(prev.evidence.mediaId),
            target: evidenceNodeId(next.evidence.mediaId),
            type: 'custom-edge',
            data: { variant, label: parts.join(' · ') },
        });
        linked.add(pairKey(prev.evidence.mediaId, next.evidence.mediaId));
    }

    const byDevice = new Map<string, Item[]>();
    for (const item of items) {
        if (!item.facts.deviceKey) continue;
        byDevice.set(item.facts.deviceKey, [...(byDevice.get(item.facts.deviceKey) ?? []), item]);
    }
    for (const group of byDevice.values()) {
        for (let k = 1; k < group.length; k++) {
            const a = group[k - 1].evidence.mediaId;
            const b = group[k].evidence.mediaId;
            if (linked.has(pairKey(a, b))) continue;
            edges.push({
                id: `device:${a}:${b}`,
                source: evidenceNodeId(a),
                target: evidenceNodeId(b),
                type: 'custom-edge',
                data: { variant: 'device', label: `Same device · ${group[k].facts.device}` },
            });
            linked.add(pairKey(a, b));
        }
    }

    return { nodes, edges };
}