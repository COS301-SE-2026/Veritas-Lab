import * as ort from "onnxruntime-web";

export type ActivationType = | "SIGMOID" | "SOFTMAX" | "NONE";

export interface ClassificationResult {
    aiProbability: number;
    classification: string;
}

export interface BaseModelConfig {
    activation: ActivationType;
    classLabels: [string, string];
    aiClassIndex: 0 | 1;
    threshold: number;
}

interface VisualModelConfig extends BaseModelConfig {
    inputWidth: number;
    inputHeight: number;
    mean: [number, number, number];
    std: [number, number, number];
}

export interface ImageModelConfig extends VisualModelConfig {
    mediaType: "IMAGE";
}

export interface VideoModelConfig extends VisualModelConfig {
    mediaType: "VIDEO";
    frameCount: number;
}

export interface PdfModelConfig extends VisualModelConfig {
    mediaType: "PDF";
    pageCount: number;
}

export type ModelConfig = | ImageModelConfig | VideoModelConfig | PdfModelConfig;

function validateBaseConfig(config: BaseModelConfig): void {
    if (!Number.isFinite(config.threshold) || config.threshold < 0 || config.threshold > 1) {
        throw new Error("Threshold must be between 0 and 1.");
    }

    if (config.classLabels.some(label => !label.trim())) {
        throw new Error("Class labels cannot be empty.");
    }

    if (config.classLabels[0].trim() === config.classLabels[1].trim()) {
        throw new Error("Class labels must be different.");
    }
}

function validateVisualConfig(config: VisualModelConfig): void {
    validateBaseConfig(config);

    if (
        !Number.isInteger(config.inputWidth) ||
        !Number.isInteger(config.inputHeight) ||
        config.inputWidth <= 0 ||
        config.inputHeight <= 0
    ) {
        throw new Error("Input dimensions must be positive integers.");
    }

    if (config.mean.some(value => !Number.isFinite(value)) || config.std.some(value => !Number.isFinite(value) || value === 0)) {
        throw new Error("Mean and standard deviation values must be valid numbers, and standard deviations cannot be 0.");
    }
}

function validateImageConfig(config: ImageModelConfig): void {
    validateVisualConfig(config);
}

function validateVideoConfig(config: VideoModelConfig): void {
    validateVisualConfig(config);

    if (!Number.isInteger(config.frameCount) || config.frameCount <= 0) {
        throw new Error("Frame count must be a positive integer.");
    }
}

function validatePdfConfig(config: PdfModelConfig): void {
    validateVisualConfig(config);

    if (!Number.isInteger(config.pageCount) || config.pageCount <= 0) {
        throw new Error("Page count must be a positive integer.");
    }
}

async function imageBitmapToTensor(bitmap: ImageBitmap, config: VisualModelConfig): Promise<ort.Tensor> {
    const canvas = document.createElement("canvas");
    canvas.width = config.inputWidth;
    canvas.height = config.inputHeight;
    const context = canvas.getContext("2d");

    if (!context) {
        throw new Error("Could not create canvas context.");
    }

    context.drawImage(bitmap, 0, 0, config.inputWidth, config.inputHeight);

    const imageData = context.getImageData(0, 0, config.inputWidth, config.inputHeight);
    const pixelData = imageData.data;
    const pixelCount =config.inputWidth * config.inputHeight;
    const tensorData = new Float32Array(3 * pixelCount);

    for (let i = 0; i < pixelCount; i++) {
        const rgbaIndex = i * 4;

        const r = pixelData[rgbaIndex] / 255;
        const g = pixelData[rgbaIndex + 1] / 255;
        const b = pixelData[rgbaIndex + 2] / 255;

        tensorData[i] = (r - config.mean[0]) / config.std[0];
        tensorData[pixelCount + i] = (g - config.mean[1]) / config.std[1];
        tensorData[(2 * pixelCount) + i] = (b - config.mean[2]) / config.std[2];
    }

    return new ort.Tensor("float32", tensorData, [1, 3, config.inputHeight, config.inputWidth]);
}

export async function processImage(file: File, config: ImageModelConfig): Promise<ort.Tensor> {
    validateImageConfig(config);

    if (!file.type.startsWith("image/")) {
        throw new Error("File must be an image.");
    }

    const bitmap = await createImageBitmap(file);

    try {
        return await imageBitmapToTensor(bitmap, config);
    } finally {
        bitmap.close();
    }
}

