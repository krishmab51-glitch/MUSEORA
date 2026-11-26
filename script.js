// ============================================
// MUSEORA — AI FUSION STUDIO
// ============================================


// ============================================
// 1. GET HTML ELEMENTS
// ============================================

const fusionInput = document.getElementById("fusionInput");
const fusionUpload = document.getElementById("fusionUpload");
const browseFusion = document.getElementById("browseFusion");

const inspirationGrid = document.getElementById("inspirationGrid");
const imageCounter = document.getElementById("imageCounter");

const visionInput = document.getElementById("visionInput");
const characterCount = document.getElementById("characterCount");
const clearPrompt = document.getElementById("clearPrompt");

const createConcept = document.getElementById("createConcept");

const summaryImageCount = document.getElementById("summaryImageCount");
const selectedElements = document.getElementById("selectedElements");
const summaryBrief = document.getElementById("summaryBrief");

const conceptSection = document.getElementById("conceptSection");
const conceptImageStrip = document.getElementById("conceptImageStrip");
const conceptDescription = document.getElementById("conceptDescription");
const conceptTags = document.getElementById("conceptTags");
const conceptDirection = document.getElementById("conceptDirection");

const editConcept = document.getElementById("editConcept");
const downloadBrief = document.getElementById("downloadBrief");

const elementInputs = document.querySelectorAll(
    'input[name="elements"]'
);

const suggestionButtons = document.querySelectorAll(
    ".suggestion-chip"
);


// ============================================
// 2. APPLICATION STATE
// ============================================

const MAX_IMAGES = 5;
const MAX_FILE_SIZE = 10 * 1024 * 1024;

let inspirationImages = [];
let nextImageId = 0;


// ============================================
// 3. OPEN FILE SELECTOR
// ============================================

browseFusion.addEventListener("click", () => {
    fusionInput.click();
});

fusionUpload.addEventListener("click", (event) => {

    if (event.target.closest("button")) {
        return;
    }

    fusionInput.click();

});


// ============================================
// 4. HANDLE IMAGE SELECTION
// ============================================

fusionInput.addEventListener("change", () => {

    const files = Array.from(fusionInput.files);

    addImages(files);

    // Allows the same file to be selected again later.
    fusionInput.value = "";

});


// ============================================
// 5. ADD AND VALIDATE IMAGES
// ============================================

function addImages(files) {

    let addedCount = 0;

    for (const file of files) {

        if (inspirationImages.length >= MAX_IMAGES) {

            alert(
                "You can add up to five inspiration images."
            );

            break;

        }

        const allowedTypes = [
            "image/jpeg",
            "image/png",
            "image/webp"
        ];

        if (!allowedTypes.includes(file.type)) {

            alert(
                `${file.name} is not a supported image.`
            );

            continue;

        }

        if (file.size > MAX_FILE_SIZE) {

            alert(
                `${file.name} is larger than 10 MB.`
            );

            continue;

        }

        const alreadyAdded = inspirationImages.some(
            item =>
                item.file.name === file.name &&
                item.file.size === file.size &&
                item.file.lastModified === file.lastModified
        );

        if (alreadyAdded) {
            continue;
        }

        const imageObject = {
            id: nextImageId++,
            file: file,
            previewUrl: URL.createObjectURL(file)
        };

        inspirationImages.push(imageObject);

        addedCount++;

    }

    renderInspirationImages();
    updateCreativeSummary();

    if (addedCount > 0) {
        conceptSection.hidden = true;
    }

}


// ============================================
// 6. DISPLAY INSPIRATION IMAGES
// ============================================

function renderInspirationImages() {

    inspirationGrid.innerHTML = "";

    inspirationImages.forEach((item, index) => {

        const card = document.createElement("article");

        card.className = "inspiration-card";

        const image = document.createElement("img");

        image.src = item.previewUrl;
        image.alt = `Inspiration image ${index + 1}`;

        const footer = document.createElement("div");

        footer.className = "inspiration-card-footer";

        const name = document.createElement("span");

        name.textContent = item.file.name;
        name.title = item.file.name;

        const removeButton = document.createElement("button");

        removeButton.type = "button";
        removeButton.className = "remove-inspiration";
        removeButton.textContent = "×";

        removeButton.setAttribute(
            "aria-label",
            `Remove ${item.file.name}`
        );

        removeButton.addEventListener("click", () => {
            removeImage(item.id);
        });

        footer.appendChild(name);
        footer.appendChild(removeButton);

        card.appendChild(image);
        card.appendChild(footer);

        inspirationGrid.appendChild(card);

    });

    imageCounter.textContent =
        `${inspirationImages.length} / ${MAX_IMAGES} images`;

    fusionUpload.style.display =
        inspirationImages.length >= MAX_IMAGES
            ? "none"
            : "flex";

}


