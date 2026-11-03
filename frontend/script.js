
const API_URL = window.location.origin;

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => document.querySelectorAll(selector);

const pdfInput = $("#pdfInput");
const paperList = $("#paperList");
const workspacePanel = $("#workspacePanel");
const panelTitle = $("#panelTitle");
const panelSubtitle = $("#panelSubtitle");
const panelBody = $("#panelBody");
const toast = $("#toast");

let papers = [];
let questionCount = 0;
let summaryCount = 0;
let currentView = "home";
let toastTimer;

function showToast(message) {
    toast.textContent = message;
    toast.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove("show"), 3500);
}

// Theme: dark is the default, and the user can switch to light.
function applyTheme(theme) {
    document.body.classList.toggle("dark", theme === "dark");

    const button = $("#themeToggle");
    if (button) {
        button.innerHTML = theme === "dark"
            ? "☀ <span>Switch to light mode</span>"
            : "☾ <span>Switch to dark mode</span>";
    }

    try {
        localStorage.setItem("knolex-theme", theme);
    } catch (error) {
        // Continue even if browser storage is unavailable.
    }
}

$("#themeToggle").addEventListener("click", () => {
    applyTheme(document.body.classList.contains("dark") ? "light" : "dark");
});

try {
    applyTheme(localStorage.getItem("knolex-theme") || "dark");
} catch (error) {
    applyTheme("dark");
}

const viewDetails = {
    home: {
        title: "Research, reimagined.",
        subtitle: "A calmer space to explore papers, connect ideas, and write with confidence."
    },
    library: {
        title: "My research library",
        subtitle: "Manage the papers you have uploaded."
    },
    ask: {
        title: "Ask your papers",
        subtitle: "Ask questions about your uploaded research."
    },
    summarize: {
        title: "Smart summaries",
        subtitle: "Discover the key ideas in a research paper."
    },
    compare: {
        title: "Compare papers",
        subtitle: "Explore similarities and differences across studies."
    },
    writing: {
        title: "Writing studio",
        subtitle: "Improve the clarity of your academic writing."
    },
    citations: {
        title: "Citation finder",
        subtitle: "Explore references and citation information."
    }
};

function openView(view) {
    currentView = view;

    $$(".nav-item").forEach((button) => {
        button.classList.toggle("active", button.dataset.view === view);
    });

    const details = viewDetails[view] || viewDetails.home;
    $("#pageTitle").textContent = details.title;
    $("#pageSubtitle").textContent = details.subtitle;
    $("#breadcrumbPage").textContent = details.title;

    const overviewSections = [
        $(".welcome-row"),
        $(".hero"),
        $(".stats-grid"),
        $(".page-content > .section-heading"),
        $(".tools-grid"),
        $(".library-section")
    ];

    overviewSections.forEach((element) => {
        if (element) element.classList.toggle("hidden", view !== "home");
    });

    workspacePanel.classList.toggle("hidden", view === "home");

    if (view === "home") return;

    panelTitle.textContent = details.title;
    panelSubtitle.textContent = details.subtitle;

    const renderers = {
        library: renderLibraryPanel,
        ask: renderAskPanel,
        summarize: renderSummarizePanel,
        compare: renderComparePanel,
        writing: renderWritingPanel,
        citations: renderCitationPanel
    };

    (renderers[view] || renderLibraryPanel)();

    workspacePanel.scrollIntoView({ behavior: "smooth", block: "start" });
}

$$("[data-view]").forEach((button) => {
    button.addEventListener("click", () => openView(button.dataset.view));
});

$$("[data-action='upload']").forEach((button) => {
    button.addEventListener("click", () => pdfInput.click());
});