function waitForVideoMetadata(video: HTMLVideoElement): Promise<void> {
    return new Promise((resolve, reject) => {
        if (video.readyState >= 1 && Number.isFinite(video.duration)) {
            resolve();
            return;
        }

        const onLoadedMetadata = () => {
            cleanup();
            resolve();
        };

        const onError = () => {
            cleanup();
            reject(new Error("Could not load video metadata."));
        };

        const cleanup = () => {
            video.removeEventListener("loadedmetadata", onLoadedMetadata);
            video.removeEventListener("error", onError);
        };

        video.addEventListener("loadedmetadata", onLoadedMetadata);
        video.addEventListener("error", onError);
    });
}

function seekVideo(video: HTMLVideoElement, time: number): Promise<void> {
    return new Promise((resolve, reject) => {
        const safeTime = Math.min(
            Math.max(time, 0),
            Math.max(video.duration - 0.001, 0)
        );

        const onSeeked = () => {
            cleanup();
            resolve();
        };

        const onError = () => {
            cleanup();
            reject(new Error("Could not seek video."));
        };

        const cleanup = () => {
            video.removeEventListener("seeked", onSeeked);
            video.removeEventListener("error", onError);
        };

        video.addEventListener("seeked", onSeeked);
        video.addEventListener("error", onError);
        video.currentTime = safeTime;
    });
}

export async function processVideo(file: File, config: VideoModelConfig): Promise<ort.Tensor[]> {
    validateVideoConfig(config);

    if (!file.type.startsWith("video/")) {
        throw new Error("File must be a video.");
    }

    const video = document.createElement("video");

    video.muted = true;
    video.preload = "auto";

    const objectUrl = URL.createObjectURL(file);

    video.src = objectUrl;
    video.load();

    try {
        await waitForVideoMetadata(video);

        if (!Number.isFinite(video.duration) || video.duration <= 0) {
            throw new Error("Could not determine video duration.");
        }

        const tensors: ort.Tensor[] = [];

        for (let i = 0; i < config.frameCount; i++) {
            const time = ((i + 0.5) / config.frameCount) * video.duration;
            await seekVideo(video, time);
            const bitmap = await createImageBitmap(video);

            try {
                tensors.push(
                    await imageBitmapToTensor(
                        bitmap,
                        config
                    )
                );
            } finally {
                bitmap.close();
            }
        }

        return tensors;
    } finally {
        URL.revokeObjectURL(objectUrl);
        video.removeAttribute("src");
        video.load();
        video.remove();
    }
}

export async function processPdf(file: File, config: PdfModelConfig): Promise<ort.Tensor[]> {
    validatePdfConfig(config);

    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
        throw new Error("File must be a PDF.");
    }

    const pdfjsLib = await import("pdfjs-dist");
    const buffer = await file.arrayBuffer();
    const pdf = await pdfjsLib.getDocument({data: buffer}).promise;
    const maxPages = Math.min(config.pageCount, pdf.numPages);
    const tensors: ort.Tensor[] = [];

    try {
        for (let pageNumber = 1; pageNumber <= maxPages; pageNumber++) {
            const page = await pdf.getPage(pageNumber);

            try {
                const viewport = page.getViewport({scale: 1.5});
                const canvas = document.createElement("canvas");
                canvas.width = Math.ceil(viewport.width);
                canvas.height = Math.ceil(viewport.height);
                const context = canvas.getContext("2d");

                if (!context) {
                    throw new Error("Could not create PDF canvas context.");
                }

                await page.render({canvasContext: context, viewport, canvas}).promise;
                const bitmap = await createImageBitmap(canvas);

                try {
                    tensors.push(await imageBitmapToTensor(bitmap, config)
                    );
                } finally {
                    bitmap.close();
                }
            } finally {
                page.cleanup();
            }
        }

        return tensors;
    } finally {
        await pdf.destroy();
    }
}

export async function loadModel(modelFile: File): Promise<ort.InferenceSession> {
    if (!modelFile.name.toLowerCase().endsWith(".onnx")) {
        throw new Error("Model file must be an ONNX model.");
    }

    const modelBuffer = await modelFile.arrayBuffer();

    return await ort.InferenceSession.create(
        modelBuffer,
        {
            executionProviders: ["webgpu", "wasm"]
        }
    );
}

async function runTensor(session: ort.InferenceSession, tensor: ort.Tensor): Promise<ort.Tensor> {
    if (session.inputNames.length !== 1) {
        throw new Error(`Model must have exactly one input. Found ${session.inputNames.length}.`);
    }

    if (session.outputNames.length !== 1) {
        throw new Error(`Model must have exactly one output. Found ${session.outputNames.length}.`);
    }

    const inputName = session.inputNames[0];
    const outputName = session.outputNames[0];

    const feeds: Record<string, ort.Tensor> = {[inputName]: tensor};

    const results = await session.run(feeds);
    const output = results[outputName];

    if (!(output instanceof ort.Tensor)) {
        throw new Error("Model output is not a tensor.");
    }

    return output;
}