// ============================================
// 7. REMOVE AN IMAGE
// ============================================

function removeImage(id) {

    const imageToRemove = inspirationImages.find(
        item => item.id === id
    );

    if (imageToRemove) {

        URL.revokeObjectURL(
            imageToRemove.previewUrl
        );

    }

    inspirationImages = inspirationImages.filter(
        item => item.id !== id
    );

    renderInspirationImages();
    updateCreativeSummary();

    conceptSection.hidden = true;

}


// ============================================
// 8. DRAG AND DROP
// ============================================

fusionUpload.addEventListener("dragover", (event) => {

    event.preventDefault();

    fusionUpload.classList.add("drag-active");

});

fusionUpload.addEventListener("dragleave", () => {

    fusionUpload.classList.remove("drag-active");

});

fusionUpload.addEventListener("drop", (event) => {

    event.preventDefault();

    fusionUpload.classList.remove("drag-active");

    const files = Array.from(
        event.dataTransfer.files
    );

    addImages(files);

});


// ============================================
// 9. UPDATE CHARACTER COUNT
// ============================================

visionInput.addEventListener("input", () => {

    characterCount.textContent =
        `${visionInput.value.length} / 1000`;

    updateCreativeSummary();

    conceptSection.hidden = true;

});


// ============================================
// 10. CLEAR THE PROMPT
// ============================================

clearPrompt.addEventListener("click", () => {

    visionInput.value = "";

    characterCount.textContent = "0 / 1000";

    updateCreativeSummary();

    conceptSection.hidden = true;

});


// ============================================
// 11. PROMPT SUGGESTIONS
// ============================================

suggestionButtons.forEach((button) => {

    button.addEventListener("click", () => {

        visionInput.value = button.dataset.prompt;

        characterCount.textContent =
            `${visionInput.value.length} / 1000`;

        updateCreativeSummary();

        conceptSection.hidden = true;

        visionInput.focus();

    });

});


// ============================================
// 12. SELECT CREATIVE ELEMENTS
// ============================================

elementInputs.forEach((input) => {

    input.addEventListener("change", () => {

        updateCreativeSummary();

        conceptSection.hidden = true;

    });

});


// ============================================
// 13. GET SELECTED ELEMENTS
// ============================================

function getSelectedElements() {

    return Array.from(elementInputs)
        .filter(input => input.checked)
        .map(input => input.value);

}


// ============================================
// 14. UPDATE CREATIVE SUMMARY
// ============================================

function updateCreativeSummary() {

    // Update image count.

    if (inspirationImages.length === 0) {

        summaryImageCount.textContent =
            "No images selected";

    } else {

        summaryImageCount.textContent =
            `${inspirationImages.length} inspiration image` +
            (inspirationImages.length === 1 ? "" : "s");

    }


    // Update selected elements.

    const elements = getSelectedElements();

    selectedElements.innerHTML = "";

    if (elements.length === 0) {

        const emptyTag = document.createElement("span");

        emptyTag.className = "empty-tag";

        emptyTag.textContent = "Nothing selected yet";

        selectedElements.appendChild(emptyTag);

    } else {

        elements.forEach((element) => {

            const tag = document.createElement("span");

            tag.className = "element-tag";

            tag.textContent = element;

            selectedElements.appendChild(tag);

        });

    }


    // Update the creative brief preview.

    const prompt = visionInput.value.trim();

    summaryBrief.textContent = prompt
        ? prompt
        : "Your description will appear here as you develop your idea.";

}


// ============================================
// 15. BUILD THE CREATIVE CONCEPT + IMAGE FUSION
// ============================================

