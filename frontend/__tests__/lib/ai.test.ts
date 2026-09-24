import * as ort from "onnxruntime-web";

import {
    ImageModelConfig,
    VideoModelConfig,
    PdfModelConfig,
    loadModel,
    processImage,
    processVideo,
    processPdf,
    runImageModel,
    runVideoModel,
    runPdfModel,
    runModel
} from "../../src/lib/ai";

jest.mock("pdfjs-dist", () => ({getDocument: jest.fn()}));

const baseImageConfig: ImageModelConfig = {
    mediaType: "IMAGE",
    activation: "NONE",
    classLabels: ["AUTHENTIC", "AI"],
    aiClassIndex: 1,
    threshold: 0.5,
    inputWidth: 2,
    inputHeight: 2,
    mean: [0, 0, 0],
    std: [1, 1, 1]
};

const baseVideoConfig: VideoModelConfig = {
    ...baseImageConfig,
    mediaType: "VIDEO",
    frameCount: 2
};

const basePdfConfig: PdfModelConfig = {
    ...baseImageConfig,
    mediaType: "PDF",
    pageCount: 2
};

function createImageFile(): File {
    return new File(
        [new Uint8Array([1, 2, 3])],
        "test.png",
        {
            type: "image/png"
        }
    );
}

function createVideoFile(): File {
    return new File(
        [new Uint8Array([1, 2, 3])],
        "test.mp4",
        {
            type: "video/mp4"
        }
    );
}

function createPdfFile(): File {
    const file = new File(
        [new Uint8Array([1, 2, 3])],
        "test.pdf",
        {
            type: "application/pdf"
        }
    );

    Object.defineProperty(
        file,
        "arrayBuffer",
        {
            configurable: true,
            value: jest.fn().mockResolvedValue(new ArrayBuffer(8))
        }
    );

    return file;
}

function createModelFile(): File {
    const file = new File(
        [new Uint8Array([1, 2, 3])],
        "model.onnx",
        {
            type: "application/octet-stream"
        }
    );

    Object.defineProperty(
        file,
        "arrayBuffer",
        {
            configurable: true,
            value: jest.fn().mockResolvedValue(new ArrayBuffer(8))
        }
    );

    return file;
}

function createOutputTensor(values: number[]): ort.Tensor {
    return new ort.Tensor(
        "float32",
        new Float32Array(values),
        [1, values.length]
    );
}

function createSession(output: ort.Tensor, inputNames: string[] = ["input"], outputNames: string[] = ["output"]): ort.InferenceSession {
    return {
        inputNames,
        outputNames,
        run: jest.fn().mockResolvedValue({output}),
        release: jest.fn().mockResolvedValue(undefined)
    } as unknown as ort.InferenceSession;
}

function mockPdf() {
    const pdfjs = jest.requireMock("pdfjs-dist") as {getDocument: jest.Mock;};

    const page = {
        getViewport: jest.fn(() => ({
            width: 100,
            height: 100
        })),
        render: jest.fn(() => ({promise: Promise.resolve()})),
        cleanup: jest.fn()
    };

    const pdf = {
        numPages: 2,
        getPage: jest.fn(async () => page),
        destroy: jest.fn(async () => undefined)
    };

    pdfjs.getDocument.mockReturnValue({promise: Promise.resolve(pdf)});
    return {pdf, page};
}

function mockSuccessfulVideo(): void {
    const realCreateElement = document.createElement.bind(document);

    jest.spyOn(document, "createElement").mockImplementation((tagName: string) => {
        if (tagName !== "video") {
            return realCreateElement(tagName);
        }

        const listeners: Record<string, EventListener[]> = {};
        let currentTime = 0;

        const video = {
            readyState: 1,
            duration: 10,
            muted: false,
            preload: "",
            src: "",
            load: jest.fn(),
            remove: jest.fn(),
            removeAttribute: jest.fn(),
            addEventListener: jest.fn(
                (
                    event: string,
                    handler: EventListener
                ) => {
                    listeners[event] ??= [];
                    listeners[event].push(handler);
                }
            ),
            removeEventListener: jest.fn(
                (
                    event: string,
                    handler: EventListener
                ) => {
                    listeners[event] = (listeners[event] ?? []).filter(existing => existing !== handler);
                }
            ),

            get currentTime() {return currentTime;},

            set currentTime(value: number) {
                currentTime = value;
                const event = new Event("seeked");
                listeners["seeked"] ?.forEach(handler => handler(event));
            }
        };
        return video as unknown as HTMLVideoElement;
    });
}

