const API = "/api";
const STATIC_DATA_URL = "/data/cards.json";
const INSTALL_TARGETS = [
    {
        target: "codex",
        label: "Codex",
        title: "Bootstrap into Codex",
        description:
            "Creates a .codex/map-cards prompt artifact and adds an AGENTS.md reference for future Codex sessions.",
        command: (name) => `npx map-cards install ${name} --target codex --dir .`,
    },
    {
        target: "claude",
        label: "Claude",
        title: "Install into Claude",
        description:
            "Creates a CLAUDE.md memory entry that Claude Code can load from the workspace.",
        command: (name) => `npx map-cards install ${name} --target claude --dir .`,
    },
    {
        target: "markdown",
        label: "Markdown",
        title: "Portable Markdown",
        description:
            "Downloads a readable prompt-card file for any repo, wiki, or prompt library.",
        command: (name) => `npx map-cards install ${name} --target markdown --dir .`,
    },
    {
        target: "prompt",
        label: "Prompt",
        title: "Raw prompt",
        description: "Copies or downloads only the prompt text with no wrapper metadata.",
        command: () => "",
    },
];

const CATEGORY_DEFS = [
    { id: "", label: "All" },
    { id: "multi-agent", label: "Multi-Agent" },
    { id: "testing", label: "Testing" },
    { id: "code-review", label: "Code Review" },
    { id: "research", label: "Research" },
    { id: "writing", label: "Writing" },
    { id: "data", label: "Data" },
    { id: "devops", label: "DevOps" },
    { id: "security", label: "Security" },
];

const CATEGORY_STYLES = {
    "multi-agent": { topline: "#B79AE2", meta: "#7C3AED" },
    testing: { topline: "#E8A15A", meta: "#9A6B2F" },
    "code-review": { topline: "#B79AE2", meta: "#7C3AED" },
    research: { topline: "#7DBFA3", meta: "#2F7A5B" },
    writing: { topline: "#CFB17A", meta: "#8A6834" },
    data: { topline: "#8FB5FF", meta: "#3965C4" },
    devops: { topline: "#C5A4F0", meta: "#7B4FCE" },
    security: { topline: "#E8A15A", meta: "#B76416" },
    default: { topline: "#D6C8B6", meta: "#7A6C57" },
};

let allCards = [];
let currentCategory = "";
let currentSort = "downloads";
let currentSearch = "";
let currentModalCard = null;
let currentInstallCard = null;
let currentInstallTarget = "codex";
let staticMode = false;

function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
    })[ch]);
}

async function fetchJSON(url) {
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

async function postJSON(url, body = {}) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return res.json();
}

async function loadCards() {
    try {
        const data = await fetchJSON(`${API}/cards?limit=100`);
        if (data.cards?.length) return data.cards;
    } catch (_) {
        staticMode = true;
    }

    const localCards = await fetchJSON(STATIC_DATA_URL);
    staticMode = true;
    return Array.isArray(localCards) ? localCards : [];
}

function showToast(message) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.classList.add("show");
    window.clearTimeout(showToast._timer);
    showToast._timer = window.setTimeout(() => {
        toast.classList.remove("show");
    }, 2400);
}

function getLabelForCategory(categoryId) {
    return CATEGORY_DEFS.find((item) => item.id === categoryId)?.label || categoryId;
}

function cardMatchesCategory(card, categoryId) {
    if (!categoryId) return true;
    if (categoryId === "multi-agent") {
        const tags = (card.tags || []).map((tag) => String(tag).toLowerCase());
        return card.category === "multi-agent" || tags.includes("multi-agent");
    }
    return card.category === categoryId;
}

function getCardsForCategory(categoryId) {
    return allCards.filter((card) => cardMatchesCategory(card, categoryId));
}

function getCategoryCount(categoryId) {
    return getCardsForCategory(categoryId).length;
}

