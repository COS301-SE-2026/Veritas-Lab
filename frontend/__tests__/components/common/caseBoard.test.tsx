// __tests__/components/common/caseBoard.test.tsx

import React from 'react';
import {act, fireEvent, render, screen,waitFor} from '@testing-library/react';

import CaseBoard, {CaseBoardInner} from '@/components/common/caseBoard';
import {getCaseBoard,saveCaseBoard} from '@/lib/api/caseBoard';

import {generateBoard, toEvidenceNode, evidenceNodeId} from '@/lib/data/boardGenerator';
import { getCapturedAt } from '@/lib/data/captureTime';
import { resolveMediaKind } from '@/lib/media';
import type { CaseEvidence } from '@/types/api';

const mockFitView = jest.fn();
const mockScreenToFlowPosition = jest.fn(
    (position: { x: number; y: number }) => ({
        x: position.x + 10,
        y: position.y + 20,
    })
);

jest.mock('@xyflow/react', () => {
    const React = require('react');

    return {
        ReactFlowProvider: ({
            children,
        }: {
            children: React.ReactNode;
        }) => (
            <div data-testid="react-flow-provider">
                {children}
            </div>
        ),

        useNodesState: (initial: unknown[]) => {
            const [state, setState] = React.useState(initial);

            return [
                state,
                setState,
                jest.fn(),
            ];
        },

        useEdgesState: (initial: unknown[]) => {
            const [state, setState] = React.useState(initial);

            return [
                state,
                setState,
                jest.fn(),
            ];
        },

        useReactFlow: () => ({
            screenToFlowPosition: mockScreenToFlowPosition,
            fitView: mockFitView,
        }),

        addEdge: (edge: unknown, edges: unknown[]) => [
            ...edges,
            edge,
        ],
    };
});

jest.mock('@dnd-kit/react', () => ({
    DragDropProvider: ({
        children,
        onDragEnd,
    }: {
        children: React.ReactNode;
        onDragEnd: (event: any) => void;
    }) => (
        <div>
            {children}

            <button
                data-testid="drop-success"
                onClick={() =>
                    onDragEnd({
                        canceled: false,
                        operation: {
                            source: {
                                data: {
                                    mediaId: 'media-1',
                                },
                            },
                            target: {
                                id: 'droppable',
                            },
                            position: {
                                current: {
                                    x: 100,
                                    y: 200,
                                },
                            },
                        },
                    })
                }
            >
                drop-success
            </button>

            <button
                data-testid="drop-missing-evidence"
                onClick={() =>
                    onDragEnd({
                        canceled: false,
                        operation: {
                            source: {
                                data: {
                                    mediaId: 'does-not-exist',
                                },
                            },
                            target: {
                                id: 'droppable',
                            },
                            position: {
                                current: {
                                    x: 100,
                                    y: 200,
                                },
                            },
                        },
                    })
                }
            >
                drop-missing-evidence
            </button>

            <button
                data-testid="drop-cancelled"
                onClick={() =>
                    onDragEnd({
                        canceled: true,
                        operation: {
                            source: {
                                data: {
                                    mediaId: 'media-1',
                                },
                            },
                            target: {
                                id: 'droppable',
                            },
                            position: {
                                current: {
                                    x: 100,
                                    y: 200,
                                },
                            },
                        },
                    })
                }
            >
                drop-cancelled
            </button>

            <button
                data-testid="drop-wrong-target"
                onClick={() =>
                    onDragEnd({
                        canceled: false,
                        operation: {
                            source: {
                                data: {
                                    mediaId: 'media-1',
                                },
                            },
                            target: {
                                id: 'somewhere-else',
                            },
                            position: {
                                current: {
                                    x: 100,
                                    y: 200,
                                },
                            },
                        },
                    })
                }
            >
                drop-wrong-target
            </button>
        </div>
    ),
}));

