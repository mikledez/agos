const MAX_UPLOAD_EDGE = 2000;
const JPEG_QUALITY = 0.85;

function loadImageElement(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(
        new Error(
          "Could not read this image. Please use a JPEG, PNG, WebP, or HEIC photo.",
        ),
      );
    };
    image.src = url;
  });
}

async function decodeImage(
  file: File,
): Promise<ImageBitmap | HTMLImageElement> {
  if (typeof createImageBitmap === "function") {
    const bitmap = await createImageBitmap(file, {
      imageOrientation: "from-image",
    }).catch(() => null);
    if (bitmap) return bitmap;
  }
  return loadImageElement(file);
}

export async function prepareImage(file: File): Promise<File> {
  const source = await decodeImage(file);
  const sourceWidth =
    source instanceof HTMLImageElement ? source.naturalWidth : source.width;
  const sourceHeight =
    source instanceof HTMLImageElement ? source.naturalHeight : source.height;

  if (!sourceWidth || !sourceHeight) {
    throw new Error("Could not read this image.");
  }

  const scale = Math.min(
    1,
    MAX_UPLOAD_EDGE / Math.max(sourceWidth, sourceHeight),
  );
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(sourceWidth * scale));
  canvas.height = Math.max(1, Math.round(sourceHeight * scale));

  const context = canvas.getContext("2d");
  if (!context) throw new Error("Could not process this image.");

  context.drawImage(source, 0, 0, canvas.width, canvas.height);
  if (!(source instanceof HTMLImageElement)) source.close();

  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(
      (value) =>
        value ? resolve(value) : reject(new Error("Could not process image.")),
      "image/jpeg",
      JPEG_QUALITY,
    );
  });

  const baseName = file.name.replace(/\.[^.]+$/, "") || "upload";
  return new File([blob], `${baseName}.jpg`, { type: "image/jpeg" });
}
