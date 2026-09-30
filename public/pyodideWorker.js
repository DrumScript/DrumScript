// public/pyodideWorker.js
importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js");

async function loadEnvironment() {
  self.pyodide = await loadPyodide();
  
  // Load the micropip installer
  await self.pyodide.loadPackage("micropip");
  const micropip = self.pyodide.pyimport("micropip");
  
  // Install your specific package wheel from the public directory
  await micropip.install("/drumscript-0.1.1-py3-none-any.whl");
  
  // Import the python module
  self.pyodide.runPython(`
    import drumscript
  `);
}

let pyodideReadyPromise = loadEnvironment();

self.onmessage = async (event) => {
  await pyodideReadyPromise;
  const { action, audioData } = event.data;

  try {
    let result;
    // Bind the raw audio bytes from the JS frontend to a Python variable
    self.pyodide.globals.set("audio_bytes", audioData);

    if (action === "DETECT_TEMPO") {
        result = self.pyodide.runPython(`drumscript.get_tempo(audio_bytes)`);
    } else if (action === "SPLIT_STEMS") {
        result = self.pyodide.runPython(`drumscript.split_stems(audio_bytes)`);
    } else if (action === "TRANSCRIBE_PDF") {
        // Calling your newly included notation generator functions
        result = self.pyodide.runPython(`
            from drumscript.notation_generator.pdf_exporter import export_to_pdf
            export_to_pdf(audio_bytes)
        `);
    }

    // Send the result back to the React UI
    self.postMessage({ status: "success", action, result });
  } catch (error) {
    self.postMessage({ status: "error", error: error.message });
  }
};