jest.mock('@/components/common/caseBoardCanvas', () => ({
    __esModule: true,
    default: (props: any) => (
        <div data-testid="case-board-canvas">
            <div data-testid="node-count">
                {props.nodes.length}
            </div>

            <div data-testid="edge-count">
                {props.edges.length}
            </div>

            <div data-testid="fullscreen-state">
                {String(props.fullscreen)}
            </div>

            <div data-testid="unsaved-state">
                {String(props.unsaved)}
            </div>

            <div data-testid="save-state">
                {props.saveState}
            </div>

            <div data-testid="readonly-state">
                {String(props.readOnly)}
            </div>

            <div data-testid="can-generate">
                {String(props.canGenerate)}
            </div>

            <div data-testid="save-present">
                {String(Boolean(props.onSave))}
            </div>

            <button
                onClick={() =>
                    props.onAddNote({
                        x: 300,
                        y: 400,
                    })
                }
            >
                add-note
            </button>

            <button
                onClick={() => props.onGenerate()}
            >
                generate
            </button>

            <button
                onClick={() =>
                    props.onToggleFullscreen()
                }
            >
                toggle-fullscreen
            </button>

            <button
                onClick={() =>
                    props.onSave?.()
                }
            >
                save
            </button>

            <button
                onClick={() =>
                    props.onConnect({
                        source: 'node-a',
                        target: 'node-b',
                    })
                }
            >
                connect
            </button>
        </div>
    ),
}));

jest.mock('@/components/common/evidenceCard', () => ({
    __esModule: true,
    default: (props: any) => (
        <div
            data-testid={`evidence-${props.mediaId}`}
            data-placed={String(props.placed)}
            data-captured={String(props.capturedAt)}
            data-annotations={String(props.annotationCount)}
        >
            {props.mediaName}
        </div>
    ),
}));

jest.mock('@/components/common/reportPanel', () => ({
    __esModule: true,
    default: (props: any) => (
        <div data-testid="report-panel">
            <div>{props.mediaName}</div>
            <div>{props.mediaKind}</div>
            <div>{props.certainty}</div>
        </div>
    ),
}));

jest.mock('@/components/ui/sliderBar', () => ({
    __esModule: true,
    default: ({
        filters,
        onChange,
    }: {
        filters: string[];
        onChange: (value: string) => void;
    }) => (
        <div>
            {filters.map((filter) => (
                <button
                    key={filter}
                    onClick={() => onChange(filter)}
                >
                    {filter}
                </button>
            ))}
        </div>
    ),
}));

jest.mock('@/lib/api/caseBoard', () => ({
    getCaseBoard: jest.fn(),
    saveCaseBoard: jest.fn(),
}));

jest.mock('@/lib/data/boardGenerator', () => ({
    generateBoard: jest.fn(),
    evidenceNodeId: jest.fn((mediaId: string) => `evidence-${mediaId}`),
    toEvidenceNode: jest.fn(
        (
            evidence: any,
            position: { x: number; y: number }
        ) => ({
            id: `evidence-${evidence.mediaId}`,
            type: 'evidence',
            position,
            data: {
                mediaId: evidence.mediaId,
            },
        })
    ),
}));

jest.mock('@/lib/data/captureTime', () => ({getCapturedAt: jest.fn(),}));
jest.mock('@/lib/media', () => ({resolveMediaKind: jest.fn(),}));

const mockedGetCaseBoard = getCaseBoard as jest.MockedFunction<typeof getCaseBoard>;
const mockedSaveCaseBoard = saveCaseBoard as jest.MockedFunction<typeof saveCaseBoard>;
const mockedGenerateBoard =generateBoard as jest.MockedFunction<typeof generateBoard>;
const mockedToEvidenceNode = toEvidenceNode as jest.MockedFunction<typeof toEvidenceNode>;
const mockedEvidenceNodeId = evidenceNodeId as jest.MockedFunction<typeof evidenceNodeId>;
const mockedGetCapturedAt = getCapturedAt as jest.MockedFunction<typeof getCapturedAt>;
const mockedResolveMediaKind =resolveMediaKind as jest.MockedFunction<typeof resolveMediaKind>;