function sigmoid(value: number): number {
    return 1 / (1 + Math.exp(-value));
}

function softmax(values: number[]): number[] {
    const maxValue = Math.max(...values);
    const exponentials = values.map(value => Math.exp(value - maxValue));
    const sum = exponentials.reduce((total, value) => total + value, 0);
    return exponentials.map(value => value / sum);
}

export async function runImageModel(session: ort.InferenceSession, file: File, config: ImageModelConfig): Promise<ClassificationResult> {
    const tensor = await processImage(file, config);
    const output = await runTensor(session, tensor);
    return classifyOutput(output, config);
}

export async function runVideoModel(session: ort.InferenceSession, file: File, config: VideoModelConfig): Promise<ClassificationResult> {
    const tensors = await processVideo(file, config);
    const probabilities: number[] = [];

    for (const tensor of tensors) {
        const output = await runTensor(session, tensor);
        probabilities.push(getAiProbability(output, config));
    }

    const aiProbability = probabilities.reduce((sum, value) => sum + value, 0) / probabilities.length;
    return classifyProbability(aiProbability, config);
}

export async function runPdfModel(session: ort.InferenceSession, file: File, config: PdfModelConfig): Promise<ClassificationResult> {
    const tensors = await processPdf(file, config);
    const probabilities: number[] = [];

    for (const tensor of tensors) {
        const output = await runTensor(session, tensor);
        probabilities.push(getAiProbability(output, config));
    }

    const aiProbability = probabilities.reduce((sum, value) => sum + value, 0) / probabilities.length;

    return classifyProbability(
        aiProbability,
        config
    );
}

function getAiProbability(output: ort.Tensor, config: BaseModelConfig): number {
    if (output.type === "string") {
        throw new Error("Model output must be numeric.");
    }

    const values = Array.from(output.data as ArrayLike<number | bigint>, value => Number(value));

    if (values.some(value => !Number.isFinite(value))) {
        throw new Error("Model output contains invalid values.");
    }

    if (values.length === 1) {
        if (config.activation === "SOFTMAX") {
            throw new Error("SOFTMAX requires a two-class model output.");
        }

        let probability: number;

        if (config.activation === "SIGMOID") {
            probability = sigmoid(values[0]);
        } else {
            probability = values[0];
        }

        if (probability < 0 || probability > 1) {
            throw new Error("Model output must be between 0 and 1 when activation is NONE.");
        }

        return config.aiClassIndex === 1 ? probability : 1 - probability;
    }

    if (values.length === 2) {
        let probabilities: number[];

        if (config.activation === "SOFTMAX") {
            probabilities = softmax(values);
        } else if (config.activation === "NONE") {

            if (values.some(value => value < 0 || value > 1)) {
                throw new Error("Model outputs must be between 0 and 1 when activation is NONE.");
            }

            probabilities = values;
        } else {
            throw new Error("SIGMOID models must produce a single output value.");
        }

        return probabilities[config.aiClassIndex];
    }

    throw new Error(`Unsupported model output size: ${values.length}. Expected 1 or 2 values.`);
}

function classifyProbability(aiProbability: number, config: BaseModelConfig): ClassificationResult {
    const aiLabel = config.classLabels[config.aiClassIndex];
    const otherClassIndex = config.aiClassIndex === 0 ? 1 : 0;
    const otherLabel =config.classLabels[otherClassIndex];

    return {
        aiProbability,
        classification: aiProbability >= config.threshold ? aiLabel : otherLabel
    };
}

function classifyOutput(output: ort.Tensor, config: BaseModelConfig): ClassificationResult {
    const aiProbability = getAiProbability(output, config);
    return classifyProbability(aiProbability, config);
}

export async function runModel(modelFile: File, mediaFile: File, config: ModelConfig): Promise<ClassificationResult> {
    const session = await loadModel(modelFile);

    try {
        switch (config.mediaType) {
            case "IMAGE":
                return await runImageModel(session, mediaFile, config);

            case "VIDEO":
                return await runVideoModel(session, mediaFile, config);

            case "PDF":
                return await runPdfModel(session, mediaFile, config);
            
            default:
                throw new Error("Unsupported media type.");
        }
    } finally {
        await session.release();
    }
}