describe("ai.ts", () => {
    let getContextSpy: jest.SpyInstance;

    beforeEach(() => {
        jest.clearAllMocks();
        const bitmap = {close: jest.fn()};
        global.createImageBitmap = jest.fn().mockResolvedValue(bitmap);

        getContextSpy =jest.spyOn(HTMLCanvasElement.prototype,"getContext");

        getContextSpy.mockImplementation(() => ({
                drawImage: jest.fn(),
                getImageData: jest.fn(() => ({
                    data: new Uint8ClampedArray([
                        255, 0, 0, 255,
                        0, 255, 0, 255,
                        0, 0, 255, 255,
                        255, 255, 255, 255
                    ])
                }))
            }) as unknown as CanvasRenderingContext2D
        );
        Object.defineProperty(
            URL,
            "createObjectURL",
            {
                configurable: true,
                value: jest.fn(() => "blob:test")
            }
        );
        Object.defineProperty(
            URL,
            "revokeObjectURL",
            {
                configurable: true,
                value: jest.fn()
            }
        );
    });

    afterEach(() => {jest.restoreAllMocks();});

    describe("processImage", () => {
        test("creates an image tensor", async () => {
            const result = await processImage(createImageFile(), baseImageConfig);
            expect(result).toBeInstanceOf(ort.Tensor);
            expect(result.dims).toEqual([1, 3, 2, 2]);
            expect(result.type).toBe("float32");
        });

        test("rejects non-image files", async () => {
            const file =new File(["test"], "test.txt", {type: "text/plain"});
            await expect(processImage(file,baseImageConfig)).rejects.toThrow("File must be an image.");
        });

        test("rejects invalid threshold", async () => {
            await expect(
                processImage(
                    createImageFile(),
                    {
                        ...baseImageConfig,
                        threshold: 2
                    }
                )
            ).rejects.toThrow("Threshold must be between 0 and 1.");
        });

        test("rejects empty class labels", async () => {
            await expect(
                processImage(
                    createImageFile(),
                    {
                        ...baseImageConfig,
                        classLabels: ["", "AI"]
                    }
                )
            ).rejects.toThrow("Class labels cannot be empty.");
        });

        test("rejects identical class labels", async () => {
            await expect(
                processImage(
                    createImageFile(),
                    {
                        ...baseImageConfig,
                        classLabels: ["AI", "AI"]
                    }
                )
            ).rejects.toThrow("Class labels must be different.");
        });

        test("rejects invalid dimensions", async () => {
            await expect(
                processImage(
                    createImageFile(),
                    {
                        ...baseImageConfig,
                        inputWidth: 0
                    }
                )
            ).rejects.toThrow("Input dimensions must be positive integers.");
        });

        test("rejects invalid standard deviation", async () => {
            await expect(
                processImage(
                    createImageFile(),
                    {
                        ...baseImageConfig,
                        std: [1, 0, 1]
                    }
                )
            ).rejects.toThrow(/standard deviation/);
        });

        test("rejects missing canvas context", async () => {
            getContextSpy.mockReturnValueOnce(null);
            await expect(processImage(createImageFile(), baseImageConfig))
            .rejects.toThrow("Could not create canvas context.");
        });
    });

    describe("loadModel", () => {
        test("rejects non-ONNX model", async () => {
            const file = new File(["model"], "model.pt");
            await expect(loadModel(file)).rejects.toThrow("Model file must be an ONNX model.");
        });

        test("loads an ONNX model", async () => {
            const session = createSession(createOutputTensor([0.7]));
            const createSpy =jest.spyOn(ort.InferenceSession,"create").mockResolvedValueOnce(session);
            const file = createModelFile();

            Object.defineProperty(
                file,
                "arrayBuffer",
                {
                    value: jest.fn().mockResolvedValue(new ArrayBuffer(8))
                }
            );

            const result = await loadModel(file);
            expect(result).toBe(session);
            expect(createSpy).toHaveBeenCalled();
            createSpy.mockRestore();
        });
    });

    describe("classification", () => {
        test("classifies a single probability", async () => {
            const session =createSession(createOutputTensor([0.8]));
            const result = await runImageModel(session, createImageFile(), baseImageConfig);
            expect(result.aiProbability).toBeCloseTo(0.8);
            expect(result.classification).toBe("AI");
        });

        test("returns authentic when below threshold", async () => {
            const session = createSession(createOutputTensor([0.2]));
            const result = await runImageModel(
                session,
                createImageFile(),
                baseImageConfig
            );

            expect(result.classification).toBe("AUTHENTIC");
        });

        test("supports AI at class index 0", async () => {
            const session =createSession(createOutputTensor([0.2]));
            const result = await runImageModel(
                session,
                createImageFile(),
                {
                    ...baseImageConfig,
                    classLabels: ["AI", "AUTHENTIC"],
                    aiClassIndex: 0
                }
            );

            expect(result.aiProbability).toBeCloseTo(0.8);
            expect(result.classification).toBe("AI");
        });

        test("applies sigmoid", async () => {
            const session = createSession(createOutputTensor([0]));

            const result = await runImageModel(
                session,
                createImageFile(),
                {
                    ...baseImageConfig,
                    activation: "SIGMOID"
                }
            );

            expect(result.aiProbability).toBeCloseTo(0.5);
        });

        test("applies softmax", async () => {
            const session =createSession(createOutputTensor([1, 3]));
            const result = await runImageModel(
                session,
                createImageFile(),
                {
                    ...baseImageConfig,
                    activation: "SOFTMAX"
                }
            );

            expect(result.aiProbability).toBeGreaterThan(0.8);
            expect(result.classification).toBe("AI");
        });

        test("supports two existing probabilities", async () => {
            const session = createSession(createOutputTensor([0.25, 0.75]));
            const result = await runImageModel(session, createImageFile(), baseImageConfig);
            expect(result.aiProbability).toBeCloseTo(0.75);
        });

        test("rejects softmax with one output", async () => {
            const session =createSession(createOutputTensor([0.5]));
            await expect(
                runImageModel(
                    session,
                    createImageFile(),
                    {
                        ...baseImageConfig,
                        activation: "SOFTMAX"
                    }
                )
            ).rejects.toThrow("SOFTMAX requires a two-class model output.");
        });

        test("rejects sigmoid with two outputs", async () => {
            const session =createSession(createOutputTensor([0.2, 0.8]));
            await expect(
                runImageModel(
                    session,
                    createImageFile(),
                    {
                        ...baseImageConfig,
                        activation: "SIGMOID"
                    }
                )
            ).rejects.toThrow("SIGMOID models must produce a single output value.");
        });

        test("rejects probability outside range", async () => {
            const session = createSession(createOutputTensor([2]));
            await expect(runImageModel(session, createImageFile(), baseImageConfig)).rejects.toThrow(/between 0 and 1/);
        });

        test("rejects unsupported output size", async () => {
            const session =createSession(createOutputTensor([0.1, 0.2, 0.7]));
            await expect(runImageModel(session,createImageFile(),baseImageConfig))
            .rejects.toThrow("Unsupported model output size");
        });

        test("rejects NaN output", async () => {
            const session = createSession( createOutputTensor([NaN]));
            await expect(runImageModel(session, createImageFile(), baseImageConfig)).rejects.toThrow("Model output contains invalid values.");
        });
    });

    describe("model contract", () => {
        test("rejects multiple model inputs", async () => {
            const session = createSession(createOutputTensor([0.8]), ["input1", "input2"]);
            await expect(runImageModel(session, createImageFile(), baseImageConfig)).rejects.toThrow("Model must have exactly one input.");
        });

        test("rejects multiple model outputs", async () => {
            const session =createSession(
                createOutputTensor([0.8]),
                ["input"],
                ["output1", "output2"]
            );

            await expect(runImageModel(session, createImageFile(), baseImageConfig))
            .rejects.toThrow("Model must have exactly one output.");
        });

        test("rejects non-tensor output", async () => {
            const session = {
                inputNames: ["input"],
                outputNames: ["output"],

                run: jest.fn()
                    .mockResolvedValue({output: "invalid"})
            } as unknown as ort.InferenceSession;

            await expect(
                runImageModel(
                    session,
                    createImageFile(),
                    baseImageConfig
                )
            ).rejects.toThrow("Model output is not a tensor.");
        });
    });

    describe("video", () => {

        test("rejects invalid frame count", async () => {
            await expect(
                processVideo(
                    createVideoFile(),
                    {
                        ...baseVideoConfig,
                        frameCount: 0
                    }
                )
            ).rejects.toThrow("Frame count must be a positive integer.");
        });

        test("rejects non-video file", async () => {
            await expect(processVideo(createImageFile(), baseVideoConfig)).rejects.toThrow("File must be a video.");
        });

        test("processes video frames", async () => {
            mockSuccessfulVideo();
            const result = await processVideo(createVideoFile(), baseVideoConfig);
            expect(result).toHaveLength(2);
            expect(global.createImageBitmap).toHaveBeenCalledTimes(2);
            expect(URL.revokeObjectURL).toHaveBeenCalled();
        });

        test("runs video model and averages frame probabilities", async () => {
            mockSuccessfulVideo();
            const session = {
                inputNames: ["input"],
                outputNames: ["output"],

                run: jest.fn()
                    .mockResolvedValueOnce({output: createOutputTensor([0.6])})
                    .mockResolvedValueOnce({output: createOutputTensor([0.8])}),

                release: jest.fn()
            } as unknown as ort.InferenceSession;

            const result = await runVideoModel(session, createVideoFile(), baseVideoConfig);
            expect(result.aiProbability).toBeCloseTo(0.7);
            expect(result.classification).toBe("AI");
        });
    });

    describe("PDF", () => {
        test("rejects invalid page count", async () => {
            await expect(
                processPdf(
                    createPdfFile(),
                    {
                        ...basePdfConfig,
                        pageCount: 0
                    }
                )
            ).rejects.toThrow("Page count must be a positive integer.");
        });

        test("rejects non-PDF files", async () => {
            await expect(processPdf(createImageFile(), basePdfConfig)).rejects.toThrow("File must be a PDF.");
        });

        test("processes PDF pages", async () => {
            const { pdf, page } = mockPdf();
            const result = await processPdf(createPdfFile(), basePdfConfig);
            expect(result).toHaveLength(2);
            expect(pdf.getPage).toHaveBeenCalledTimes(2);
            expect(page.render).toHaveBeenCalledTimes(2);
            expect(pdf.destroy).toHaveBeenCalled();
        });

        test("runs PDF model and averages page results", async () => {
            mockPdf();
            const session = {
                inputNames: ["input"],
                outputNames: ["output"],

                run: jest.fn()
                    .mockResolvedValueOnce({output: createOutputTensor([0.6])})
                    .mockResolvedValueOnce({output: createOutputTensor([0.8])}),
                release: jest.fn()
            } as unknown as ort.InferenceSession;

            const result = await runPdfModel(session, createPdfFile(), basePdfConfig);
            expect(result.aiProbability).toBeCloseTo(0.7);
            expect(result.classification).toBe("AI");
        });
    });

    describe("runModel", () => {
        test("runs image model and releases session", async () => {
            const session = createSession(createOutputTensor([0.8]));
            jest.spyOn(ort.InferenceSession, "create").mockResolvedValueOnce(session);
            const result = await runModel(createModelFile(), createImageFile(), baseImageConfig);
            expect(result.classification).toBe("AI");
            expect(session.release).toHaveBeenCalled();
        });
    });
});