pdfInput.addEventListener("change", async () => {
    const file = pdfInput.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
        showToast("Please choose a PDF file.");
        pdfInput.value = "";
        return;
    }

    if (file.size > 25 * 1024 * 1024) {
        showToast("Please choose a PDF smaller than 25 MB.");
        pdfInput.value = "";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);
    showToast("Uploading your paper...");

    try {
        const response = await fetch(`${API_URL}/api/upload`, {
            method: "POST",
            body: formData
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.detail || "The backend could not upload this paper.");
        }

        papers.push({
            id: data.id || `${Date.now()}-${file.name}`,
            name: data.filename || file.name,
            pages: data.pages ?? null,
            characters: data.characters ?? null,
            chunks: data.total_chunks ?? null,
            status: "Uploaded"
        });

        updateStats();
        renderPaperList();
        showToast("Paper uploaded successfully!");

        if (currentView === "library") renderLibraryPanel();
    } catch (error) {
        console.error("Upload error:", error);
        showToast(error.message.includes("Failed to fetch")
            ? "Cannot reach the backend. Check that the server is running."
            : error.message);
    } finally {
        pdfInput.value = "";
    }
});

function updateStats() {
    $("#paperCount").textContent = papers.length;
    $("#questionCount").textContent = questionCount;
    $("#summaryCount").textContent = summaryCount;
}

function renderPaperList() {
    if (!papers.length) {
        paperList.className = "empty-library";
        paperList.innerHTML = `
            <div class="empty-icon">▤</div>
            <h3>Your library starts here</h3>
            <p>Upload your first PDF to build your research collection.</p>
            <button class="secondary-button" data-action="upload">Choose a PDF</button>
        `;

        paperList.querySelector("[data-action='upload']")
            .addEventListener("click", () => pdfInput.click());
        return;
    }

    paperList.className = "";
    paperList.innerHTML = papers.map((paper) => `
        <div class="paper-row">
            <div class="paper-row-icon">PDF</div>
            <div class="paper-row-info">
                <strong>${escapeHTML(paper.name)}</strong>
                <small>${paper.pages == null ? "Page count unavailable" : `${paper.pages} pages`} · ${escapeHTML(paper.status)}</small>
            </div>
        </div>
    `).join("");
}

function renderLibraryPanel() {
    panelBody.innerHTML = `
        <button class="primary-button" id="libraryUpload">+ Upload a research paper</button>
        <div id="libraryItems" class="result-box"></div>
    `;

    $("#libraryUpload").addEventListener("click", () => pdfInput.click());
    const container = $("#libraryItems");

    if (!papers.length) {
        container.textContent = "Your library is empty. Upload a PDF to get started.";
        return;
    }

    container.innerHTML = papers.map((paper) => `
        <div class="paper-row">
            <div class="paper-row-icon">PDF</div>
            <div class="paper-row-info">
                <strong>${escapeHTML(paper.name)}</strong>
                <small>${paper.pages == null ? "Page count unavailable" : `${paper.pages} pages`}</small>
            </div>
        </div>
    `).join("");
}

function paperOptions() {
    if (!papers.length) return `<option value="">No papers uploaded yet</option>`;

    return papers.map((paper) => `
        <option value="${escapeHTML(String(paper.id))}">${escapeHTML(paper.name)}</option>
    `).join("");
}

function renderAskPanel() {
    panelBody.innerHTML = `
        <div class="field-group">
            <label for="askPaper">Choose a paper</label>
            <select id="askPaper">${paperOptions()}</select>
        </div>
        <div class="field-group">
            <label for="questionInput">Your question</label>
            <textarea id="questionInput" placeholder="What is the main research question of this paper?"></textarea>
        </div>
        <button class="primary-button" id="askButton">Ask KNOLEX →</button>
        <div id="askResult" class="result-box hidden"></div>
    `;

    $("#askButton").addEventListener("click", async () => {
        const question = $("#questionInput").value.trim();

        if (!papers.length) return showToast("Upload a paper before asking questions.");
        if (!question) return showToast("Please enter a question.");

        await runResearchAction("/api/ask",
            { question, paper_id: $("#askPaper").value },
            $("#askButton"), $("#askResult"), "question");
    });
}

function renderSummarizePanel() {
    panelBody.innerHTML = `
        <div class="field-group">
            <label for="summaryPaper">Choose a paper</label>
            <select id="summaryPaper">${paperOptions()}</select>
        </div>
        <button class="primary-button" id="summaryButton">Generate summary →</button>
        <div id="summaryResult" class="result-box hidden"></div>
    `;

    $("#summaryButton").addEventListener("click", async () => {
        if (!papers.length) return showToast("Upload a paper before generating a summary.");

        await runResearchAction("/api/summarize",
            { paper_id: $("#summaryPaper").value },
            $("#summaryButton"), $("#summaryResult"), "summary");
    });
}

