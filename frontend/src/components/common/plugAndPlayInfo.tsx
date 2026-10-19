'use client';
import { Info, X } from 'lucide-react';
import { useEffect, useState, type ReactNode } from 'react';
import { createPortal } from 'react-dom';

type PlugAndPlayInfoProps = {
    mediaKind: string;
    mean: readonly number[];
    std: readonly number[];
    threshold: number;
    classLabels: readonly [string, string];
};

const Code = ({ children }: { children: ReactNode }) => (
    <code className="rounded-md bg-(--color-surface-sunken) px-1.5 py-0.5 font-mono text-xs text-(--color-text-strong)">
        {children}
    </code>
);

const Section = ({ title, children }: { title: string; children: ReactNode }) => (
    <section className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold text-(--color-text-strong)">{title}</h3>
        <div className="flex flex-col gap-2 text-sm text-(--color-text-muted)">{children}</div>
    </section>
);

const EXPORT_SNIPPET = `import torch

model.eval()
dummy = torch.randn(1, 3, 224, 224)  # [batch, RGB, height, width]

torch.onnx.export(
    model, dummy, "detector.onnx",
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
    opset_version=17,
)

# If the exporter wrote a separate .onnx.data file, embed the weights:
# import onnx
# onnx.save(onnx.load("detector.onnx"), "detector_single.onnx",
#           save_as_external_data=False)`;