function computeStats(cards) {
    const contributors = new Set(cards.map((card) => card.author));
    const totalDownloads = cards.reduce((sum, card) => sum + (card.download_count || 0), 0);
    const ratedCards = cards.filter((card) => (card.rating_count || 0) > 0);
    const averageRating = ratedCards.length
        ? ratedCards.reduce((sum, card) => sum + (card.avg_rating || 0), 0) / ratedCards.length
        : 0;

    return {
        totalCards: cards.length,
        totalDownloads,
        totalContributors: contributors.size,
        averageRating,
    };
}

function formatNumber(value) {
    return Number(value || 0).toLocaleString();
}

function formatRating(card) {
    return (card.rating_count || 0) > 0
        ? `${(card.avg_rating || 0).toFixed(1)} · ${card.rating_count || 0} ratings`
        : "New";
}

function getFeaturedCard(cards) {
    const preferred = cards.find((card) => card.name === "full-stack-code-review");
    if (preferred) return preferred;
    return sortCards(cards, "trending")[0] || cards[0] || null;
}

function sortCards(cards, sort) {
    const sorted = [...cards];
    sorted.sort((a, b) => {
        if (sort === "rating") {
            const left = (b.avg_rating || 0) - (a.avg_rating || 0);
            if (left !== 0) return left;
        }
        if (sort === "newest") {
            return new Date(b.created_at || 0) - new Date(a.created_at || 0);
        }
        if (sort === "trending") {
            return (b.trending_score || 0) - (a.trending_score || 0);
        }
        return (b.download_count || 0) - (a.download_count || 0);
    });
    return sorted;
}

function getFilteredCards() {
    const normalizedQuery = currentSearch.trim().toLowerCase();
    let filtered = getCardsForCategory(currentCategory);

    if (!normalizedQuery) return filtered;

    return filtered.filter((card) => {
        const haystacks = [
            card.name,
            card.title,
            card.description,
            card.author,
            card.category,
            ...(card.tags || []),
        ].map((value) => String(value || "").toLowerCase());
        return haystacks.some((value) => value.includes(normalizedQuery));
    });
}

function getInstallTargets(card) {
    const apiOptions = card.install_options || [];
    return INSTALL_TARGETS.map((target) => {
        const apiOption = apiOptions.find((option) => option.target === target.target) || {};
        return {
            ...target,
            ...apiOption,
            label: target.label,
            title: target.title,
            command: apiOption.command || target.command(card.name),
            description: apiOption.description || target.description,
        };
    });
}

function getVariableValues() {
    const values = {};
    document.querySelectorAll("[data-variable-name]").forEach((input) => {
        values[input.dataset.variableName] = input.value;
    });
    return values;
}

function applyVariableValues(text, values) {
    let rendered = text || "";
    Object.entries(values).forEach(([name, value]) => {
        const replacement = value || "";
        rendered = rendered
            .replaceAll(`{{${name}}}`, replacement)
            .replaceAll(`{${name}}`, replacement)
            .replaceAll(`$${name}`, replacement);
    });
    return rendered;
}

function renderVariablesMarkdown(variables) {
    if (!variables.length) return "No variables declared.";
    return variables
        .map((variable) => {
            const defaultText = variable.default ? ` Default: \`${variable.default}\`.` : "";
            return `- \`${variable.name}\`: ${variable.description}${defaultText}`;
        })
        .join("\n");
}

function renderMarkdownArtifact(card, codex = false) {
    const prompt = applyVariableValues(card.prompt, getVariableValues()).trim();
    const codexUsage = codex
        ? `\n## Codex Usage\nUse this card as task-specific operating guidance when the user asks for ${card.description.toLowerCase()}\n`
        : "";
    return `${codex ? `# MAPrompt Card: ${card.title}` : `# ${card.title}`}

Name: \`${card.name}\`
Version: \`${card.version || "1.0.0"}\`
Category: \`${card.category}\`
Platforms: ${(card.platforms || []).join(", ")}
License: ${card.license || "MIT"}

## Description
${card.description}
${codexUsage}
## Variables
${renderVariablesMarkdown(card.variables || [])}

## Prompt
${prompt}
`;
}