createConcept.addEventListener("click", async () => {

    const prompt = visionInput.value.trim();
    const elements = getSelectedElements();

    if (inspirationImages.length === 0) {
        alert("Add at least one inspiration image to begin.");
        fusionUpload.scrollIntoView({
            behavior: "smooth",
            block: "center"
        });
        return;
    }

    if (!prompt && elements.length === 0) {
        alert("Describe your vision or select at least one creative element.");
        visionInput.focus();
        return;
    }

    // Display selected inspiration images
    conceptImageStrip.innerHTML = "";

    inspirationImages.forEach((item, index) => {
        const image = document.createElement("img");

        image.src = item.previewUrl;
        image.alt = `Inspiration image ${index + 1}`;
        image.title = item.file.name;

        conceptImageStrip.appendChild(image);
    });

    // Display creative description
    conceptDescription.textContent = prompt ||
        "A visual concept inspired by your selected images.";

    // Display selected elements
    conceptTags.innerHTML = "";

    elements.forEach(element => {
        const tag = document.createElement("span");

        tag.className = "concept-tag";
        tag.textContent = element;

        conceptTags.appendChild(tag);
    });

    // Build creative direction
    const directionParts = [];

    directionParts.push(
        `Create a composition using ${inspirationImages.length} uploaded image(s).`
    );

    if (elements.length > 0) {
        directionParts.push(`Focus on ${elements.join(", ")}.`);
    }

    if (prompt) {
        directionParts.push(`Creative vision: ${prompt}`);
    }

    conceptDirection.textContent = directionParts.join(" ");

    // Display concept section
    conceptSection.hidden = false;

    // Show loading status
    createConcept.disabled = true;
    createConcept.textContent = "Creating Fusion...";

    let resultContainer = document.getElementById(
        "fusionResultContainer"
    );

    if (!resultContainer) {
        resultContainer = document.createElement("div");
        resultContainer.id = "fusionResultContainer";

        conceptSection.appendChild(resultContainer);
    }

    resultContainer.innerHTML = `
        <p>Removing backgrounds and combining your images...</p>
    `;

    try {

        // Prepare images for Flask
        const formData = new FormData();

        inspirationImages.forEach(item => {
            formData.append("images", item.file);
        });

        // Send images to Flask backend
        const response = await fetch("/api/fusion", {
            method: "POST",
            body: formData
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(
                result.error || "Image fusion failed."
            );
        }

     // Display interactive composition editor

const editorTitle = document.createElement("h3");
editorTitle.textContent = "Edit Your Composition";
editorTitle.style.textAlign = "center";

resultContainer.innerHTML = "";
resultContainer.appendChild(editorTitle);

// Create editor canvas
const editorStage = document.createElement("div");

editorStage.style.position = "relative";
editorStage.style.width = "100%";
editorStage.style.maxWidth = "800px";
editorStage.style.aspectRatio = "4 / 3";
editorStage.style.margin = "20px auto";
editorStage.style.overflow = "hidden";
editorStage.style.borderRadius = "12px";
editorStage.style.background = "#f5f1e9";
editorStage.style.border = "1px solid #ddd";

resultContainer.appendChild(editorStage);

// Calculate automatic object layout
const canvasWidth = 1200;
const canvasHeight = 900;

const imageCount = result.objects.length;

const columns = Math.ceil(
    Math.sqrt(imageCount * canvasWidth / canvasHeight)
);

const rows = Math.ceil(imageCount / columns);

const cellWidth = canvasWidth / columns;
const cellHeight = canvasHeight / rows;

// Add individual transparent objects
result.objects.forEach((object, index) => {

    const image = document.createElement("img");

    image.src = object.image_url;
    image.alt = "Editable object";

    image.draggable = false;

    image.style.position = "absolute";
    image.style.cursor = "grab";
    image.style.userSelect = "none";
    image.style.touchAction = "none";
    image.style.maxWidth = "none";

    image.style.filter =
        "drop-shadow(5px 8px 8px rgba(0,0,0,0.20))";

    editorStage.appendChild(image);

    image.onload = () => {

        const maxWidth = cellWidth - 80;
        const maxHeight = cellHeight - 80;

        const scale = Math.min(
            maxWidth / image.naturalWidth,
            maxHeight / image.naturalHeight,
            1
        );

        const imageWidth = image.naturalWidth * scale;
        const imageHeight = image.naturalHeight * scale;

        const row = Math.floor(index / columns);
        const column = index % columns;

        const x =
            column * cellWidth +
            (cellWidth - imageWidth) / 2;

        const y =
            row * cellHeight +
            (cellHeight - imageHeight) / 2;

        image.style.width =
            (imageWidth / canvasWidth * 100) + "%";

        image.style.left =
            (x / canvasWidth * 100) + "%";

        image.style.top =
            (y / canvasHeight * 100) + "%";

        image.dataset.x = x;
        image.dataset.y = y;
        image.dataset.width = imageWidth;
        image.dataset.height = imageHeight;
    };

    // Drag individual objects
    let dragging = false;
    let startX = 0;
    let startY = 0;
    let initialX = 0;
    let initialY = 0;

    image.addEventListener("pointerdown", (event) => {

        dragging = true;

        image.style.cursor = "grabbing";

        image.setPointerCapture(event.pointerId);

        const stageRect =
            editorStage.getBoundingClientRect();

        startX = event.clientX;
        startY = event.clientY;

        initialX =
            parseFloat(image.style.left) / 100 *
            stageRect.width;

        initialY =
            parseFloat(image.style.top) / 100 *
            stageRect.height;

    });

    image.addEventListener("pointermove", (event) => {

        if (!dragging) return;

        const stageRect =
            editorStage.getBoundingClientRect();

        const deltaX = event.clientX - startX;
        const deltaY = event.clientY - startY;

        const newX = Math.max(
            0,
            Math.min(
                stageRect.width - image.offsetWidth,
                initialX + deltaX
            )
        );

        const newY = Math.max(
            0,
            Math.min(
                stageRect.height - image.offsetHeight,
                initialY + deltaY
            )
        );

        image.style.left =
            (newX / stageRect.width * 100) + "%";

        image.style.top =
            (newY / stageRect.height * 100) + "%";

    });

    image.addEventListener("pointerup", () => {

        dragging = false;
        image.style.cursor = "grab";

    });

    image.addEventListener("pointercancel", () => {

        dragging = false;
        image.style.cursor = "grab";

    });

});

        // Add download button
        const downloadButton = document.createElement("a");

        downloadButton.href = result.image_url;
        downloadButton.download = "museora-fusion.png";
        downloadButton.textContent = "Download Fusion Image";

        downloadButton.style.display = "inline-block";
        downloadButton.style.margin = "15px";
        downloadButton.style.padding = "12px 20px";
        downloadButton.style.borderRadius = "8px";
        downloadButton.style.background = "#222";
        downloadButton.style.color = "white";
        downloadButton.style.textDecoration = "none";

        resultContainer.appendChild(downloadButton);

        console.log("MUSEORA fusion completed!");

    } catch (error) {

        console.error("Fusion error:", error);

        resultContainer.innerHTML = `
            <p>Unable to create composition: ${error.message}</p>
        `;

    } finally {

        createConcept.disabled = false;
        createConcept.textContent = "Create Concept";

    }

    conceptSection.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

});


// ============================================
// 16. CONTINUE EDITING
// ============================================

editConcept.addEventListener("click", () => {

    document.getElementById("studio").scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

});


// ============================================
// 17. DOWNLOAD CREATIVE BRIEF
// ============================================

downloadBrief.addEventListener("click", () => {

    const prompt = visionInput.value.trim();

    const elements = getSelectedElements();

    const imageNames = inspirationImages.map(
        item => item.file.name
    );

    const content = [
        "MUSEORA — CREATIVE BRIEF",
        "========================",
        "",
        "INSPIRATION IMAGES",
        ...imageNames.map(
            (name, index) => `${index + 1}. ${name}`
        ),
        "",
        "SELECTED CREATIVE ELEMENTS",
        elements.length > 0
            ? elements.join(", ")
            : "No specific elements selected.",
        "",
        "CREATIVE VISION",
        prompt || "No description provided.",
        "",
        "CREATIVE DIRECTION",
        conceptDirection.textContent,
        "",
        "Created with MUSEORA AI Fusion Studio.",
        "",
        "Note: This document describes a creative concept.",
        "It is not an AI-generated image."
    ].join("\n");

    const blob = new Blob(
        [content],
        { type: "text/plain;charset=utf-8" }
    );

    const downloadUrl = URL.createObjectURL(blob);

    const link = document.createElement("a");

    link.href = downloadUrl;

    link.download = "museora-creative-brief.txt";

    document.body.appendChild(link);

    link.click();

    link.remove();

    URL.revokeObjectURL(downloadUrl);

});


// ============================================
// 18. INITIALIZE THE APPLICATION
// ============================================

updateCreativeSummary();

console.log(
    "MUSEORA AI Fusion Studio is ready!"
);