const evidence1 = {
    mediaId: 'media-1',
    casePerspective: 'Front image',
    mediaUrl: 'https://example.com/image.jpg',
    mediaExtension: '.jpg',
    reportCertainty: 91,
    reportFindings: ['Finding one'],
    annotations: [
        {
            id: 'annotation-1',
        },
    ],
    reportArtifacts: {
        createdAt: '2026-09-29T10:00:00Z',
    },
} as unknown as CaseEvidence;

const evidence2 = {
    mediaId: 'media-2',
    casePerspective: 'Second image',
    mediaUrl: 'https://example.com/image2.jpg',
    mediaExtension: '.jpg',
    reportCertainty: 75,
    reportFindings: [],
    annotations: [],
    reportArtifacts: null,
} as unknown as CaseEvidence;

describe('CaseBoard', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        mockedGetCaseBoard.mockResolvedValue(null);
        mockedSaveCaseBoard.mockResolvedValue(undefined as never);
        mockedGetCapturedAt.mockImplementation((artifacts: any) => artifacts? new Date('2026-09-29T10:00:00Z').getTime() : null);
        mockedResolveMediaKind.mockReturnValue('image' as never);
        mockedEvidenceNodeId.mockImplementation((mediaId: string) => `evidence-${mediaId}`);
        mockedToEvidenceNode.mockImplementation(
            (
                evidence: any,
                position: {
                    x: number;
                    y: number;
                }
            ) => ({
                id: `evidence-${evidence.mediaId}`,
                type: 'evidence',
                position,
                data: {
                    mediaId: evidence.mediaId,
                },
            } as any)
        );

        mockedGenerateBoard.mockReturnValue({
            nodes: [],
            edges: [],
        } as any);
    });

    it('wraps the inner board in ReactFlowProvider', async () => {
        render(
            <CaseBoard
                caseId="case-1"
                evidenceList={[]}
            />
        );

        expect(screen.getByTestId('react-flow-provider')).toBeInTheDocument();
        expect(screen.getByTestId('case-board-canvas')).toBeInTheDocument();
    });

    it('renders available evidence and capture information', async () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[
                    evidence1,
                    evidence2,
                ]}
            />
        );

        await waitFor(() => {
            expect(mockedGetCaseBoard).toHaveBeenCalledWith('case-1');
        });

        expect(screen.getByTestId('evidence-media-1')).toHaveAttribute('data-placed', 'false');
        expect(screen.getByTestId('evidence-media-1')).toHaveAttribute('data-annotations', '1');
        expect(screen.getByTestId('evidence-media-1')).not.toHaveAttribute('data-captured', 'null');
        expect(screen.getByTestId('evidence-media-2')).toHaveAttribute('data-captured','null');
        expect(screen.getByTestId('can-generate')).toHaveTextContent('true');
        expect(screen.getByText('Drag evidence onto the board to start.')).toBeInTheDocument();
    });

    it('restores saved evidence, notes and valid edges', async () => {
        mockedToEvidenceNode.mockImplementation(
            (evidence: any, position: any) => ({
                id: `evidence-${evidence.mediaId}`,
                type: 'evidence',
                position,
                selected: true,
                data: {
                    mediaId: evidence.mediaId,
                },
            } as any)
        );

        mockedGetCaseBoard.mockResolvedValue({
            nodes: {
                evidenceNodes: [
                    {
                        mediaId: 'missing-media',
                        position: {
                            x: 1,
                            y: 2,
                        },
                    },
                    {
                        mediaId: 'media-1',
                        position: {
                            x: 50,
                            y: 60,
                        },
                    },
                ],
                noteNodes: [
                    {
                        id: 'note-existing',
                        position: {
                            x: 70,
                            y: 80,
                        },
                        text: 'Existing note',
                    },
                ],
            },

            edges: [
                {
                    id: 'valid-edge',
                    source: 'evidence-media-1',
                    target: 'note-existing',
                    sourceHandle: 'source-handle',
                    targetHandle: 'target-handle',
                    variant: 'solid',
                    label: 'supports',
                },

                {
                    id: 'invalid-edge',
                    source: 'does-not-exist',
                    target: 'note-existing',
                },
            ],
        } as any);

        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[evidence1]}
            />
        );

        await waitFor(() => {
            expect(screen.getByTestId('node-count')).toHaveTextContent('2');
        });

        expect(screen.getByTestId('edge-count')).toHaveTextContent('1');
        expect(screen.getByTestId('evidence-media-1')).toHaveAttribute('data-placed', 'true');
        expect(screen.getByText('All evidence is on the board.')).toBeInTheDocument();
        expect(mockedToEvidenceNode).toHaveBeenCalledWith(
            evidence1,
            {
                x: 50,
                y: 60,
            }
        );
    });

    it('does not restore a board containing no usable nodes', async () => {
        mockedGetCaseBoard.mockResolvedValue({
            nodes: {
                evidenceNodes: [
                    {
                        mediaId: 'missing',
                        position: {
                            x: 1,
                            y: 2,
                        },
                    },
                ],
                noteNodes: [],
            },
            edges: [],
        } as any);

        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[evidence1]}
            />
        );

        await waitFor(() => {
            expect(mockedGetCaseBoard).toHaveBeenCalled();
        });

        expect(screen.getByTestId('node-count')).toHaveTextContent('0');
    });

    it('adds a note using the requested board position', async () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[]}
            />
        );

        fireEvent.click(screen.getByText('add-note'));
        expect(screen.getByTestId('node-count')).toHaveTextContent('1');
        expect(screen.getByTestId('unsaved-state')).toHaveTextContent('true');
    });

    it('generates the board and fits the generated nodes', async () => {
        jest.useFakeTimers();

        mockedGenerateBoard.mockReturnValue({
            nodes: [
                {
                    id: 'generated-node',
                    type: 'note',
                    position: {
                        x: 10,
                        y: 20,
                    },
                    data: {
                        text: 'Generated',
                    },
                },
            ],
            edges: [
                {
                    id: 'generated-edge',
                    source: 'generated-node',
                    target: 'other',
                },
            ],
        } as any);

        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[evidence1]}
            />
        );

        fireEvent.click(screen.getByText('generate'));
        expect(mockedGenerateBoard).toHaveBeenCalled();
        expect(screen.getByTestId('node-count')).toHaveTextContent('1');
        expect(screen.getByTestId('edge-count')).toHaveTextContent('1');
        act(() => {
            jest.advanceTimersByTime(50);
        });

        expect(mockFitView).toHaveBeenCalledWith({
            padding: 0.1,
            duration: 500,
        });

        jest.useRealTimers();
    });

    it('creates a custom edge when nodes are connected', () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[]}
            />
        );

        fireEvent.click(screen.getByText('connect'));
        expect(screen.getByTestId('edge-count')).toHaveTextContent('1');
        expect(screen.getByTestId('unsaved-state')).toHaveTextContent('true');
    });

    it('saves the current board successfully', async () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[]}
            />
        );

        fireEvent.click(screen.getByText('add-note'));
        expect(screen.getByTestId('unsaved-state')).toHaveTextContent('true');
        fireEvent.click(screen.getByText('save'));
        await waitFor(() => {
            expect(mockedSaveCaseBoard).toHaveBeenCalledTimes(1);
        });

        expect(
            mockedSaveCaseBoard
        ).toHaveBeenCalledWith(
            'case-1',
            expect.objectContaining({
                nodes: expect.objectContaining({
                    noteNodes: expect.arrayContaining([
                        expect.objectContaining({
                            text: '',
                            position: {
                                x: 188,
                                y: 288,
                            },
                        }),
                    ]),
                }),
                edges: [],
            }),
            undefined
        );

        await waitFor(() => {
            expect(screen.getByTestId('save-state')).toHaveTextContent('saved');
        });

        expect(screen.getByTestId('unsaved-state')).toHaveTextContent('false');
    });

    it('shows an error when saving fails', async () => {
        mockedSaveCaseBoard.mockRejectedValue(new Error('Save failed'));
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[]}
            />
        );

        fireEvent.click(screen.getByText('add-note'));
        fireEvent.click(screen.getByText('save'));

        await waitFor(() => {
            expect(
                screen.getByTestId('save-state')
            ).toHaveTextContent('error');
        });
    });

    it('autosaves an unsaved board on pagehide using keepalive', async () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[]}
            />
        );

        fireEvent.click(screen.getByText('add-note'));
        await waitFor(() => {
            expect(screen.getByTestId('unsaved-state')).toHaveTextContent('true');
        });

        act(() => {
            window.dispatchEvent(
                new Event('pagehide')
            );
        });

        await waitFor(() => {
            expect(
                mockedSaveCaseBoard
            ).toHaveBeenCalledWith(
                'case-1',
                expect.any(Object),
                {
                    keepalive: true,
                }
            );
        });
    });

    it('autosaves unsaved changes when unmounted', async () => {
        const { unmount } = render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[]}
            />
        );

        fireEvent.click(screen.getByText('add-note'));
        await waitFor(() => {
            expect(screen.getByTestId('unsaved-state')).toHaveTextContent('true');
        });

        unmount();

        await waitFor(() => {
            expect(
                mockedSaveCaseBoard
            ).toHaveBeenCalledWith(
                'case-1',
                expect.any(Object),
                {
                    keepalive: true,
                }
            );
        });
    });

    it('does not save in read-only mode', async () => {
        mockedGenerateBoard.mockReturnValue({
            nodes: [
                {
                    id: 'readonly-note',
                    type: 'note',
                    position: {
                        x: 0,
                        y: 0,
                    },
                    data: {
                        text: 'Read only',
                    },
                },
            ],
            edges: [],
        } as any);

        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[]}
                readOnly
            />
        );

        expect(screen.getByTestId('save-present')).toHaveTextContent('false');
        expect(screen.getByTestId('readonly-state')).toHaveTextContent('true');
        fireEvent.click(screen.getByText('generate'));

        act(() => {
            window.dispatchEvent(new Event('pagehide'));
        });

        await waitFor(() => {
            expect(mockedSaveCaseBoard).not.toHaveBeenCalled();
        });
    });

    it('enters and exits fullscreen with Escape', () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[]}
            />
        );

        expect(screen.getByTestId('fullscreen-state')).toHaveTextContent('false');
        fireEvent.click(screen.getByText('toggle-fullscreen'));
        expect(screen.getByTestId('fullscreen-state')).toHaveTextContent('true');
        expect(document.body.style.overflow).toBe('hidden');
        fireEvent.keyDown(window, {key: 'Escape',});
        expect(screen.getByTestId('fullscreen-state')).toHaveTextContent('false');
        expect(document.body.style.overflow).toBe('');
    });

    it('does not leave fullscreen when Escape is pressed while typing', () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[]}
            />
        );

        fireEvent.click(screen.getByText('toggle-fullscreen'));
        const input = document.createElement('input');
        document.body.appendChild(input);
        input.focus();

        fireEvent.keyDown(window, {key: 'Escape',});
        expect(screen.getByTestId('fullscreen-state')).toHaveTextContent('true');
        input.remove();
        fireEvent.keyDown(window, {key: 'Escape',});
        expect(screen.getByTestId('fullscreen-state')).toHaveTextContent('false');
    });

    it('ignores non-Escape keys while fullscreen', () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[]}
            />
        );

        fireEvent.click(screen.getByText('toggle-fullscreen'));
        fireEvent.keyDown(window, {key: 'Enter',});
        expect(screen.getByTestId('fullscreen-state')).toHaveTextContent('true');
    });

    it('adds dropped evidence to the board', () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[evidence1]}
            />
        );

        expect(screen.getByTestId('node-count')).toHaveTextContent('0');
        fireEvent.click(screen.getByTestId('drop-success'));
        expect(mockScreenToFlowPosition).toHaveBeenCalledWith({x: 100, y: 200,});
        expect(mockedToEvidenceNode).toHaveBeenCalledWith(
            evidence1,
            {
                x: 110,
                y: 220,
            }
        );

        expect(screen.getByTestId('node-count')).toHaveTextContent('1');
        expect(screen.getByTestId('evidence-media-1')).toHaveAttribute('data-placed','true');
    });

    it('does not add evidence if the dropped media does not exist', () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[evidence1]}
            />
        );

        fireEvent.click(screen.getByTestId('drop-missing-evidence'));
        expect(screen.getByTestId('node-count')).toHaveTextContent('0');
    });

    it('does not add the same evidence twice', () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[evidence1]}
            />
        );

        fireEvent.click(screen.getByTestId('drop-success'));
        expect(screen.getByTestId('node-count')).toHaveTextContent('1');
        fireEvent.click(screen.getByTestId('drop-success'));
        expect(screen.getByTestId('node-count')).toHaveTextContent('1');
    });

    it('ignores cancelled drops and drops outside the board', () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[evidence1]}
            />
        );

        fireEvent.click(screen.getByTestId('drop-cancelled'));
        fireEvent.click(screen.getByTestId('drop-wrong-target'));
        expect(screen.getByTestId('node-count')).toHaveTextContent('0');
    });

    it('shows the empty Report state when no evidence is selected', () => {
        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[evidence1]}
            />
        );

        fireEvent.click(screen.getByText('Report'));
        expect(screen.getByText('Select an evidence to view its findings.')).toBeInTheDocument();
        expect(screen.queryByTestId('report-panel')).not.toBeInTheDocument();
    });

    it('shows the selected evidence report', async () => {
        mockedToEvidenceNode.mockImplementation(
            (evidence: any, position: any) => ({
                id: `evidence-${evidence.mediaId}`,
                type: 'evidence',
                position,
                selected: true,
                data: {
                    mediaId: evidence.mediaId,
                },
            } as any)
        );

        mockedGetCaseBoard.mockResolvedValue({
            nodes: {
                evidenceNodes: [
                    {
                        mediaId: 'media-1',
                        position: {
                            x: 50,
                            y: 60,
                        },
                    },
                ],
                noteNodes: [],
            },
            edges: [],
        } as any);

        mockedResolveMediaKind.mockReturnValue('image' as never);

        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[evidence1]}
            />
        );

        await waitFor(() => {expect(screen.getByTestId('node-count')).toHaveTextContent('1');});
        fireEvent.click(screen.getByText('Report'));
        expect(screen.getByTestId('report-panel')).toBeInTheDocument();
        expect(screen.getByTestId('report-panel')).toHaveTextContent('Front image');
        expect(mockedResolveMediaKind).toHaveBeenCalledWith(evidence1);
    });

    it('handles failure to load the saved board', async () => {
        mockedGetCaseBoard.mockRejectedValue(new Error('Could not load'));

        render(
            <CaseBoardInner
                caseId="case-1"
                evidenceList={[evidence1]}
            />
        );

        await waitFor(() => {expect(mockedGetCaseBoard).toHaveBeenCalledWith('case-1');});
        expect(screen.getByTestId('node-count')).toHaveTextContent('0');
        expect(screen.getByTestId('case-board-canvas')).toBeInTheDocument();
    });
});