function cardManifest(card) {
    return {
        name: card.name,
        title: card.title,
        description: card.description,
        author: card.author,
        author_url: card.author_url || "",
        category: card.category,
        tags: card.tags || [],
        platforms: card.platforms || [],
        version: card.version || "1.0.0",
        license: card.license || "MIT",
        variables: card.variables || [],
        prompt: applyVariableValues(card.prompt, getVariableValues()),
    };
}

function buildClientBootstrap(card, target) {
    const prompt = applyVariableValues(card.prompt, getVariableValues());
    if (target === "codex") {
        return {
            filename: `${card.name}.codex.md`,
            contentType: "text/markdown",
            content: renderMarkdownArtifact(card, true),
            nextSteps: [
                "Run the command from the workspace root.",
                "Commit the generated .codex/map-cards artifact if it should travel with the repo.",
                "Start Codex from this workspace so AGENTS.md can reference the card.",
            ],
        };
    }
    if (target === "claude") {
        const claudeMemory = `# MAPrompt Card: ${card.title}

Use this prompt card when the task matches: ${card.description}

${prompt.trim()}
`;
        const manifest = {
            schema_version: "map-cards.claude.v1",
            card: cardManifest(card),
            claude: {
                name: card.name,
                display_name: card.title,
                memory_file: "CLAUDE.md",
                memory_entry: claudeMemory,
                variables: card.variables || [],
            },
        };
        return {
            filename: `${card.name}.claude.json`,
            contentType: "application/json",
            content: JSON.stringify(manifest, null, 2),
            nextSteps: [
                "Run the Claude install command from the workspace root.",
                "The CLI appends a managed MAPrompt Cards section to CLAUDE.md.",
                "Start Claude Code from this workspace so it can load CLAUDE.md.",
            ],
        };
    }
    if (target === "markdown") {
        return {
            filename: `${card.name}.md`,
            contentType: "text/markdown",
            content: renderMarkdownArtifact(card),
            nextSteps: ["Add the Markdown file to your prompt library or project documentation."],
        };
    }
    return {
        filename: `${card.name}.txt`,
        contentType: "text/plain",
        content: prompt,
        nextSteps: ["Paste the prompt into your AI tool."],
    };
}

function getCurrentBootstrap() {
    if (!currentInstallCard) return null;
    return buildClientBootstrap(currentInstallCard, currentInstallTarget);
}

function renderHeroStats() {
    const stats = computeStats(allCards);
    document.getElementById("statCards").textContent = formatNumber(stats.totalCards);
    document.getElementById("statDownloads").textContent = formatNumber(stats.totalDownloads);
    document.getElementById("statContributors").textContent = formatNumber(stats.totalContributors);
    document.getElementById("statRating").textContent = stats.averageRating
        ? stats.averageRating.toFixed(1)
        : "New";

    document.getElementById("marketPulseTitle").textContent = `${stats.totalCards} curated cards`;
    document.getElementById("marketPulseBody").textContent =
        `${formatNumber(stats.totalDownloads)} installs across ${stats.totalContributors} contributors with a ${stats.averageRating ? stats.averageRating.toFixed(1) : "new"} average rating profile.`;
}

function renderCollectionSummary(filteredCards) {
    const categoryLabel = currentCategory ? getLabelForCategory(currentCategory) : "Durable internal tooling";
    const categoryCount = filteredCards.length;
    document.getElementById("collectionTitle").textContent = currentCategory
        ? `${categoryLabel} systems`
        : "Durable internal tooling";
    document.getElementById("collectionBody").textContent = currentCategory
        ? `${categoryCount} card${categoryCount === 1 ? "" : "s"} currently in view for ${categoryLabel.toLowerCase()} work.`
        : "Migration planning, pipeline debugging, and technical writing in one quieter set.";
}