export default function PlugAndPlayInfo({ mediaKind, mean, std, threshold, classLabels }: PlugAndPlayInfoProps) {
    const [isOpen, setIsOpen] = useState(false);
    const [isMounted, setIsMounted] = useState(false);

    useEffect(() => {
        setIsMounted(true);
    }, []);

    useEffect(() => {
        if (!isOpen) return;
        const onKey = (k: KeyboardEvent) => {
            if (k.key === 'Escape') setIsOpen(false);
        };
        document.addEventListener('keydown', onKey);
        return () => document.removeEventListener('keydown', onKey);
    }, [isOpen]);

    const fmt = (values: readonly number[]) => `[${values.join(', ')}]`;
    const [authenticLabel, aiLabel] = classLabels;

    const mediaRows = [
        { kind: 'image', label: 'Image', text: 'The model runs once on the image.' },
        { kind: 'video', label: 'Video', text: 'Frames are sampled evenly across the video (Frame Count, default 8). The model runs on each frame and the AI probabilities are averaged.' },
        { kind: 'pdf', label: 'PDF', text: 'The first pages are rendered as images (Page Count, default 4). The model runs on each page and the AI probabilities are averaged.' },
    ];

    return (
        <>
            <button
                type="button"
                onClick={() => setIsOpen(true)}
                aria-label="How plug and play models work"
                title="How plug and play models work"
                className="ml-auto rounded-full p-1.5 text-(--color-text-muted) transition-colors hover:bg-(--color-surface-sunken) hover:text-(--color-text-strong)"
            >
                <Info size={20} />
            </button>

            {isOpen && isMounted && createPortal(
                <div
                    className="vl-animation-fade fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
                    onClick={() => setIsOpen(false)}
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="pnp-info-title"
                >
                    <div
                        className="vl-animation-pop flex max-h-[85vh] w-full max-w-2xl flex-col rounded-2xl bg-(--color-surface) shadow-lg"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="flex items-start gap-4 border-b border-(--color-line) p-6">
                            <div>
                                <h2 id="pnp-info-title" className="text-xl font-bold text-(--color-text-strong)">
                                    Model requirements
                                </h2>
                                <p className="mt-1 text-sm text-(--color-text-muted)">
                                    What your model needs to look like to run in Plug and Play.
                                </p>
                            </div>
                            <button
                                type="button"
                                onClick={() => setIsOpen(false)}
                                aria-label="Close"
                                className="ml-auto rounded-full p-1 text-(--color-text-muted) transition-colors hover:bg-(--color-surface-sunken) hover:text-(--color-text-strong)"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <div className="flex flex-col gap-6 overflow-y-auto p-6">
                            <Section title="1. File format">
                                <p>
                                    A single <Code>.onnx</Code> file with its weights embedded. Separate weight files
                                    (<Code>.onnx.data</Code>) are not supported.
                                </p>
                                <p>
                                    The model runs in your browser (WebGPU, falling back to WebAssembly). It is never uploaded;
                                    only the result is saved to the case. Smaller models run faster and are less likely to run out of memory.
                                </p>
                                <p>
                                    The model must have <strong>exactly one input</strong> and <strong>exactly one output</strong>.
                                </p>
                            </Section>

                            <Section title="2. Input">
                                <p>
                                    One <Code>float32</Code> tensor with shape <Code>[1, 3, H, W]</Code> (batch, channels, height, width),
                                    with channels in <strong>RGB</strong> order. <Code>H</Code> and <Code>W</Code> default to 224 and must match
                                    the Input Width and Input Height under Advanced Model Config Options.
                                </p>
                                <p>Veritas preprocesses the evidence for you, so don&apos;t build these steps into the model:</p>
                                <ul className="ml-5 list-disc space-y-1">
                                    <li>Resized (stretched, not cropped) to W × H</li>
                                    <li>Pixel values scaled to 0–1</li>
                                    <li>Normalized per channel with mean <Code>{fmt(mean)}</Code> and std <Code>{fmt(std)}</Code> (ImageNet)</li>
                                </ul>
                            </Section>

                            <Section title="3. Output">
                                <p>The output must contain exactly 1 or 2 numbers, for example shape <Code>[1, 1]</Code> or <Code>[1, 2]</Code>.</p>
                                <div className="overflow-x-auto rounded-[var(--radius-sm)] border border-(--color-line)">
                                    <table className="w-full text-left text-xs">
                                        <thead className="bg-(--color-surface-muted) text-(--color-text-strong)">
                                            <tr>
                                                <th className="p-2 font-semibold">Outputs</th>
                                                <th className="p-2 font-semibold">Meaning</th>
                                                <th className="p-2 font-semibold">Activation to pick</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-(--color-line)">
                                            <tr>
                                                <td className="p-2">1 value</td>
                                                <td className="p-2">Score for <strong>{aiLabel}</strong></td>
                                                <td className="p-2"><strong>Sigmoid</strong> if it&apos;s a raw logit, <strong>None</strong> if it&apos;s already a probability (0–1)</td>
                                            </tr>
                                            <tr>
                                                <td className="p-2">2 values</td>
                                                <td className="p-2"><Code>[{authenticLabel}, {aiLabel}]</Code>, in that order</td>
                                                <td className="p-2"><strong>Softmax</strong> if they&apos;re logits, <strong>None</strong> if they&apos;re already probabilities (0–1)</td>
                                            </tr>
                                        </tbody>
                                    </table>
                                </div>
                                <p>
                                    Evidence is labelled <strong>{aiLabel}</strong> when the AI probability is at least {threshold}; otherwise it&apos;s labelled <strong>{authenticLabel}</strong>.
                                </p>
                            </Section>

                            <Section title="4. Media types">
                                <p>Your model is always an image classifier. Videos and PDFs are turned into images first.</p>
                                <ul className="flex flex-col gap-2">
                                    {mediaRows.map((row) => {
                                        const isCurrent = row.kind === mediaKind;
                                        return (
                                            <li
                                                key={row.kind}
                                                className={`rounded-[var(--radius-sm)] border p-3 ${isCurrent ? 'border-(--color-secondary) bg-(--color-b-50)' : 'border-(--color-line)'}`}
                                            >
                                                <span className="font-semibold text-(--color-text-strong)">{row.label}</span>
                                                {isCurrent && <span className="ml-2 text-xs text-(--color-b-600)">(this evidence)</span>}
                                                <p className="mt-1">{row.text}</p>
                                            </li>
                                        );
                                    })}
                                </ul>
                            </Section>

                            <Section title="5. Exporting from PyTorch">
                                <pre className="overflow-x-auto rounded-[var(--radius-sm)] bg-(--color-surface-sunken) p-3 font-mono text-xs leading-relaxed text-(--color-text-strong)">
                                    {EXPORT_SNIPPET}
                                </pre>
                            </Section>

                            <Section title="Common errors">
                                <ul className="ml-5 list-disc space-y-1">
                                    <li><Code>SIGMOID models must produce a single output value</Code>: your model has 2 outputs, so switch to Softmax or None.</li>
                                    <li><Code>SOFTMAX requires a two-class model output</Code>: your model has 1 output, so switch to Sigmoid or None.</li>
                                    <li><Code>Model output must be between 0 and 1 when activation is NONE</Code>: the model outputs logits, so pick Sigmoid or Softmax.</li>
                                    <li><Code>Unsupported model output size</Code>: the model must output exactly 1 or 2 numbers.</li>
                                    <li><strong>Shape or dimension errors</strong>: Input Width and Height don&apos;t match the size the model was exported with.</li>
                                </ul>
                            </Section>
                        </div>
                    </div>
                </div>,
                document.body
            )}
        </>
    );
}