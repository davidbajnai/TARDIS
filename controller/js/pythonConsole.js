// Console state, independent of the inlet sequence -----------------------------

let pythonStartInProgress = false;
let pythonConsoleTimer = null;
let pythonConsoleGeneration = 0;

// Display output as text, preserving tracebacks and overwriting speed lines -----

function showPythonConsoleState(state) {
    document.getElementById("pythonConsoleStatus").textContent = state.message +
        (state.pid ? " PID: " + state.pid + "." : "");
    if (typeof state.output === "string") {
        const output = document.getElementById("pythonConsoleOutput");
        const atBottom = output.scrollTop + output.clientHeight >= output.scrollHeight - 20;
        output.textContent = state.output;
        if (atBottom) output.scrollTop = output.scrollHeight;
    }
}

async function pythonConsoleRequest(method) {
    const response = await fetch("controller/php/pythonConsole.php", {
        method: method,
        headers: { "X-TARDIS-Python": "1" },
        cache: "no-store",
    });
    const state = await response.json();
    if (!response.ok || state.ok !== true) {
        throw new Error(state.message || "Python console request failed.");
    }
    return state;
}

// Poll only while visible; closing the popup never signals the Python process ---

function closePythonConsole() {
    clearTimeout(pythonConsoleTimer);
    pythonConsoleTimer = null;
    pythonConsoleGeneration++;
}

async function pollPythonConsole(generation) {
    const dialog = document.getElementById("pythonConsole");
    if (!dialog.open || generation !== pythonConsoleGeneration) return;
    let keepWatching = true;
    try {
        const state = await pythonConsoleRequest("GET");
        if (generation !== pythonConsoleGeneration) return;
        showPythonConsoleState(state);
        keepWatching = state.running === true;
    } catch (error) {
        if (generation !== pythonConsoleGeneration) return;
        showPythonConsoleState({ message: error.message + " Retrying live output..." });
    }
    if (keepWatching && dialog.open && generation === pythonConsoleGeneration) {
        pythonConsoleTimer = setTimeout(() => pollPythonConsole(generation), 1000);
    }
}

// Start once, or reopen the existing GUI session -------------------------------

async function startPythonButton() {
    const dialog = document.getElementById("pythonConsole");
    // Non-modal: STOP and the existing GUI controls remain accessible.
    if (!dialog.open) dialog.show();
    if (pythonStartInProgress) return;
    closePythonConsole();
    pythonStartInProgress = true;
    showPythonConsoleState({ message: "Starting or checking Python...", output: "" });
    let watch = false;
    try {
        const state = await pythonConsoleRequest("POST");
        showPythonConsoleState(state);
        watch = state.watch === true;
    } catch (error) {
        showPythonConsoleState({ message: error.message +
            " Startup is not confirmed. Check the Linux terminal before retrying." });
    } finally {
        pythonStartInProgress = false;
    }
    if (watch && dialog.open) pollPythonConsole(pythonConsoleGeneration);
}