function getSpotlightPoints(card) {
    const primary = getLabelForCategory(card.category);
    const tags = (card.tags || [])
        .slice(0, 2)
        .map((tag) => tag.replace(/(^|-)([a-z])/g, (_, sep, letter) => `${sep}${letter.toUpperCase()}`));
    return [primary, ...tags].slice(0, 3);
}

function renderSpotlight(card) {
    if (!card) return;
    const categoryLabel = getLabelForCategory(card.category);
    document.getElementById("spotlightBadge").textContent = currentCategory
        ? `${categoryLabel} pick`
        : "Editor’s choice";
    document.getElementById("spotlightHeading").textContent = card.title;
    document.getElementById("spotlightDescription").textContent = card.description;
    document.getElementById("spotlightMeta").textContent =
        `${card.author} · ${formatNumber(card.download_count || 0)} installs · ${formatRating(card)}`;
    document.getElementById("spotlightPoints").innerHTML = getSpotlightPoints(card)
        .map((point) => `<li>${escapeHTML(point)}</li>`)
        .join("");

    const openButton = document.getElementById("spotlightOpenButton");
    const installButton = document.getElementById("spotlightInstallButton");
    openButton.onclick = () => openModal(card);
    installButton.onclick = () => openInstallModal(card);
}

function renderCategoryPills() {
    const container = document.getElementById("categoryPills");
    container.innerHTML = CATEGORY_DEFS.map((category) => {
        const count = getCategoryCount(category.id);
        return `
            <button
                type="button"
                class="category-pill${category.id === currentCategory ? " is-active" : ""}"
                data-category="${escapeHTML(category.id)}"
                aria-pressed="${category.id === currentCategory ? "true" : "false"}"
            >
                <span>${escapeHTML(category.label)}</span>
                <span class="category-pill-count">${count}</span>
            </button>
        `;
    }).join("");
}

function renderCard(card) {
    const styles = CATEGORY_STYLES[card.category] || CATEGORY_STYLES.default;
    const tags = (card.tags || [])
        .slice(0, 3)
        .map((tag) => {
            const label = tag.replace(/(^|-)([a-z])/g, (_, sep, letter) => `${sep}${letter.toUpperCase()}`);
            return `<button type="button" class="card-tag" data-tag="${escapeHTML(tag)}">${escapeHTML(label)}</button>`;
        })
        .join("");

    return `
        <article class="card" data-name="${escapeHTML(card.name)}">
            <div class="card-topline" style="--topline-color:${styles.topline}"></div>
            <div class="card-body">
                <div class="card-header">
                    <button type="button" class="card-category" data-category="${escapeHTML(card.category)}">
                        ${escapeHTML(getLabelForCategory(card.category))}
                    </button>
                    <span class="card-rating">${formatRating(card)}</span>
                </div>
                <h3>${escapeHTML(card.title)}</h3>
                <div class="card-description">${escapeHTML(card.description)}</div>
                <div class="card-tags">${tags}</div>
                <div class="card-footer">
                    <div class="card-meta">
                        <div class="card-author">by <a href="${escapeHTML(card.author_url || "#")}" target="_blank" rel="noreferrer">${escapeHTML(card.author)}</a></div>
                        <div class="card-downloads" style="color:${styles.meta}">${formatNumber(card.download_count || 0)} installs</div>
                    </div>
                    <button type="button" class="card-install" data-install="${escapeHTML(card.name)}">Install</button>
                </div>
            </div>
        </article>
    `;
}

function renderGrid(cards) {
    const grid = document.getElementById("resultsGrid");
    grid.innerHTML = cards.map(renderCard).join("");
}