function renderComparePanel() {
    panelBody.innerHTML = `
        <p>Select two uploaded papers to compare their findings.</p>
        <div class="field-group">
            <label for="comparePaper1">First paper</label>
            <select id="comparePaper1">${paperOptions()}</select>
        </div>
        <div class="field-group">
            <label for="comparePaper2">Second paper</label>
            <select id="comparePaper2">${paperOptions()}</select>
        </div>
        <button class="primary-button" id="compareButton">Compare research →</button>
        <div id="compareResult" class="result-box hidden"></div>
    `;

    $("#compareButton").addEventListener("click", async () => {
        if (papers.length < 2) return showToast("Upload at least two papers to compare them.");

        const first = $("#comparePaper1").value;
        const second = $("#comparePaper2").value;

        if (first === second) return showToast("Choose two different papers.");

        await runResearchAction("/api/compare",
            { paper_id_1: first, paper_id_2: second },
            $("#compareButton"), $("#compareResult"), "comparison");
    });
}

function renderWritingPanel() {
    panelBody.innerHTML = `
        <div class="field-group">
            <label for="writingMode">Writing task</label>
            <select id="writingMode">
                <option value="improve">Improve clarity and grammar</option>
                <option value="academic">Make the tone more academic</option>
                <option value="paraphrase">Paraphrase while preserving meaning</option>
            </select>
        </div>
        <div class="field-group">
            <label for="writingInput">Your text</label>
            <textarea id="writingInput" placeholder="Paste your paragraph here..."></textarea>
        </div>
        <button class="primary-button" id="writingButton">Improve my writing →</button>
        <div id="writingResult" class="result-box hidden"></div>
    `;

    $("#writingButton").addEventListener("click", async () => {
        const content = $("#writingInput").value.trim();
        if (!content) return showToast("Paste some text first.");

        await runResearchAction("/api/writing",
            { text: content, mode: $("#writingMode").value },
            $("#writingButton"), $("#writingResult"), "writing");
    });
}

function renderCitationPanel() {
    panelBody.innerHTML = `
        <p>Explore references extracted from your research paper.</p>
        <div class="field-group">
            <label for="citationPaper">Choose a paper</label>
            <select id="citationPaper">${paperOptions()}</select>
        </div>
        <button class="primary-button" id="citationButton">Find citations →</button>
        <div id="citationResult" class="result-box hidden"></div>
    `;

    $("#citationButton").addEventListener("click", async () => {
        if (!papers.length) return showToast("Upload a paper first.");

        await runResearchAction("/api/citations",
            { paper_id: $("#citationPaper").value },
            $("#citationButton"), $("#citationResult"), "citations");
    });
}

async function runResearchAction(endpoint, payload, button, resultBox, type) {
    const originalText = button.textContent;
    button.disabled = true;
    button.textContent = "Working...";
    resultBox.classList.remove("hidden");
    resultBox.textContent = "KNOLEX is processing your request...";

    try {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json().catch(() => ({}));
        if (!response.ok) throw new Error(data.detail || `Request failed (${response.status}).`);

        const output = data.answer ?? data.summary ?? data.comparison
            ?? data.result ?? data.text ?? data.citations;

        if (output == null) throw new Error("The server returned no result.");

        resultBox.textContent = typeof output === "string"
            ? output : JSON.stringify(output, null, 2);

        if (type === "question") questionCount++;
        if (type === "summary") summaryCount++;
        updateStats();
    } catch (error) {
        console.error(`${type} error:`, error);
        resultBox.textContent = error.message.includes("Failed to fetch")
            ? "Cannot reach the backend. Check that KNOLEX is running."
            : error.message;
        showToast("This feature needs its backend endpoint implemented.");
    } finally {
        button.disabled = false;
        button.textContent = originalText;
    }
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, (character) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[character]);
}

renderPaperList();
updateStats();
