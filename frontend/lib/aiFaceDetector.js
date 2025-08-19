'use client'

// Lightweight wrapper around TensorFlow.js BlazeFace detector.
// Lazy-loads the model and WebGL backend on first use.

let modelPromise = null

async function loadModel() {
  if (modelPromise) return modelPromise
  modelPromise = (async () => {
    const tf = await import('@tensorflow/tfjs-core')
    await import('@tensorflow/tfjs-backend-webgl')
    await tf.ready()
    await tf.setBackend('webgl')
    const blazeface = await import('@tensorflow-models/blazeface')
    const model = await blazeface.load()
    return { tf, model }
  })()
  return modelPromise
}

export async function detectLargestFaceOnCanvas(canvas, minScore = 0.9) {
  const { tf, model } = await loadModel()
  // The model accepts image/video/canvas; pass canvas directly
  const predictions = await model.estimateFaces(canvas, false)
  if (!predictions || predictions.length === 0) return null
  // Filter by probability if present
  const filtered = predictions
    .filter(p => (typeof p.probability?.[0] === 'number' ? p.probability[0] >= minScore : true))
    .map(p => ({
      x: p.topLeft[0],
      y: p.topLeft[1],
      w: p.bottomRight[0] - p.topLeft[0],
      h: p.bottomRight[1] - p.topLeft[1],
      score: typeof p.probability?.[0] === 'number' ? p.probability[0] : 1.0,
    }))
  const faces = (filtered.length ? filtered : predictions.map(p => ({
    x: p.topLeft[0],
    y: p.topLeft[1],
    w: p.bottomRight[0] - p.topLeft[0],
    h: p.bottomRight[1] - p.topLeft[1],
    score: 1.0,
  })))
  faces.sort((a, b) => (b.w * b.h) - (a.w * a.h))
  return faces[0]
}

// Preload the TF.js backend and BlazeFace model to avoid first-use latency
export async function warmupFaceDetector() {
  try {
    await loadModel()
  } catch (e) {
    // swallow; UI should remain responsive even if warmup fails
  }
}