function updateResultsHeader(filteredCards) {
    const categoryLabel = currentCategory ? getLabelForCategory(currentCategory) : "Selected cards";
    document.getElementById("resultsTitle").textContent = currentCategory ? `${categoryLabel} cards` : "Selected cards";

    if (currentSearch && currentCategory) {
        document.getElementById("resultsSubtitle").textContent =
            `Matching ${categoryLabel.toLowerCase()} systems for “${currentSearch}”.`;
    } else if (currentSearch) {
        document.getElementById("resultsSubtitle").textContent =
            `Search results for “${currentSearch}” across the full marketplace.`;
    } else if (currentCategory) {
        document.getElementById("resultsSubtitle").textContent =
            `${categoryLabel} systems presented in the quieter marketplace layout.`;
    } else {
        document.getElementById("resultsSubtitle").textContent =
            "Muted category cues, thin strokes, and enough space for each card to breathe.";
    }

    const filteredDownloads = filteredCards.reduce((sum, card) => sum + (card.download_count || 0), 0);
    document.getElementById("resultsMeta").textContent =
        `${filteredCards.length} card${filteredCards.length === 1 ? "" : "s"} · ${formatNumber(filteredDownloads)} installs in view`;
}

function filterAndDisplay() {
    const filtered = sortCards(getFilteredCards(), currentSort);
    renderCategoryPills();
    renderCollectionSummary(filtered);
    updateResultsHeader(filtered);
    renderSpotlight(getFeaturedCard(filtered.length ? filtered : allCards));
    renderGrid(filtered);
    document.getElementById("emptyState").hidden = filtered.length !== 0;
}

function setCategory(categoryId) {
    currentCategory = categoryId || "";
    filterAndDisplay();
}

function setSearch(query) {
    currentSearch = query || "";
    document.getElementById("searchInput").value = currentSearch;
    filterAndDisplay();
}

function openModal(card) {
    currentModalCard = card;
    document.getElementById("modalTitle").textContent = card.title;
    document.getElementById("modalMeta").innerHTML = [
        `by ${escapeHTML(card.author)}`,
        escapeHTML(getLabelForCategory(card.category)),
        `v${escapeHTML(card.version || "1.0.0")}`,
        `${formatNumber(card.download_count || 0)} installs`,
        escapeHTML((card.platforms || []).join(", ")),
    ].map((part) => `<span>${part}</span>`).join("");
    document.getElementById("modalPrompt").textContent = card.prompt;

    const rating = document.getElementById("modalRating");
    rating.innerHTML = "";
    for (let index = 1; index <= 5; index += 1) {
        const star = document.createElement("span");
        star.className = `star${index <= Math.round(card.avg_rating || 0) ? " filled" : ""}`;
        star.textContent = "★";
        star.onclick = () => rateCard(card.name, index);
        rating.appendChild(star);
    }

    document.getElementById("modalOverlay").classList.add("active");
}

function closeModal() {
    document.getElementById("modalOverlay").classList.remove("active");
    currentModalCard = null;
}

function openInstallModal(card, target = "codex") {
    if (!card) return;
    closeModal();
    currentInstallCard = card;
    currentInstallTarget = target;

    document.getElementById("installTitle").textContent = `Install ${card.title}`;
    document.getElementById("installSummary").textContent =
        `${card.description} Compatible with ${(card.platforms || []).join(", ") || "AI assistants"}.`;

    const targets = getInstallTargets(card);
    document.getElementById("installTargets").innerHTML = targets.map((option) => `
        <button
            type="button"
            class="target-card${option.target === currentInstallTarget ? " active" : ""}"
            data-target="${option.target}"
            onclick="selectInstallTarget('${option.target}')"
        >
            <strong>${escapeHTML(option.label)}</strong>
            <span>${escapeHTML(option.description)}</span>
        </button>
    `).join("");

    const variables = card.variables || [];
    document.getElementById("variableGrid").innerHTML = variables.length
        ? variables.map((variable) => `
            <label>
                ${escapeHTML(variable.name)}
                <input
                    data-variable-name="${escapeHTML(variable.name)}"
                    value="${escapeHTML(variable.default || "")}"
                    placeholder="${escapeHTML(variable.description || "")}"
                    oninput="updateInstallPanel()"
                >
            </label>
        `).join("")
        : "<p>No variables required for this card.</p>";

    updateInstallPanel();
    document.getElementById("installOverlay").classList.add("active");
}

