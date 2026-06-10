// Product Label Scanner Logic

document.addEventListener("DOMContentLoaded", () => {
    const uploadZone = document.getElementById("upload-zone");
    const fileInput = document.getElementById("file-input");
    const previewContainer = document.getElementById("preview-container");
    const previewImage = document.getElementById("preview-image");
    const resetBtn = document.getElementById("reset-btn");
    const scanBtn = document.getElementById("scan-btn");
    const scanSpinner = document.getElementById("scan-spinner");
    const scanBtnText = document.getElementById("scan-btn-text");
    const resultCard = document.getElementById("result-card");

    let base64ImageString = "";

    // Drag & Drop event listeners
    ["dragenter", "dragover"].forEach(eventName => {
        uploadZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            uploadZone.classList.add("dragover");
        }, false);
    });

    ["dragleave", "drop"].forEach(eventName => {
        uploadZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            uploadZone.classList.remove("dragover");
        }, false);
    });

    uploadZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });

    uploadZone.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", (e) => {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
        }
    });

    // Reset layout
    resetBtn.addEventListener("click", () => {
        base64ImageString = "";
        previewImage.src = "";
        previewContainer.style.display = "none";
        uploadZone.style.display = "block";
        resultCard.style.display = "none";
        fileInput.value = "";
    });

    // Scan Label Action
    scanBtn.addEventListener("click", async () => {
        if (!base64ImageString) {
            showAlert("Please upload or drag an image first", "danger");
            return;
        }

        // Setup loading state
        scanBtn.disabled = true;
        resetBtn.disabled = true;
        scanSpinner.style.display = "inline-block";
        scanBtnText.textContent = "Scanning with AI...";
        resultCard.style.display = "none";

        try {
            const response = await fetch("/api/scan", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    image: base64ImageString
                })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Failed to process image scan.");
            }

            // Populate Results UI
            document.getElementById("res-product-name").textContent = data.product_name;
            document.getElementById("res-category").textContent = data.category || "Dairy Product";
            
            // Populate nutrition table
            document.getElementById("res-serving").textContent = data.nutrition.serving_size || "N/A";
            document.getElementById("res-calories").textContent = data.nutrition.calories !== null ? `${data.nutrition.calories} kcal` : "N/A";
            document.getElementById("res-protein").textContent = data.nutrition.protein !== null ? `${data.nutrition.protein} g` : "N/A";
            document.getElementById("res-fat").textContent = data.nutrition.fat !== null ? `${data.nutrition.fat} g` : "N/A";
            document.getElementById("res-carbs").textContent = data.nutrition.carbs !== null ? `${data.nutrition.carbs} g` : "N/A";
            document.getElementById("res-sugar").textContent = data.nutrition.sugar !== null ? `${data.nutrition.sugar} g` : "N/A";
            document.getElementById("res-sodium").textContent = data.nutrition.sodium !== null ? `${data.nutrition.sodium} mg` : "N/A";

            // Grade description map
            const gradeDesc = {
                "A": "Excellent nutrition profile (Healthy Choice)",
                "B": "Good nutrition profile (Recommended Choice)",
                "C": "Moderate nutrition profile (Consume in moderation)",
                "D": "Poor nutrition profile (Limit consumption)",
                "E": "Very poor nutrition profile (Avoid or consume rarely)"
            };

            // Grade badge styling
            const gradeBadge = document.getElementById("res-grade-badge");
            const grade = data.nutrition_grade || "C";
            gradeBadge.textContent = grade;
            gradeBadge.setAttribute("data-grade", grade);
            gradeBadge.setAttribute("data-tooltip", `Nutri-Score Grade ${grade} - ${gradeDesc[grade]}`);
            document.getElementById("res-grade-desc").textContent = gradeDesc[grade] || "Calculated Nutri-Score";

            // DB match text
            const matchTextEl = document.getElementById("res-match-text");
            if (data.matched_product) {
                matchTextEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="#28a745" viewBox="0 0 16 16" style="vertical-align: -2px; margin-right: 4px;"><path d="M12.736 3.97a.733.733 0 0 1 1.047 0c.286.289.29.756.01 1.05L7.88 12.01a.733.733 0 0 1-1.065.02L3.217 8.384a.757.757 0 0 1 0-1.06.733.733 0 0 1 1.047 0l3.052 3.093 5.4-6.425z"/></svg> Matched with catalog product: <strong>${data.matched_product.name}</strong>`;
            } else {
                matchTextEl.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="#ffc107" viewBox="0 0 16 16" style="vertical-align: -2px; margin-right: 4px;"><path d="M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.15.15 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.2.2 0 0 1-.054.06.1.1 0 0 1-.066.017H1.146a.1.1 0 0 1-.066-.017.2.2 0 0 1-.054-.06.18.18 0 0 1 .002-.183L7.884 2.073a.15.15 0 0 1 .054-.057m1.044-.45a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767z"/><path d="M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0M7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0z"/></svg> AI recognized this product, but it was not found in our catalog. Added as a custom scanned item.`;
            }

            // Suitability Badge Styling
            const suitBadge = document.getElementById("res-suit-badge");
            const suitability = data.suitability || {}; // verdict: 'recommend' / 'avoid' / 'neutral'
            
            suitBadge.className = `suitability-badge ${suitability.verdict || 'neutral'}`;
            
            if (suitability.verdict === "recommend") {
                suitBadge.textContent = "Recommend";
            } else if (suitability.verdict === "avoid") {
                suitBadge.textContent = "Avoid";
            } else {
                suitBadge.textContent = "Neutral";
            }

            // Diet advice text
            const adviceEl = document.getElementById("res-advice-text");
            if (suitability.reason) {
                adviceEl.textContent = suitability.reason;
                if (suitability.serving_suggestion) {
                    adviceEl.innerHTML += `<br><br><strong>Suggested Serving:</strong> ${suitability.serving_suggestion}`;
                }
            } else {
                adviceEl.innerHTML = `Log in and set up your <a href="/diet" style="color: var(--primary-color); font-weight: 600;">Diet Profile</a> to receive personalized compatibility advice.`;
            }

            // Show results section
            resultCard.style.display = "block";
            resultCard.scrollIntoView({ behavior: "smooth" });

        } catch (err) {
            console.error(err);
            showAlert(err.message || "Error analyzing product image", "danger");
        } finally {
            scanBtn.disabled = false;
            resetBtn.disabled = false;
            scanSpinner.style.display = "none";
            scanBtnText.textContent = "Analyze Product";
        }
    });

    // Helper: read file to base64
    function handleFile(file) {
        if (!file.type.match("image.*")) {
            showAlert("Please select a valid image file (PNG, JPG, JPEG)", "danger");
            return;
        }

        if (file.size > 5 * 1024 * 1024) {
            showAlert("Image size exceeds the 5MB limit", "danger");
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            previewImage.src = e.target.result;
            base64ImageString = e.target.result.split(",")[1];
            
            // Swap display
            uploadZone.style.display = "none";
            previewContainer.style.display = "block";
        };
        reader.readAsDataURL(file);
    }
});