function closeInstallModal() {
    document.getElementById("installOverlay").classList.remove("active");
    currentInstallCard = null;
}

function selectInstallTarget(target) {
    currentInstallTarget = target;
    document.querySelectorAll(".target-card").forEach((element) => {
        element.classList.toggle("active", element.dataset.target === target);
    });
    updateInstallPanel();
}

function updateInstallPanel() {
    if (!currentInstallCard) return;
    const option = getInstallTargets(currentInstallCard).find((item) => item.target === currentInstallTarget);
    const bootstrap = getCurrentBootstrap();
    document.getElementById("installPanelTitle").textContent = option.title;
    document.getElementById("installDescription").textContent = option.description;
    document.getElementById("installCommand").textContent =
        option.command || "No command required. Use copy or download below.";
    document.getElementById("copyCommandBtn").disabled = !option.command;

    const actionLabels = {
        codex: ["Download Codex File", "Copy Codex File", "Copy Raw Prompt"],
        claude: ["Download Claude Manifest", "Copy Claude Manifest", "Copy Raw Prompt"],
        markdown: ["Download Markdown", "Copy Markdown", "Copy Raw Prompt"],
        prompt: ["Download Prompt", "Copy Prompt", "Copy Raw Prompt"],
    };
    const labels = actionLabels[currentInstallTarget] || actionLabels.prompt;
    document.getElementById("downloadActionBtn").textContent = labels[0];
    document.getElementById("copyArtifactBtn").textContent = labels[1];
    document.getElementById("copyRawPromptBtn").textContent = labels[2];
    document.getElementById("copyRawPromptBtn").style.display =
        currentInstallTarget === "prompt" ? "none" : "inline-flex";
    document.getElementById("installNextSteps").innerHTML = bootstrap.nextSteps
        .map((step) => `<li>${escapeHTML(step)}</li>`)
        .join("");
    document.getElementById("installPreview").textContent = bootstrap.content;
}

async function writeClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(text);
        return;
    }
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    textarea.remove();
}

async function recordDownload(target) {
    if (staticMode || !currentInstallCard) return;
    try {
        const data = await postJSON(`${API}/cards/${currentInstallCard.name}/download`, { target });
        const card = allCards.find((item) => item.name === currentInstallCard.name);
        if (card) {
            card.download_count = data.download_count;
        }
        filterAndDisplay();
    } catch (_) {
        // Swallow analytics failures in client mode.
    }
}

async function copyInstallCommand() {
    if (!currentInstallCard) return;
    const option = getInstallTargets(currentInstallCard).find((item) => item.target === currentInstallTarget);
    if (!option.command) {
        showToast("This target does not need a command");
        return;
    }
    await writeClipboard(option.command);
    showToast("Install command copied");
}

async function copyInstallArtifact() {
    const bootstrap = getCurrentBootstrap();
    if (!bootstrap) return;
    await writeClipboard(bootstrap.content);
    showToast("Artifact copied");
}

async function copyRawPrompt() {
    if (!currentInstallCard) return;
    await writeClipboard(applyVariableValues(currentInstallCard.prompt, getVariableValues()));
    showToast("Raw prompt copied");
}

function downloadInstallArtifact() {
    const bootstrap = getCurrentBootstrap();
    if (!bootstrap) return;
    const blob = new Blob([bootstrap.content], { type: bootstrap.contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = bootstrap.filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    recordDownload(currentInstallTarget);
    showToast(`${bootstrap.filename} downloaded`);
}

async function copyModalPrompt() {
    if (!currentModalCard) return;
    await writeClipboard(currentModalCard.prompt);
    showToast("Prompt copied to clipboard");
}

async function rateCard(name, stars) {
    if (staticMode) {
        showToast("Ratings are available on the hosted API version");
        return;
    }
    try {
        const userId = localStorage.getItem("map_user_id") || crypto.randomUUID();
        localStorage.setItem("map_user_id", userId);
        const data = await postJSON(`${API}/cards/${name}/rate`, { user_id: userId, stars });
        const card = allCards.find((item) => item.name === name);
        if (card) {
            card.avg_rating = data.avg_rating;
            card.rating_count = data.rating_count;
            if (currentModalCard && currentModalCard.name === name) {
                currentModalCard = card;
            }
        }
        filterAndDisplay();
        if (currentModalCard && currentModalCard.name === name) {
            openModal(currentModalCard);
        }
        showToast(`Rated ${stars} stars`);
    } catch (_) {
        showToast("Failed to rate card");
    }
}

function bindEvents() {
    document.getElementById("searchInput").addEventListener("input", (event) => {
        setSearch(event.target.value);
    });

    document.getElementById("sortSelect").addEventListener("change", (event) => {
        currentSort = event.target.value;
        filterAndDisplay();
    });

    document.getElementById("categoryPills").addEventListener("click", (event) => {
        const pill = event.target.closest(".category-pill");
        if (!pill) return;
        setCategory(pill.dataset.category || "");
    });

    document.getElementById("collectionAction").addEventListener("click", () => {
        setCategory(currentCategory || "devops");
    });

    document.getElementById("resultsGrid").addEventListener("click", (event) => {
        const installButton = event.target.closest("[data-install]");
        if (installButton) {
            const card = allCards.find((item) => item.name === installButton.dataset.install);
            if (card) openInstallModal(card);
            event.stopPropagation();
            return;
        }

        const tagButton = event.target.closest(".card-tag");
        if (tagButton) {
            setSearch(tagButton.dataset.tag || "");
            event.stopPropagation();
            return;
        }

        const categoryButton = event.target.closest(".card-category");
        if (categoryButton) {
            setCategory(categoryButton.dataset.category || "");
            event.stopPropagation();
            return;
        }

        const cardElement = event.target.closest(".card");
        if (!cardElement) return;
        const card = allCards.find((item) => item.name === cardElement.dataset.name);
        if (card) openModal(card);
    });

    document.getElementById("modalOverlay").addEventListener("click", (event) => {
        if (event.target === event.currentTarget) closeModal();
    });

    document.getElementById("installOverlay").addEventListener("click", (event) => {
        if (event.target === event.currentTarget) closeInstallModal();
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape") {
            closeModal();
            closeInstallModal();
        }
    });
}

async function init() {
    try {
        allCards = await loadCards();
        renderHeroStats();
        bindEvents();
        filterAndDisplay();
    } catch (error) {
        console.error("Failed to load cards", error);
        document.getElementById("emptyState").hidden = false;
        document.getElementById("emptyState").innerHTML = `
            <h3>Failed to load cards</h3>
            <p>Make sure the API server is running or static card data is available.</p>
        `;
    }
}

window.currentModalCard = null;
window.openInstallModal = openInstallModal;
window.closeModal = closeModal;
window.closeInstallModal = closeInstallModal;
window.selectInstallTarget = selectInstallTarget;
window.copyInstallCommand = copyInstallCommand;
window.copyInstallArtifact = copyInstallArtifact;
window.copyRawPrompt = copyRawPrompt;
window.downloadInstallArtifact = downloadInstallArtifact;
window.copyModalPrompt = copyModalPrompt;
window.rateCard = rateCard;
Object.defineProperty(window, "currentModalCard", {
    get() {
        return currentModalCard;
    },
    set(value) {
        currentModalCard = value;
    },
});

init();
